"""
Evaluation Pipeline for Recommendation Quality

Metrics:
- Recall@K: Proportion of relevant items retrieved in top K
- Precision@K: Proportion of retrieved items that are relevant
- Hit Rate@K: Proportion of users with at least one relevant item in top K
- NDCG@K: Normalized Discounted Cumulative Gain
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from typing import Dict, List, Tuple, Set
import os


class EvaluationPipeline:
    """Pipeline to evaluate recommendation quality."""

    def __init__(self, db_url: str):
        self.engine = create_engine(db_url)

    def evaluate_recommendations(
        self,
        test_start_date: datetime = None,
        test_end_date: datetime = None,
        k_values: List[int] = None,
    ) -> Dict[str, Dict[int, float]]:
        """
        Evaluate recommendation quality using temporal split.

        Train: Events before test_start_date
        Test: Events between test_start_date and test_end_date

        For each user in test set:
        1. Get recommendations using only train data (from precomputed similarities)
        2. Compare against actual interactions in test period
        """
        if k_values is None:
            k_values = [5, 10, 20]

        if test_end_date is None:
            test_end_date = datetime.utcnow()

        if test_start_date is None:
            test_start_date = test_end_date - timedelta(days=7)

        print(f"Evaluation period: {test_start_date.date()} to {test_end_date.date()}")

        print("Loading train/test split...")
        train_events, test_events = self._load_temporal_split(test_start_date, test_end_date)

        print(f"  Train events: {len(train_events)}")
        print(f"  Test events: {len(test_events)}")

        if test_events.empty:
            print("No test events found. Cannot evaluate.")
            return {}

        print(f"  Test users: {test_events['user_id'].nunique()}")

        # Get ground truth for each user
        ground_truth = self._get_ground_truth(test_events)
        print(f"  Users with relevant items: {len(ground_truth)}")

        if not ground_truth:
            print("No users with relevant items in test period.")
            return {}

        # Get recommendations for each user
        print("Getting recommendations for test users...")
        recommendations = self._get_recommendations_for_users(
            list(ground_truth.keys()),
            max(k_values),
            train_events
        )

        # Compute metrics
        metrics = self._compute_metrics(ground_truth, recommendations, k_values)

        return metrics

    def _load_temporal_split(
        self,
        test_start: datetime,
        test_end: datetime
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Load events split by time."""
        with self.engine.connect() as conn:
            train_query = text("""
                SELECT user_id, product_id, event_type, timestamp
                FROM events WHERE timestamp < :test_start
            """)
            train_df = pd.read_sql(train_query, conn, params={'test_start': test_start})

            test_query = text("""
                SELECT user_id, product_id, event_type, timestamp
                FROM events WHERE timestamp >= :test_start AND timestamp <= :test_end
            """)
            test_df = pd.read_sql(test_query, conn, params={
                'test_start': test_start,
                'test_end': test_end
            })

        return train_df, test_df

    def _get_ground_truth(self, test_events: pd.DataFrame) -> Dict[int, Set[int]]:
        """Get actual items each user interacted with in test period."""
        # Consider items with add_to_cart or purchase as "relevant"
        relevant_events = test_events[
            test_events['event_type'].isin(['add_to_cart', 'purchase'])
        ]

        ground_truth = {}
        for user_id in relevant_events['user_id'].unique():
            user_items = set(
                relevant_events[relevant_events['user_id'] == user_id]['product_id'].unique()
            )
            if user_items:
                ground_truth[user_id] = user_items

        return ground_truth

    def _get_recommendations_for_users(
        self,
        user_ids: List[int],
        k: int,
        train_events: pd.DataFrame
    ) -> Dict[int, List[int]]:
        """Get recommendations for each user from precomputed similarities."""
        recommendations = {}

        with self.engine.connect() as conn:
            for user_id in user_ids:
                # Get user's recent interactions from train data
                user_events = train_events[train_events['user_id'] == user_id]

                if user_events.empty:
                    continue

                # Convert numpy.int64 to Python int to avoid psycopg2 adapter error
                interacted_ids = set(int(x) for x in user_events['product_id'].unique())

                # Get similar products from precomputed table
                if not interacted_ids:
                    continue

                # Build query for similar products
                placeholders = ','.join([f':p{i}' for i in range(len(interacted_ids))])
                sim_query = text(f"""
                    SELECT similar_product_id as product_id,
                           SUM(similarity_score) as score
                    FROM item_similarity
                    WHERE product_id IN ({placeholders})
                    GROUP BY similar_product_id
                    ORDER BY score DESC
                    LIMIT :limit
                """)

                params = {f'p{i}': int(pid) for i, pid in enumerate(interacted_ids)}
                params['limit'] = k + len(interacted_ids)  # Get extra to filter

                try:
                    recs_df = pd.read_sql(sim_query, conn, params=params)

                    # Filter out already interacted items
                    recs_df = recs_df[~recs_df['product_id'].isin(interacted_ids)]
                    recommendations[user_id] = recs_df['product_id'].head(k).tolist()
                except Exception as e:
                    print(f"  Warning: Could not get recs for user {user_id}: {e}")
                    continue

        return recommendations

    def _compute_metrics(
        self,
        ground_truth: Dict[int, Set[int]],
        recommendations: Dict[int, List[int]],
        k_values: List[int]
    ) -> Dict[str, Dict[int, float]]:
        """Compute evaluation metrics."""
        metrics = {
            'recall': {},
            'precision': {},
            'hit_rate': {},
            'ndcg': {}
        }

        for k in k_values:
            recall_scores = []
            precision_scores = []
            hits = 0
            ndcg_scores = []

            for user_id, actual_items in ground_truth.items():
                if user_id not in recommendations:
                    continue

                predicted_items = recommendations[user_id][:k]

                # Recall@K
                relevant_retrieved = len(set(predicted_items) & actual_items)
                recall = relevant_retrieved / len(actual_items) if actual_items else 0
                recall_scores.append(recall)

                # Precision@K
                precision = relevant_retrieved / k if k > 0 else 0
                precision_scores.append(precision)

                # Hit Rate@K
                if relevant_retrieved > 0:
                    hits += 1

                # NDCG@K
                ndcg = self._compute_ndcg(predicted_items, actual_items, k)
                ndcg_scores.append(ndcg)

            n_users = len([u for u in ground_truth if u in recommendations])
            if n_users > 0:
                metrics['recall'][k] = np.mean(recall_scores) if recall_scores else 0
                metrics['precision'][k] = np.mean(precision_scores) if precision_scores else 0
                metrics['hit_rate'][k] = hits / n_users
                metrics['ndcg'][k] = np.mean(ndcg_scores) if ndcg_scores else 0
            else:
                metrics['recall'][k] = 0
                metrics['precision'][k] = 0
                metrics['hit_rate'][k] = 0
                metrics['ndcg'][k] = 0

        return metrics

    def _compute_ndcg(
        self,
        predicted: List[int],
        actual: Set[int],
        k: int
    ) -> float:
        """Compute Normalized Discounted Cumulative Gain."""
        dcg = 0.0
        for i, item in enumerate(predicted[:k]):
            if item in actual:
                dcg += 1.0 / np.log2(i + 2)  # i+2 because log2(1) = 0

        # Ideal DCG
        ideal_dcg = sum(1.0 / np.log2(i + 2) for i in range(min(len(actual), k)))

        return dcg / ideal_dcg if ideal_dcg > 0 else 0.0

    def print_metrics(self, metrics: Dict[str, Dict[int, float]]):
        """Pretty print evaluation metrics."""
        print("\n" + "=" * 60)
        print("RECOMMENDATION EVALUATION RESULTS")
        print("=" * 60)

        if not metrics:
            print("No metrics to display.")
            return

        for metric_name, k_values in metrics.items():
            print(f"\n{metric_name.upper()}:")
            for k, value in sorted(k_values.items()):
                print(f"  @{k}: {value:.4f}")

        print("\n" + "=" * 60)


if __name__ == "__main__":
    db_url = os.getenv("DATABASE_URL", "postgresql://shopsmart:shopsmart_secret@localhost:5432/shopsmart")

    evaluator = EvaluationPipeline(db_url)

    # Use last 7 days as test, everything before as train
    test_end = datetime.utcnow()
    test_start = test_end - timedelta(days=7)

    metrics = evaluator.evaluate_recommendations(
        test_start_date=test_start,
        test_end_date=test_end,
        k_values=[5, 10, 20]
    )

    evaluator.print_metrics(metrics)

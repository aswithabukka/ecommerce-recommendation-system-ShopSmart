"""
Item-to-Item Similarity Pipeline

Computes co-occurrence based similarity between products.
Users who viewed/purchased X also viewed/purchased Y.

Similarity formula: Weighted cosine similarity on user-item interaction matrix
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from scipy import sparse
from sklearn.metrics.pairwise import cosine_similarity
from typing import Dict, List, Tuple
import os
import redis


class SimilarityPipeline:
    """Pipeline to compute item-to-item similarity."""

    def __init__(self, db_url: str, redis_url: str = None):
        self.engine = create_engine(db_url)
        self.redis_client = redis.from_url(redis_url) if redis_url else None
        self.event_weights = {
            'view': 1.0,
            'add_to_cart': 3.0,
            'purchase': 5.0
        }
        self.min_co_occurrence = 2   # Minimum co-occurrence count to consider
        self.top_k_similar = 50      # Store top K similar products per item
        self.lookback_days = 90      # Consider events from last N days

    def run(self):
        """Execute the similarity pipeline."""
        print("Loading user-item interactions...")
        interactions = self._load_interactions()

        if interactions.empty:
            print("No interactions found. Skipping similarity computation.")
            return

        n_products = interactions['product_id'].nunique()
        n_users = interactions['user_id'].nunique()
        print(f"  Found {len(interactions)} interactions")
        print(f"  {n_users} users, {n_products} products")

        print("Computing item-item similarity...")
        similarity_pairs = self._compute_similarity(interactions)

        print(f"Saving {len(similarity_pairs)} similarity pairs...")
        self._save_similarities(similarity_pairs)

        # Invalidate cache
        if self.redis_client:
            print("Invalidating similarity cache...")
            keys = self.redis_client.keys("sim:*")
            if keys:
                self.redis_client.delete(*keys)
            # Also invalidate recommendation cache
            rec_keys = self.redis_client.keys("rec:*")
            if rec_keys:
                self.redis_client.delete(*rec_keys)
            print("  Cache invalidated")

        print("Similarity pipeline complete!")

    def _load_interactions(self) -> pd.DataFrame:
        """Load user-item interactions within the lookback window."""
        cutoff_date = datetime.utcnow() - timedelta(days=self.lookback_days)

        query = text("""
            SELECT
                e.user_id,
                e.product_id,
                e.event_type
            FROM events e
            JOIN products p ON e.product_id = p.id
            WHERE e.timestamp >= :cutoff
            AND p.is_active = true
        """)

        with self.engine.connect() as conn:
            df = pd.read_sql(query, conn, params={'cutoff': cutoff_date})

        if df.empty:
            return df

        # Apply event weights
        df['weight'] = df['event_type'].map(self.event_weights)

        # Aggregate weights per user-item pair
        interactions = df.groupby(['user_id', 'product_id'])['weight'].sum().reset_index()

        return interactions

    def _compute_similarity(self, interactions: pd.DataFrame) -> List[Dict]:
        """
        Compute item-item similarity using weighted co-occurrence + cosine similarity.
        """
        # Create user-item matrix
        users = interactions['user_id'].unique()
        products = interactions['product_id'].unique()

        if len(products) < 2:
            print("  Not enough products for similarity computation")
            return []

        user_idx = {u: i for i, u in enumerate(users)}
        product_idx = {p: i for i, p in enumerate(products)}

        # Build sparse matrix
        row_indices = interactions['user_id'].map(user_idx).values
        col_indices = interactions['product_id'].map(product_idx).values
        values = interactions['weight'].values

        user_item_matrix = sparse.csr_matrix(
            (values, (row_indices, col_indices)),
            shape=(len(users), len(products))
        )

        # Compute item-item similarity (cosine similarity on transposed matrix)
        # For large matrices, compute in batches
        n_products = len(products)
        batch_size = 500

        idx_to_product = {v: k for k, v in product_idx.items()}
        similarity_pairs = []

        # Compute co-occurrence counts (binary user-item matrix)
        binary_matrix = (user_item_matrix > 0).astype(int)
        item_matrix_t = user_item_matrix.T

        for batch_start in range(0, n_products, batch_size):
            batch_end = min(batch_start + batch_size, n_products)
            batch_indices = range(batch_start, batch_end)

            # Compute similarities for this batch
            batch_matrix = item_matrix_t[batch_start:batch_end]
            sim_scores = cosine_similarity(batch_matrix, item_matrix_t)

            # Compute co-occurrence for this batch
            batch_binary = binary_matrix.T[batch_start:batch_end]
            co_occur = (batch_binary @ binary_matrix).toarray()

            # Extract top K for each product in batch
            for local_idx, global_idx in enumerate(batch_indices):
                product_id = idx_to_product[global_idx]
                scores = sim_scores[local_idx]
                co_counts = co_occur[local_idx]

                # Get candidates (excluding self, meeting min co-occurrence)
                candidates = []
                for other_idx in range(n_products):
                    if other_idx == global_idx:
                        continue
                    if co_counts[other_idx] >= self.min_co_occurrence:
                        candidates.append((
                            idx_to_product[other_idx],
                            float(scores[other_idx]),
                            int(co_counts[other_idx])
                        ))

                # Sort by similarity and take top K
                candidates.sort(key=lambda x: x[1], reverse=True)
                for similar_id, sim_score, co_count in candidates[:self.top_k_similar]:
                    similarity_pairs.append({
                        'product_id': product_id,
                        'similar_product_id': similar_id,
                        'similarity_score': sim_score,
                        'co_occurrence_count': co_count,
                    })

            print(f"  Processed products {batch_start}-{batch_end}")

        return similarity_pairs

    def _save_similarities(self, similarity_pairs: List[Dict]):
        """Save similarity scores to database."""
        if not similarity_pairs:
            print("  No similarities to save")
            return

        now = datetime.utcnow()
        for pair in similarity_pairs:
            pair['last_updated'] = now

        df = pd.DataFrame(similarity_pairs)

        with self.engine.begin() as conn:
            # Clear existing similarities
            conn.execute(text("DELETE FROM item_similarity"))

            # Insert new similarities in batches
            batch_size = 10000
            for i in range(0, len(df), batch_size):
                batch = df.iloc[i:i + batch_size]
                batch.to_sql('item_similarity', conn, if_exists='append', index=False)
                print(f"  Saved batch {i // batch_size + 1}")

        print(f"  Total: {len(df)} similarity pairs saved")


if __name__ == "__main__":
    db_url = os.getenv("DATABASE_URL", "postgresql://shopsmart:shopsmart_secret@localhost:5432/shopsmart")
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    pipeline = SimilarityPipeline(db_url, redis_url)
    pipeline.run()

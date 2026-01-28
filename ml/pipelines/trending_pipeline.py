"""
Trending Recommender Pipeline

Computes time-decayed popularity scores for products based on recent events.
Score formula: sum(event_weight * decay_factor) where:
- event_weight: view=1, add_to_cart=3, purchase=5
- decay_factor: exp(-lambda * days_ago) where lambda controls decay rate
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from typing import List
import os
import redis


class TrendingPipeline:
    """Pipeline to compute trending product scores."""

    def __init__(self, db_url: str, redis_url: str = None):
        self.engine = create_engine(db_url)
        self.redis_client = redis.from_url(redis_url) if redis_url else None
        self.event_weights = {
            'view': 1.0,
            'add_to_cart': 3.0,
            'purchase': 5.0
        }
        self.decay_lambda = {
            '7d': 0.3,   # Faster decay for short window
            '30d': 0.1   # Slower decay for longer window
        }

    def run(self, time_windows: List[str] = None):
        """Execute the trending pipeline for specified time windows."""
        if time_windows is None:
            time_windows = ['7d', '30d']

        for window in time_windows:
            print(f"Computing trending scores for {window} window...")
            scores = self._compute_trending_scores(window)
            self._save_scores(scores, window)
            print(f"  Saved {len(scores)} trending scores")

        # Invalidate cache
        if self.redis_client:
            print("Invalidating trending cache...")
            keys = self.redis_client.keys("trending:*")
            if keys:
                self.redis_client.delete(*keys)
            # Also invalidate recommendation cache since trending affects fallback
            rec_keys = self.redis_client.keys("rec:*")
            if rec_keys:
                self.redis_client.delete(*rec_keys)
            print("  Cache invalidated")

        print("Trending pipeline complete!")

    def _compute_trending_scores(self, time_window: str) -> pd.DataFrame:
        """Compute time-decayed popularity scores."""
        days = int(time_window.replace('d', ''))
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Fetch events within the time window
        query = text("""
            SELECT
                e.product_id,
                p.category_id,
                e.event_type,
                e.timestamp
            FROM events e
            JOIN products p ON e.product_id = p.id
            WHERE e.timestamp >= :cutoff
            AND p.is_active = true
        """)

        with self.engine.connect() as conn:
            events_df = pd.read_sql(query, conn, params={'cutoff': cutoff_date})

        if events_df.empty:
            print(f"  No events found for {time_window} window")
            return pd.DataFrame(columns=['product_id', 'category_id', 'score', 'event_count'])

        # Calculate days ago for each event
        now = datetime.utcnow()
        events_df['timestamp'] = pd.to_datetime(events_df['timestamp'])
        events_df['days_ago'] = (now - events_df['timestamp']).dt.total_seconds() / 86400

        # Apply time decay and event weights
        lambda_val = self.decay_lambda[time_window]
        events_df['weight'] = events_df['event_type'].map(self.event_weights)
        events_df['decay'] = np.exp(-lambda_val * events_df['days_ago'])
        events_df['score_contribution'] = events_df['weight'] * events_df['decay']

        # Aggregate by product
        scores = events_df.groupby(['product_id', 'category_id']).agg({
            'score_contribution': 'sum',
            'product_id': 'count'
        })
        scores.columns = ['score', 'event_count']
        scores = scores.reset_index()

        # Normalize scores to 0-100 range
        if scores['score'].max() > 0:
            scores['score'] = (scores['score'] / scores['score'].max()) * 100

        return scores

    def _save_scores(self, scores: pd.DataFrame, time_window: str):
        """Save or update trending scores in the database."""
        if scores.empty:
            return

        scores = scores.copy()
        scores['time_window'] = time_window
        scores['last_updated'] = datetime.utcnow()

        with self.engine.begin() as conn:
            # Delete existing scores for this time window
            conn.execute(text(
                "DELETE FROM trending_scores WHERE time_window = :window"
            ), {'window': time_window})

            # Insert new scores
            scores.to_sql('trending_scores', conn, if_exists='append', index=False)


if __name__ == "__main__":
    db_url = os.getenv("DATABASE_URL", "postgresql://shopsmart:shopsmart_secret@localhost:5432/shopsmart")
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    pipeline = TrendingPipeline(db_url, redis_url)
    pipeline.run()

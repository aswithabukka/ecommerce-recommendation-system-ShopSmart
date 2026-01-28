"""
RetailRocket Dataset Loader

Loads the RetailRocket e-commerce dataset into the ShopSmart database.
Dataset: https://www.kaggle.com/datasets/retailrocket/ecommerce-dataset

Required files in ml/data/retailrocket/:
- events.csv: User behavior events (~2.7M records)
- item_properties_part1.csv: Product metadata (optional)
- category_tree.csv: Category hierarchy (optional)
"""

import pandas as pd
import numpy as np
from datetime import datetime
from sqlalchemy import create_engine, text
from pathlib import Path
import os
from tqdm import tqdm


class RetailRocketLoader:
    """Load RetailRocket dataset into ShopSmart database."""

    def __init__(self, db_url: str, data_path: str = None):
        self.engine = create_engine(db_url)
        self.data_path = Path(data_path) if data_path else Path(__file__).parent.parent / "retailrocket"

    def load(self, max_events: int = None, sample_fraction: float = None) -> bool:
        """
        Load RetailRocket data into the database.

        Args:
            max_events: Maximum number of events to load (for testing)
            sample_fraction: Fraction of events to sample (0-1)

        Returns:
            True if successful, False otherwise
        """
        events_file = self.data_path / "events.csv"

        if not events_file.exists():
            print(f"RetailRocket events.csv not found at {events_file}")
            print("Please download from: https://www.kaggle.com/datasets/retailrocket/ecommerce-dataset")
            return False

        print("Loading RetailRocket dataset...")
        print(f"Data path: {self.data_path}")

        # Load categories if available
        self._load_categories()

        # Load events
        return self._load_events(events_file, max_events, sample_fraction)

    def _load_categories(self):
        """Load category tree if available."""
        category_file = self.data_path / "category_tree.csv"

        if not category_file.exists():
            print("  Category file not found, creating default categories...")
            categories = [
                {"name": "Electronics"},
                {"name": "Clothing"},
                {"name": "Home & Garden"},
                {"name": "Sports"},
                {"name": "Books"},
                {"name": "Toys"},
                {"name": "Beauty"},
                {"name": "Food"},
                {"name": "Automotive"},
                {"name": "Health"},
            ]
            df = pd.DataFrame(categories)
        else:
            print("  Loading categories...")
            df = pd.read_csv(category_file)
            # RetailRocket has categoryid and parentid columns
            df = df.rename(columns={
                'categoryid': 'external_id',
                'parentid': 'parent_external_id'
            })
            # Create simple category names
            df['name'] = df['external_id'].apply(lambda x: f"Category_{x}")
            df = df[['name']].drop_duplicates().head(100)  # Limit to 100 categories

        with self.engine.begin() as conn:
            # Clear existing categories
            conn.execute(text("DELETE FROM categories"))
            df.to_sql('categories', conn, if_exists='append', index=False)

        print(f"    Loaded {len(df)} categories")

    def _load_events(self, events_file: Path, max_events: int, sample_fraction: float) -> bool:
        """Load events from RetailRocket CSV."""
        print("  Loading events...")

        # Read events in chunks for memory efficiency
        chunk_size = 100000
        total_loaded = 0
        user_map = {}
        product_map = {}

        # First pass: collect unique visitors and items
        print("    Pass 1: Collecting unique users and products...")
        unique_visitors = set()
        unique_items = set()

        for chunk in pd.read_csv(events_file, chunksize=chunk_size):
            unique_visitors.update(chunk['visitorid'].unique())
            unique_items.update(chunk['itemid'].unique())

            if max_events and len(unique_visitors) > max_events // 10:
                break

        print(f"      Found {len(unique_visitors)} unique visitors")
        print(f"      Found {len(unique_items)} unique items")

        # Sample if requested
        if sample_fraction and sample_fraction < 1.0:
            sample_size = int(len(unique_visitors) * sample_fraction)
            unique_visitors = set(np.random.choice(list(unique_visitors), sample_size, replace=False))
            print(f"      Sampled to {len(unique_visitors)} visitors")

        # Create users
        print("    Creating users...")
        users_df = pd.DataFrame({
            'external_id': [f"RR_{v}" for v in unique_visitors],
            'is_anonymous': True
        })

        with self.engine.begin() as conn:
            conn.execute(text("DELETE FROM events"))
            conn.execute(text("DELETE FROM users"))
            conn.execute(text("DELETE FROM products"))

            users_df.to_sql('users', conn, if_exists='append', index=False)

            # Get user ID mapping
            result = conn.execute(text("SELECT id, external_id FROM users"))
            for row in result:
                user_map[row[1].replace("RR_", "")] = row[0]

        print(f"      Created {len(users_df)} users")

        # Create products
        print("    Creating products...")
        categories_count = 10  # We created 10 default categories

        products_data = []
        for item_id in unique_items:
            products_data.append({
                'external_id': f"RR_ITEM_{item_id}",
                'name': f"RetailRocket Product {item_id}",
                'description': f"Product from RetailRocket dataset (ID: {item_id})",
                'price': round(np.random.uniform(9.99, 499.99), 2),
                'image_url': f"https://picsum.photos/seed/{item_id}/400/400",
                'category_id': (item_id % categories_count) + 1,
                'is_active': True
            })

        products_df = pd.DataFrame(products_data)

        with self.engine.begin() as conn:
            products_df.to_sql('products', conn, if_exists='append', index=False)

            # Get product ID mapping
            result = conn.execute(text("SELECT id, external_id FROM products"))
            for row in result:
                item_id = row[1].replace("RR_ITEM_", "")
                product_map[int(item_id)] = row[0]

        print(f"      Created {len(products_df)} products")

        # Second pass: load events
        print("    Pass 2: Loading events...")
        event_type_map = {
            'view': 'view',
            'addtocart': 'add_to_cart',
            'transaction': 'purchase'
        }

        events_batch = []
        batch_size = 10000

        for chunk in tqdm(pd.read_csv(events_file, chunksize=chunk_size), desc="Processing events"):
            # Filter to sampled visitors
            chunk = chunk[chunk['visitorid'].isin([int(v.replace("RR_", "")) for v in user_map.keys() if v.replace("RR_", "").isdigit()] if sample_fraction else chunk['visitorid'])]

            for _, row in chunk.iterrows():
                visitor_id = str(int(row['visitorid']))
                item_id = int(row['itemid'])

                if visitor_id not in user_map or item_id not in product_map:
                    continue

                event_type = event_type_map.get(row['event'])
                if not event_type:
                    continue

                events_batch.append({
                    'user_id': user_map[visitor_id],
                    'product_id': product_map[item_id],
                    'event_type': event_type,
                    'timestamp': datetime.fromtimestamp(row['timestamp'] / 1000),
                })

                if len(events_batch) >= batch_size:
                    self._save_events_batch(events_batch)
                    total_loaded += len(events_batch)
                    events_batch = []

                    if max_events and total_loaded >= max_events:
                        break

            if max_events and total_loaded >= max_events:
                break

        # Save remaining events
        if events_batch:
            self._save_events_batch(events_batch)
            total_loaded += len(events_batch)

        print(f"      Loaded {total_loaded} events")
        return True

    def _save_events_batch(self, events: list):
        """Save a batch of events to database."""
        df = pd.DataFrame(events)
        with self.engine.begin() as conn:
            df.to_sql('events', conn, if_exists='append', index=False)


if __name__ == "__main__":
    db_url = os.getenv("DATABASE_URL", "postgresql://shopsmart:shopsmart_secret@localhost:5432/shopsmart")
    data_path = os.getenv("DATA_PATH", None)

    loader = RetailRocketLoader(db_url, data_path)

    # Load with optional limits for testing
    max_events = int(os.getenv("MAX_EVENTS", "0")) or None
    sample_fraction = float(os.getenv("SAMPLE_FRACTION", "0")) or None

    success = loader.load(max_events=max_events, sample_fraction=sample_fraction)

    if success:
        print("\nRetailRocket data loaded successfully!")
        print("Run the ML pipelines to generate recommendations:")
        print("  python -m pipelines.trending_pipeline")
        print("  python -m pipelines.similarity_pipeline")
    else:
        print("\nFailed to load RetailRocket data.")
        print("You can generate synthetic data instead:")
        print("  python -m data.seed.synthetic_generator")

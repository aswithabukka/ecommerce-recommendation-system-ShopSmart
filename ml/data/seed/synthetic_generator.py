"""
Synthetic Data Generator

Generates synthetic e-commerce data for testing the recommendation system.
Use this when RetailRocket dataset is not available.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
import os
from tqdm import tqdm


class SyntheticDataGenerator:
    """Generate synthetic e-commerce data."""

    def __init__(self, db_url: str):
        self.engine = create_engine(db_url)
        self.categories = [
            "Electronics",
            "Clothing",
            "Home & Garden",
            "Sports",
            "Books",
            "Toys",
            "Beauty",
            "Food",
            "Automotive",
            "Health",
        ]
        self.category_id_map = {}  # Will be populated after categories are created

    def generate_all(
        self,
        num_products: int = 1000,
        num_users: int = 500,
        num_events: int = 50000,
        days_back: int = 90,
    ):
        """Generate complete synthetic dataset."""
        print("Generating synthetic data...")
        print(f"  Products: {num_products}")
        print(f"  Users: {num_users}")
        print(f"  Events: {num_events}")
        print(f"  Time span: {days_back} days")

        # Clear existing data
        print("Clearing existing data...")
        with self.engine.begin() as conn:
            conn.execute(text("DELETE FROM product_reviews"))
            conn.execute(text("DELETE FROM events"))
            conn.execute(text("DELETE FROM item_similarity"))
            conn.execute(text("DELETE FROM trending_scores"))
            conn.execute(text("DELETE FROM daily_event_stats"))
            conn.execute(text("DELETE FROM users"))
            conn.execute(text("DELETE FROM products"))
            conn.execute(text("DELETE FROM categories"))
            # Commit happens automatically at end of with block

        print("Data cleared successfully")

        # Try to reset sequences in a separate transaction (may fail if user doesn't have ownership privileges)
        # If this fails, it won't affect the data clearing above
        try:
            with self.engine.begin() as conn:
                conn.execute(text("ALTER SEQUENCE categories_id_seq RESTART WITH 1"))
                conn.execute(text("ALTER SEQUENCE products_id_seq RESTART WITH 1"))
                conn.execute(text("ALTER SEQUENCE users_id_seq RESTART WITH 1"))
                conn.execute(text("ALTER SEQUENCE events_id_seq RESTART WITH 1"))
                conn.execute(text("ALTER SEQUENCE product_reviews_id_seq RESTART WITH 1"))
            print("Sequences reset successfully")
        except Exception as e:
            print(f"Warning: Could not reset sequences (will continue with existing sequence values): {str(e)[:100]}")

        print("\n1. Generating categories...")
        self._generate_categories()

        print("2. Generating products...")
        self._generate_products(num_products)

        print("3. Generating users...")
        self._generate_users(num_users)

        print("4. Generating events...")
        self._generate_events(num_events, days_back)

        print("\nSynthetic data generation complete!")
        print("\nRun the ML pipelines to generate recommendations:")
        print("  python -m pipelines.trending_pipeline")
        print("  python -m pipelines.similarity_pipeline")

    def _generate_categories(self):
        """Insert categories and return their IDs."""
        categories_df = pd.DataFrame({'name': self.categories})

        with self.engine.begin() as conn:
            categories_df.to_sql('categories', conn, if_exists='append', index=False)

        # Fetch the actual category IDs that were created
        with self.engine.connect() as conn:
            result = pd.read_sql("SELECT id, name FROM categories ORDER BY id", conn)
            self.category_id_map = dict(zip(result['name'], result['id']))

        print(f"    Created {len(self.categories)} categories")
        print(f"    Category IDs: {list(self.category_id_map.values())}")

    def _generate_products(self, num_products: int):
        """Generate synthetic products."""
        np.random.seed(42)

        # Category-specific image URLs from Unsplash
        category_images = {
            "Electronics": "https://images.unsplash.com/photo-1498049794561-7780e7231661?w=400&h=400&fit=crop",
            "Clothing": "https://images.unsplash.com/photo-1523381210434-271e8be1f52b?w=400&h=400&fit=crop",
            "Home & Garden": "https://images.unsplash.com/photo-1556912173-3bb406ef7e77?w=400&h=400&fit=crop",
            "Sports": "https://images.unsplash.com/photo-1461896836934-ffe607ba8211?w=400&h=400&fit=crop",
            "Books": "https://images.unsplash.com/photo-1495446815901-a7297e633e8d?w=400&h=400&fit=crop",
            "Toys": "https://images.unsplash.com/photo-1558060370-d644479cb6f7?w=400&h=400&fit=crop",
            "Beauty": "https://images.unsplash.com/photo-1596462502278-27bfdc403348?w=400&h=400&fit=crop",
            "Food": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=400&h=400&fit=crop",
            "Automotive": "https://images.unsplash.com/photo-1492144534655-ae79c964c9d7?w=400&h=400&fit=crop",
            "Health": "https://images.unsplash.com/photo-1505751172876-fa1923c5c528?w=400&h=400&fit=crop",
        }

        products = []
        product_names = [
            "Premium", "Essential", "Pro", "Ultra", "Classic", "Modern", "Smart",
            "Deluxe", "Basic", "Advanced", "Compact", "Professional", "Elite",
            "Standard", "Superior", "Value", "Luxury", "Eco", "Tech", "Comfort"
        ]
        product_types = [
            "Widget", "Gadget", "Device", "Tool", "Kit", "Set", "Pack",
            "Bundle", "Collection", "Series", "Edition", "Model", "System"
        ]

        for i in range(num_products):
            category_idx = i % len(self.categories)
            category_name = self.categories[category_idx]
            name_prefix = np.random.choice(product_names)
            name_suffix = np.random.choice(product_types)

            # Use the actual category ID from the database
            category_id = self.category_id_map[category_name]

            products.append({
                'external_id': f'PROD_{i:05d}',
                'name': f'{name_prefix} {category_name} {name_suffix} #{i}',
                'description': f'High-quality {category_name.lower()} product with excellent features and great value.',
                'price': round(np.random.uniform(9.99, 499.99), 2),
                'image_url': category_images[category_name],
                'category_id': category_id,
                'is_active': True
            })

        df = pd.DataFrame(products)

        with self.engine.begin() as conn:
            df.to_sql('products', conn, if_exists='append', index=False)

        print(f"    Created {num_products} products")

    def _generate_users(self, num_users: int):
        """Generate synthetic users."""
        np.random.seed(42)

        users = []
        for i in range(num_users):
            users.append({
                'external_id': f'USER_{i:05d}',
                'is_anonymous': np.random.random() > 0.3  # 70% anonymous
            })

        df = pd.DataFrame(users)

        with self.engine.begin() as conn:
            df.to_sql('users', conn, if_exists='append', index=False)

        print(f"    Created {num_users} users")

    def _generate_events(self, num_events: int, days_back: int):
        """Generate synthetic events with realistic patterns."""
        np.random.seed(42)

        # Get product and user IDs
        with self.engine.connect() as conn:
            products_df = pd.read_sql("SELECT id, category_id FROM products", conn)
            users_df = pd.read_sql("SELECT id FROM users", conn)

        product_ids = products_df['id'].tolist()
        user_ids = users_df['id'].tolist()

        # Group products by category for realistic user preferences
        products_by_category = products_df.groupby('category_id')['id'].apply(list).to_dict()
        num_categories = len(products_by_category)

        # Assign each user 1-2 preferred categories (realistic shopping behavior)
        user_preferences = {}
        for user_id in user_ids:
            # Each user has 1-2 preferred categories
            num_prefs = np.random.choice([1, 2], p=[0.7, 0.3])
            preferred_cats = np.random.choice(
                list(products_by_category.keys()),
                size=num_prefs,
                replace=False
            )
            user_preferences[user_id] = preferred_cats

        # Create product popularity distribution (power law - some products are much more popular)
        popularity = np.power(np.arange(1, len(product_ids) + 1), -1.2)
        popularity = popularity / popularity.sum()

        # Create user activity distribution (some users are more active)
        user_activity = np.power(np.arange(1, len(user_ids) + 1), -0.8)
        user_activity = user_activity / user_activity.sum()

        # Generate events
        events = []
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days_back)

        print(f"    Generating {num_events} events...")

        for _ in tqdm(range(num_events), desc="    Progress"):
            # Select user (weighted by activity)
            user_id = np.random.choice(user_ids, p=user_activity)

            # Select product based on user preferences (90% from preferred categories, 10% random)
            if np.random.random() < 0.9:
                # Choose from preferred categories
                preferred_cat = np.random.choice(user_preferences[user_id])
                category_products = products_by_category[preferred_cat]
                product_id = np.random.choice(category_products)
            else:
                # Random product (exploration)
                product_id = np.random.choice(product_ids, p=popularity)

            # Event type distribution: 80% view, 15% add_to_cart, 5% purchase
            event_type = np.random.choice(
                ['view', 'add_to_cart', 'purchase'],
                p=[0.80, 0.15, 0.05]
            )

            # Random timestamp with recency bias (more recent events more likely)
            days_ago = np.random.exponential(scale=days_back / 3)
            days_ago = min(days_ago, days_back)
            timestamp = end_time - timedelta(days=days_ago)

            events.append({
                'user_id': int(user_id),
                'product_id': int(product_id),
                'event_type': event_type,
                'timestamp': timestamp,
                'session_id': f'sess_{user_id}_{np.random.randint(1, 10)}'
            })

        # Save events in batches
        df = pd.DataFrame(events)
        batch_size = 10000

        with self.engine.begin() as conn:
            for i in range(0, len(df), batch_size):
                batch = df.iloc[i:i + batch_size]
                batch.to_sql('events', conn, if_exists='append', index=False)

        # Print statistics
        event_counts = df['event_type'].value_counts()
        print(f"    Created {len(df)} events:")
        print(f"      - Views: {event_counts.get('view', 0)}")
        print(f"      - Add to cart: {event_counts.get('add_to_cart', 0)}")
        print(f"      - Purchases: {event_counts.get('purchase', 0)}")


if __name__ == "__main__":
    db_url = os.getenv("DATABASE_URL", "postgresql://shopsmart:shopsmart_secret@localhost:5432/shopsmart")

    generator = SyntheticDataGenerator(db_url)

    # Parse optional parameters
    num_products = int(os.getenv("NUM_PRODUCTS", "1000"))
    num_users = int(os.getenv("NUM_USERS", "500"))
    num_events = int(os.getenv("NUM_EVENTS", "50000"))
    days_back = int(os.getenv("DAYS_BACK", "90"))

    generator.generate_all(
        num_products=num_products,
        num_users=num_users,
        num_events=num_events,
        days_back=days_back,
    )

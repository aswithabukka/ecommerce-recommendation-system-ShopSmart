#!/bin/bash
# ShopSmart Startup Script

set -e

echo "🛍️  Starting ShopSmart E-Commerce Recommendation System"
echo "=================================================="
echo ""

# Navigate to infra directory
cd "$(dirname "$0")/infra"

echo "📦 Step 1: Starting infrastructure services (PostgreSQL, Redis)..."
docker compose up -d postgres redis

echo "⏳ Waiting for services to be healthy..."
sleep 5

# Check if services are running
if ! docker compose ps | grep -q "shopsmart-db.*Up"; then
    echo "❌ PostgreSQL failed to start"
    exit 1
fi

if ! docker compose ps | grep -q "shopsmart-redis.*Up"; then
    echo "❌ Redis failed to start"
    exit 1
fi

echo "✅ Infrastructure services are running"
echo ""

echo "🚀 Step 2: Starting application services..."
docker compose up -d backend frontend

echo "⏳ Waiting for application to start..."
sleep 10

echo ""
echo "📊 Step 3: Loading sample data..."
echo "Choose data source:"
echo "  1) Synthetic data (quick, ~1 minute)"
echo "  2) RetailRocket dataset (requires download, ~5 minutes)"
echo ""
read -p "Enter choice (1 or 2, or 's' to skip): " choice

case $choice in
    1)
        echo "Generating synthetic data..."
        docker compose --profile ml run --rm ml-pipeline python -m data.seed.synthetic_generator
        ;;
    2)
        echo "Loading RetailRocket data..."
        if [ ! -f "../ml/data/retailrocket/events.csv" ]; then
            echo "❌ RetailRocket dataset not found!"
            echo "   Download from: https://www.kaggle.com/datasets/retailrocket/ecommerce-dataset"
            echo "   Place files in: ml/data/retailrocket/"
            exit 1
        fi
        docker compose --profile ml run --rm ml-pipeline python -m data.seed.retailrocket_loader
        ;;
    s|S)
        echo "⏭️  Skipping data loading"
        ;;
    *)
        echo "Invalid choice. Skipping data loading."
        ;;
esac

if [ "$choice" = "1" ] || [ "$choice" = "2" ]; then
    echo ""
    echo "🤖 Step 4: Running ML pipelines..."
    echo "  → Generating trending scores..."
    docker compose --profile ml run --rm ml-pipeline python -m pipelines.trending_pipeline

    echo "  → Computing item similarities..."
    docker compose --profile ml run --rm ml-pipeline python -m pipelines.similarity_pipeline

    echo "✅ ML pipelines completed"
fi

echo ""
echo "=================================================="
echo "🎉 ShopSmart is ready!"
echo "=================================================="
echo ""
echo "Access points:"
echo "  🌐 Frontend:        http://localhost:3000"
echo "  📚 API Docs:        http://localhost:8000/docs"
echo "  👨‍💼 Admin Dashboard: http://localhost:3000/admin"
echo "  ❤️  Health Check:    http://localhost:8000/health"
echo ""
echo "To stop: docker compose down"
echo "To view logs: docker compose logs -f"
echo ""

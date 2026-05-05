#!/bin/bash

echo "=========================================="
echo "Rebuilding and Restarting Docker Services"
echo "=========================================="

# Stop current containers
echo ""
echo "🛑 Stopping containers..."
docker-compose down

# Rebuild images
echo ""
echo "🔨 Rebuilding images..."
docker-compose build --no-cache

# Start services
echo ""
echo "🚀 Starting services..."
docker-compose up -d

# Wait for services to be ready
echo ""
echo "⏳ Waiting for services to be ready..."
sleep 5

# Check logs
echo ""
echo "📋 Checking logs..."
docker-compose logs --tail=50 spam-detection-api

# Check if custom filters loaded
echo ""
echo "=========================================="
echo "Checking Custom Filters Status"
echo "=========================================="
docker-compose logs spam-detection-api | grep -E "(Custom filters|CAKE filter|Filter Registry|Excluded Sites)" || echo "⚠️ No custom filter logs found"

echo ""
echo "=========================================="
echo "✅ Done! Service is running on http://localhost:8010"
echo "=========================================="
echo ""
echo "To view logs: docker-compose logs -f spam-detection-api"
echo "To stop: docker-compose down"

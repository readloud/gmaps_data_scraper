#!/bin/bash
# build.sh - Render build script

echo "🔧 Installing dependencies..."
pip install -r requirements.txt

echo "🎭 Installing Playwright browsers..."
playwright install chromium

echo "📦 Collecting static files..."
python manage.py collectstatic --noinput

echo "✅ Build complete!"
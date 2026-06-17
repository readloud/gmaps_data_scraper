# build.sh
#!/bin/bash

# Exit on error
set -e

echo "🚀 Starting build process..."

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Install Playwright and browsers
echo "🎭 Installing Playwright and browsers..."
playwright install chromium
playwright install-deps

# Run Django collectstatic with environment variable to skip playwright
echo "📁 Collecting static files..."
DJANGO_COLLECT_STATIC=1 python manage.py collectstatic --noinput

echo "✅ Build completed!"

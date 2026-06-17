# build.sh
#!/bin/bash

# Exit on error
set -e

echo "🚀 Starting build process..."

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install --no-cache-dir -r requirements.txt

# Install Playwright and browsers
echo "🎭 Installing Playwright and browsers..."
if grep -q "playwright" requirements.txt; then
    echo "🎭 Installing Playwright..."
    playwright install chromium --with-deps 2>/dev/null || echo "⚠️ Playwright install skipped"
fi

# Run Django collectstatic with environment variable to skip playwright
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput --clear

echo "✅ Build completed!"

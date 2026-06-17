# scraper_data/management/commands/setup_playwright.py
from django.core.management.base import BaseCommand
import subprocess
import sys

class Command(BaseCommand):
    help = 'Install Playwright and browsers'

    def handle(self, *args, **options):
        self.stdout.write('Installing Playwright browsers...')
        try:
            subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
            subprocess.run([sys.executable, "-m", "playwright", "install-deps"], check=True)
            self.stdout.write(self.style.SUCCESS('✅ Playwright browsers installed successfully'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error: {e}'))

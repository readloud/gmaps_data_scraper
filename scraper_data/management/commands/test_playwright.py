# scraper_data/management/commands/test_playwright.py
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Test Playwright installation'

    def handle(self, *args, **options):
        try:
            import playwright
            self.stdout.write(self.style.SUCCESS('✅ Playwright imported successfully'))
            
            # Try to import async playwright
            from playwright.async_api import async_playwright
            self.stdout.write(self.style.SUCCESS('✅ Playwright async_api imported successfully'))
            
        except ImportError as e:
            self.stdout.write(self.style.ERROR(f'❌ Playwright import error: {e}'))

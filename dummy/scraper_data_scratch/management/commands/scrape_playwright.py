"""
Management command untuk scraping dengan Playwright
Cara penggunaan:
python manage.py scrape_playwright masjid --level nasional
python manage.py scrape_playwright "toko sembako" --level provinsi --value "DKI Jakarta"
"""

import asyncio
import sys
from django.core.management.base import BaseCommand
from django.utils import timezone
from scraper_data.models import Place, ScrapingLog
from scraper_data.playwright_maps_scraper import GoogleMapsPlaywrightScraper


class Command(BaseCommand):
    help = 'Scrape Google Maps dengan Playwright'
    
    def add_arguments(self, parser):
        parser.add_argument('keyword', type=str, help='Keyword pencarian')
        parser.add_argument('--level', type=str, default='nasional',
                           choices=['nasional', 'provinsi', 'kota'],
                           help='Level filter lokasi')
        parser.add_argument('--value', type=str, default='',
                           help='Nilai filter (provinsi/kota)')
        parser.add_argument('--max', type=int, default=100,
                           help='Maksimal hasil')
        parser.add_argument('--headless', action='store_true',
                           help='Jalankan headless mode')
    
    def handle(self, *args, **options):
        keyword = options['keyword']
        level = options['level']
        value = options['value']
        max_results = options['max']
        headless = options['headless']
        
        self.stdout.write(f"🚀 Mulai scraping Playwright: {keyword}")
        self.stdout.write(f"📌 Filter: {level} = {value if value else 'semua'}")
        
        # Run async function
        results = asyncio.run(self._run_scraper(
            keyword, level, value, max_results, headless
        ))
        
        self.stdout.write(self.style.SUCCESS(f"✅ Selesai! {len(results)} data tersimpan"))
    
    async def _run_scraper(self, keyword, level, value, max_results, headless):
        """Jalankan scraper async"""
        
        # Buat log entry
        log = ScrapingLog.objects.create(
            keyword=f"{keyword} - {level}:{value}" if value else keyword,
            status='running'
        )
        
        try:
            # Jalankan scraper
            async with GoogleMapsPlaywrightScraper(headless=headless) as scraper:
                data = await scraper.search_by_keyword_with_filter(
                    keyword=keyword,
                    filter_level=level,
                    filter_value=value,
                    max_results=max_results
                )
            
            # Simpan ke database
            saved_count = 0
            for place_data in data:
                place, created = Place.objects.update_or_create(
                    name=place_data.name,
                    defaults={
                        'category': place_data.category,
                        'keyword': keyword,
                        'address': place_data.address,
                        'province': place_data.province,
                        'city': place_data.city,
                        'district': place_data.district,
                        'postal_code': place_data.postal_code,
                        'phone': place_data.phone,
                        'website': place_data.website,
                        'rating': place_data.rating,
                        'reviews_count': place_data.reviews_count,
                        'latitude': place_data.latitude,
                        'longitude': place_data.longitude,
                        'scraped_date': timezone.now(),
                        'is_active': True
                    }
                )
                saved_count += 1
            
            # Update log
            log.total_found = len(data)
            log.total_saved = saved_count
            log.status = 'completed'
            log.completed_at = timezone.now()
            log.save()
            
            return data
            
        except Exception as e:
            log.status = 'failed'
            log.error_message = str(e)
            log.save()
            raise
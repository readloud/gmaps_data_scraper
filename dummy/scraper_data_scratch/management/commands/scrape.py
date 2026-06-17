# scraper_data/management/commands/scrape.py
from django.core.management.base import BaseCommand
from scraper_data.import_to_db import DjangoGoogleMapsScraper

class Command(BaseCommand):
    help = 'Scrape Google Maps data berdasarkan keyword dan filter'
    
    def add_arguments(self, parser):
        parser.add_argument('keyword', type=str, help='Keyword pencarian (masjid, toko sembako, dll)')
        parser.add_argument('--level', type=str, default='nasional', 
                           choices=['nasional', 'provinsi', 'kota'],
                           help='Level filter lokasi')
        parser.add_argument('--value', type=str, default='',
                           help='Value filter (contoh: DKI Jakarta, Surabaya)')
    
    def handle(self, *args, **options):
        keyword = options['keyword']
        level = options['level']
        value = options['value']
        
        self.stdout.write(f"🚀 Mulai scraping: {keyword} - {level}:{value}")
        
        scraper = DjangoGoogleMapsScraper()
        result = scraper.scrape_and_save(keyword, level, value)
        
        self.stdout.write(
            self.style.SUCCESS(f"✅ Selesai! {result} data tersimpan")
        )
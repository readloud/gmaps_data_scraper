# scraper_data/import_to_db.py
import os
import sys
import django
from datetime import datetime

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'maps_scraper_admin.settings')
django.setup()

from scraper_data.models import Place, ScrapingLog
from scraper_data.google_maps_scraper import GoogleMapsScraper
from django.utils import timezone

class DjangoGoogleMapsScraper:
    def __init__(self):
        self.scraper = GoogleMapsScraper(headless=True)
    
    def scrape_and_save(self, keyword, filter_level="nasional", filter_value=""):
        """
        Scrape dan langsung simpan ke database Django
        """
        # Create log entry
        log = ScrapingLog.objects.create(
            keyword=f"{keyword} - {filter_level}:{filter_value}",
            status='running'
        )
        
        try:
            # Do scraping
            data = self.scraper.scrape_with_filter(keyword, filter_level, filter_value)
            
            # Save to database
            saved_count = 0
            for item in data:
                # Parse alamat
                address = item.get('full_address') or item.get('address', '')
                province = item.get('province', '')
                city = item.get('city', '')
                
                # Map kategori
                category = self.map_category(keyword)
                
                # Save or update
                place, created = Place.objects.update_or_create(
                    name=item.get('name', ''),
                    defaults={
                        'category': category,
                        'keyword': keyword,
                        'address': address,
                        'province': province,
                        'city': city,
                        'district': item.get('district', ''),
                        'phone': item.get('phone', ''),
                        'website': item.get('website', ''),
                        'rating': item.get('rating'),
                        'reviews_count': item.get('reviews_count', 0),
                        'latitude': item.get('latitude'),
                        'longitude': item.get('longitude'),
                        'scraped_date': timezone.now(),
                        'is_active': True
                    }
                )
                saved_count += 1
                
                if created:
                    print(f"✅ Menambah: {place.name}")
                else:
                    print(f"🔄 Mengupdate: {place.name}")
            
            # Update log
            log.total_found = len(data)
            log.total_saved = saved_count
            log.status = 'completed'
            log.completed_at = timezone.now()
            log.save()
            
            print(f"\n🎉 Selesai! {saved_count} data tersimpan")
            return saved_count
            
        except Exception as e:
            log.status = 'failed'
            log.error_message = str(e)
            log.save()
            print(f"❌ Error: {e}")
            raise
        
        finally:
            self.scraper.close()
    
    def map_category(self, keyword):
        """Map keyword ke kategori database"""
        keyword_lower = keyword.lower()
        if 'masjid' in keyword_lower:
            return 'masjid'
        elif 'sembako' in keyword_lower or 'toko' in keyword_lower:
            return 'toko_sembako'
        elif 'restoran' in keyword_lower or 'makan' in keyword_lower:
            return 'restaurant'
        elif 'cafe' in keyword_lower or 'kopi' in keyword_lower:
            return 'cafe'
        elif 'hotel' in keyword_lower or 'penginapan' in keyword_lower:
            return 'hotel'
        else:
            return 'lainnya'

# ========== CONTOH PENGGUNAAN ==========
if __name__ == "__main__":
    scraper_db = DjangoGoogleMapsScraper()
    
    # Scrape masjid di seluruh Indonesia
    scraper_db.scrape_and_save("masjid", "nasional")
    
    # Scrape toko sembako di DKI Jakarta
    scraper_db.scrape_and_save("toko sembako", "provinsi", "DKI Jakarta")
import time
import json
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from fake_useragent import UserAgent
import pandas as pd

class GoogleMapsScraper:
    def __init__(self, headless=False):
        """
        Inisialisasi scraper Google Maps
        
        Args:
            headless (bool): Jalankan di background (tanpa UI browser)
        """
        self.driver = None
        self.headless = headless
        self.results = []
        self.setup_driver()
    
    def setup_driver(self):
        """Setup Chrome driver dengan optimal settings"""
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument("--headless")
        
        # Settings untuk menghindari deteksi sebagai bot
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Performance settings
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # User agent random
        ua = UserAgent()
        chrome_options.add_argument(f"--user-agent={ua.random}")
        
        # Preferensi tambahan
        prefs = {
            "profile.default_content_setting_values.notifications": 2,
            "profile.default_content_settings.popups": 0,
            "download.default_directory": "/dev/null"
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        # Setup driver
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        self.wait = WebDriverWait(self.driver, 10)
    
    def search_places(self, keyword, location=""):
        """
        Mencari tempat berdasarkan keyword dan lokasi
        
        Args:
            keyword (str): Jenis tempat (masjid, toko sembako, dll)
            location (str): Lokasi (Jakarta, Surabaya, dll) - kosongkan untuk nasional
        
        Returns:
            list: List of place data
        """
        search_query = f"{keyword} {location}" if location else keyword
        search_url = f"https://www.google.com/maps/search/{search_query.replace(' ', '+')}"
        
        print(f"🔍 Mencari: {search_query}")
        self.driver.get(search_url)
        time.sleep(5)  # Tunggu halaman load
        
        # Scroll untuk memuat lebih banyak hasil
        self.scroll_results_panel()
        
        # Ambil semua place cards
        places = self.extract_places_from_panel()
        
        # Ambil detail untuk setiap tempat
        detailed_places = []
        for idx, place in enumerate(places):
            print(f"📋 Mengambil detail {idx+1}/{len(places)}: {place.get('name', 'Unknown')}")
            detail = self.get_place_details(place)
            if detail:
                detailed_places.append(detail)
            time.sleep(1)  # Delay untuk menghindari block
            
            # Batasi jumlah untuk testing (hapus untuk unlimited)
            # if idx >= 20: break
        
        return detailed_places
    
    def scroll_results_panel(self):
        """Scroll panel hasil untuk memuat lebih banyak data"""
        try:
            # Cari panel scrollable
            scrollable_div = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div[role='feed']"))
            )
            
            # Scroll beberapa kali
            last_height = 0
            scroll_attempts = 0
            while scroll_attempts < 10:  # Maksimal 10 scroll
                self.driver.execute_script(
                    "arguments[0].scrollTop = arguments[0].scrollHeight", 
                    scrollable_div
                )
                time.sleep(2)
                
                new_height = self.driver.execute_script(
                    "return arguments[0].scrollHeight", 
                    scrollable_div
                )
                if new_height == last_height:
                    break
                last_height = new_height
                scroll_attempts += 1
                
        except TimeoutException:
            print("⚠️ Panel scrollable tidak ditemukan")
    
    def extract_places_from_panel(self):
        """Ekstrak data dasar dari panel hasil"""
        places = []
        
        try:
            # Cari semua elemen hasil
            result_elements = self.driver.find_elements(By.CSS_SELECTOR, "div[role='feed'] > div > div")
            
            for elem in result_elements[:50]:  # Batasi 50 hasil awal
                try:
                    # Ekstrak nama
                    name_elem = elem.find_element(By.CSS_SELECTOR, ".fontHeadlineSmall")
                    name = name_elem.text if name_elem else ""
                    
                    # Ekstrak rating dan jumlah review
                    rating_elem = elem.find_elements(By.CSS_SELECTOR, ".fontBodyMedium span[aria-hidden='true']")
                    rating = None
                    reviews_count = 0
                    
                    if rating_elem and len(rating_elem) > 0:
                        rating_text = rating_elem[0].text
                        # Format rating: "4.5 (123 reviews)"
                        match = re.search(r'([\d.]+).*?\((\d+)\)', rating_text)
                        if match:
                            rating = float(match.group(1))
                            reviews_count = int(match.group(2))
                    
                    # Ekstrak kategori/jenis
                    category_elem = elem.find_elements(By.CSS_SELECTOR, ".fontBodyMedium span:not([aria-hidden])")
                    category = category_elem[0].text if category_elem else ""
                    
                    # Ekstrak alamat singkat
                    address_elem = elem.find_elements(By.CSS_SELECTOR, ".W4Efsd:not(.fontBodyMedium)")
                    address = address_elem[0].text if address_elem else ""
                    
                    # Ekstrak link detail
                    link_elem = elem.find_element(By.CSS_SELECTOR, "a")
                    detail_url = link_elem.get_attribute("href") if link_elem else ""
                    
                    places.append({
                        'name': name,
                        'rating': rating,
                        'reviews_count': reviews_count,
                        'category': category,
                        'address': address,
                        'detail_url': detail_url,
                        'element': elem  # Simpan untuk akses detail nanti
                    })
                    
                except NoSuchElementException:
                    continue
                    
        except Exception as e:
            print(f"❌ Error extracting places: {e}")
        
        print(f"✅ Ditemukan {len(places)} tempat")
        return places
    
    def get_place_details(self, place):
        """
        Buka halaman detail tempat dan ekstrak informasi lengkap
        
        Args:
            place (dict): Place data dari panel hasil
        
        Returns:
            dict: Place data dengan detail lengkap
        """
        if not place.get('detail_url'):
            return place
        
        try:
            # Buka tab baru untuk detail
            self.driver.execute_script(f"window.open('{place['detail_url']}', '_blank');")
            time.sleep(2)
            
            # Pindah ke tab baru
            self.driver.switch_to.window(self.driver.window_handles[-1])
            time.sleep(3)
            
            # Tunggu panel detail muncul
            self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div[role='main']"))
            )
            
            # Ekstrak detail
            details = self.extract_place_details()
            
            # Gabungkan dengan data dasar
            place.update(details)
            
            # Tutup tab detail dan kembali ke tab utama
            self.driver.close()
            self.driver.switch_to.window(self.driver.window_handles[0])
            
            return place
            
        except Exception as e:
            print(f"❌ Error getting detail: {e}")
            # Pastikan kembali ke tab utama
            if len(self.driver.window_handles) > 1:
                self.driver.close()
                self.driver.switch_to.window(self.driver.window_handles[0])
            return place
    
    def extract_place_details(self):
        """Ekstrak informasi detail dari halaman tempat"""
        details = {
            'phone': '',
            'website': '',
            'full_address': '',
            'hours': '',
            'latitude': None,
            'longitude': None,
            'price_level': ''
        }
        
        try:
            # Ekstrak telepon
            try:
                phone_elem = self.driver.find_element(By.CSS_SELECTOR, 
                    "button[data-tooltip='Salin nomor telepon'] span")
                details['phone'] = phone_elem.text
            except NoSuchElementException:
                pass
            
            # Ekstrak website
            try:
                website_elem = self.driver.find_element(By.CSS_SELECTOR, 
                    "a[data-tooltip='Buka situs web']")
                details['website'] = website_elem.get_attribute('href')
            except NoSuchElementException:
                pass
            
            # Ekstrak alamat lengkap
            try:
                address_elem = self.driver.find_element(By.CSS_SELECTOR, 
                    "button[data-tooltip='Salin alamat'] span")
                details['full_address'] = address_elem.text
            except NoSuchElementException:
                pass
            
            # Ekstrak jam operasional
            try:
                hours_elems = self.driver.find_elements(By.CSS_SELECTOR, 
                    "table tr td div span")
                hours_text = [h.text for h in hours_elems if h.text]
                details['hours'] = '; '.join(hours_text[:10])
            except:
                pass
            
            # Ekstrak koordinat dari URL
            current_url = self.driver.current_url
            lat_lon_match = re.search(r'@([-\d.]+),([-\d.]+)', current_url)
            if lat_lon_match:
                details['latitude'] = float(lat_lon_match.group(1))
                details['longitude'] = float(lat_lon_match.group(2))
            
            # Ekstrak price level (jika ada)
            try:
                price_elem = self.driver.find_element(By.CSS_SELECTOR, 
                    "span[aria-label*='rupiah']")
                details['price_level'] = price_elem.text
            except:
                pass
                
        except Exception as e:
            print(f"⚠️ Error extracting details: {e}")
        
        return details
    
    def parse_location_from_address(self, address):
        """
        Parse alamat untuk mendapatkan provinsi dan kota
        
        Args:
            address (str): Alamat lengkap
        
        Returns:
            tuple: (province, city, district)
        """
        # List provinsi di Indonesia
        provinces = [
            'Aceh', 'Sumatera Utara', 'Sumatera Barat', 'Riau', 'Kepulauan Riau',
            'Jambi', 'Bengkulu', 'Sumatera Selatan', 'Kepulauan Bangka Belitung',
            'Lampung', 'Banten', 'DKI Jakarta', 'Jawa Barat', 'Jawa Tengah',
            'DI Yogyakarta', 'Jawa Timur', 'Bali', 'Nusa Tenggara Barat',
            'Nusa Tenggara Timur', 'Kalimantan Barat', 'Kalimantan Tengah',
            'Kalimantan Selatan', 'Kalimantan Timur', 'Kalimantan Utara',
            'Sulawesi Utara', 'Sulawesi Tengah', 'Sulawesi Selatan',
            'Sulawesi Tenggara', 'Sulawesi Barat', 'Gorontalo', 'Maluku',
            'Maluku Utara', 'Papua', 'Papua Barat', 'Papua Tengah', 'Papua Pegunungan'
        ]
        
        province = ""
        city = ""
        district = ""
        
        # Cari provinsi
        for prov in provinces:
            if prov.lower() in address.lower():
                province = prov
                break
        
        # Split alamat dengan koma
        parts = address.split(',')
        
        # Coba ekstrak kota (biasanya sebelum provinsi)
        if province and len(parts) > 1:
            for i, part in enumerate(parts):
                if province.lower() in part.lower() and i > 0:
                    city = parts[i-1].strip()
                    break
        
        # Ekstrak kecamatan (jika ada)
        if 'kecamatan' in address.lower() or 'kec.' in address.lower():
            kec_match = re.search(r'Kec(?:amatan)?\.?\s+([^,]+)', address, re.IGNORECASE)
            if kec_match:
                district = kec_match.group(1).strip()
        
        return province, city, district
    
    def scrape_with_filter(self, keyword, filter_level="nasional", filter_value=""):
        """
        Scrape dengan filter lokasi (nasional/provinsi/kota)
        
        Args:
            keyword (str): Keyword pencarian
            filter_level (str): 'nasional', 'provinsi', 'kota'
            filter_value (str): Value untuk filter (nama provinsi/kota)
        
        Returns:
            list: Data yang sudah difilter
        """
        # Tentukan lokasi berdasarkan filter
        if filter_level == "provinsi":
            search_location = filter_value
        elif filter_level == "kota":
            search_location = filter_value
        else:  # nasional
            search_location = "Indonesia"
        
        # Lakukan scraping
        raw_data = self.search_places(keyword, search_location)
        
        # Filter lebih lanjut berdasarkan level
        filtered_data = []
        for place in raw_data:
            address = place.get('full_address') or place.get('address', '')
            province, city, district = self.parse_location_from_address(address)
            
            place['province'] = province
            place['city'] = city
            place['district'] = district
            
            # Apply filter berdasarkan level
            if filter_level == "provinsi" and filter_value:
                if province.lower() == filter_value.lower():
                    filtered_data.append(place)
            elif filter_level == "kota" and filter_value:
                if city.lower() == filter_value.lower():
                    filtered_data.append(place)
            else:  # nasional
                filtered_data.append(place)
        
        print(f"✅ Data setelah filter: {len(filtered_data)} dari {len(raw_data)} tempat")
        return filtered_data
    
    def save_to_json(self, data, filename):
        """Simpan data ke file JSON"""
        # Konversi untuk serializable
        serializable_data = []
        for item in data:
            # Hapus elemen Selenium
            if 'element' in item:
                del item['element']
            serializable_data.append(item)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(serializable_data, f, indent=2, ensure_ascii=False)
        print(f"💾 Data tersimpan di {filename}")
    
    def save_to_csv(self, data, filename):
        """Simpan data ke file CSV"""
        # Hapus elemen Selenium
        for item in data:
            if 'element' in item:
                del item['element']
        
        df = pd.DataFrame(data)
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"💾 Data tersimpan di {filename}")
    
    def close(self):
        """Tutup browser"""
        if self.driver:
            self.driver.quit()
            print("🔒 Browser ditutup")

# ========== CONTOH PENGGUNAAN ==========
if __name__ == "__main__":
    # Inisialisasi scraper
    scraper = GoogleMapsScraper(headless=False)  # Set True untuk mode tanpa UI
    
    try:
        # Contoh 1: Scrape semua masjid di Indonesia
        print("\n" + "="*50)
        print("CONTOH 1: Scrape Masjid di Seluruh Indonesia")
        print("="*50)
        masjid_data = scraper.scrape_with_filter(
            keyword="masjid",
            filter_level="nasional"
        )
        scraper.save_to_csv(masjid_data, "masjid_indonesia.csv")
        
        # Contoh 2: Scrape toko sembako di DKI Jakarta
        print("\n" + "="*50)
        print("CONTOH 2: Scrape Toko Sembako di DKI Jakarta")
        print("="*50)
        sembako_data = scraper.scrape_with_filter(
            keyword="toko sembako",
            filter_level="provinsi",
            filter_value="DKI Jakarta"
        )
        scraper.save_to_csv(sembako_data, "toko_sembako_jakarta.csv")
        
        # Contoh 3: Scrape restoran di Surabaya
        print("\n" + "="*50)
        print("CONTOH 3: Scrape Restoran di Surabaya")
        print("="*50)
        restoran_data = scraper.scrape_with_filter(
            keyword="restoran",
            filter_level="kota",
            filter_value="Surabaya"
        )
        scraper.save_to_json(restoran_data, "restoran_surabaya.json")
        
    finally:
        scraper.close()
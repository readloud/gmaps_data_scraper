"""
Google Maps Scraper menggunakan Playwright
Fitur: Anti-detection, async, export ke JSON/CSV, filter lokasi
"""

import asyncio
import json
import re
import os
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path

import pandas as pd
from playwright.async_api import async_playwright, Browser, Page, Playwright
from playwright_stealth import stealth_async
from fake_useragent import UserAgent


@dataclass
class PlaceData:
    """Data class untuk tempat yang di-scrape"""
    name: str = ""
    category: str = ""
    address: str = ""
    phone: str = ""
    website: str = ""
    rating: float = 0.0
    reviews_count: int = 0
    latitude: float = None
    longitude: float = None
    province: str = ""
    city: str = ""
    district: str = ""
    postal_code: str = ""
    price_level: str = ""
    hours: str = ""
    plus_code: str = ""
    search_keyword: str = ""
    scraped_at: str = ""
    
    def to_dict(self):
        return asdict(self)


class GoogleMapsPlaywrightScraper:
    """
    Google Maps Scraper dengan Playwright
    Bisa scraping unlimited data dengan anti-detection
    """
    
    # Daftar provinsi Indonesia untuk parsing alamat
    INDONESIAN_PROVINCES = [
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
    
    def __init__(self, headless: bool = False, use_stealth: bool = True):
        """
        Inisialisasi scraper
        
        Args:
            headless: Jalankan tanpa UI browser
            use_stealth: Gunakan stealth mode untuk hindari deteksi
        """
        self.headless = headless
        self.use_stealth = use_stealth
        self.playwright: Playwright = None
        self.browser: Browser = None
        self.page: Page = None
        self.ua = UserAgent()
        
    async def __aenter__(self):
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    async def start(self):
        """Start browser dan setup anti-detection"""
        self.playwright = await async_playwright().start()
        
        # Pilih browser (Firefox lebih stealth untuk Google Maps)
        self.browser = await self.playwright.firefox.launch(
            headless=self.headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-features=IsolateOrigins,site-per-process',
            ]
        )
        
        # Buat context dengan random viewport dan user agent
        viewport = {'width': 1920, 'height': 1080}
        user_agent = self.ua.random
        
        context = await self.browser.new_context(
            viewport=viewport,
            user_agent=user_agent,
            locale='id-ID',
            timezone_id='Asia/Jakarta',
            extra_http_headers={
                'Accept-Language': 'id-ID,id;q=0.9,en;q=0.8',
            }
        )
        
        self.page = await context.new_page()
        
        # Apply stealth jika diperlukan
        if self.use_stealth:
            await stealth_async(self.page)
        
        print(f"✅ Browser started (Stealth: {self.use_stealth})")
        print(f"📱 User Agent: {user_agent[:100]}...")
    
    async def close(self):
        """Tutup semua resource"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        print("🔒 Browser closed")
    
    async def search(self, keyword: str, location: str = "Indonesia", 
                     max_results: int = 100) -> List[PlaceData]:
        """
        Mencari tempat di Google Maps
        
        Args:
            keyword: Jenis tempat (masjid, toko sembako, restoran)
            location: Lokasi spesifik (Jakarta, Surabaya) atau kosong untuk nasional
            max_results: Maksimal hasil yang diambil
        
        Returns:
            List of PlaceData objects
        """
        # Format search query
        if location and location.lower() != "indonesia":
            search_query = f"{keyword} di {location}"
        else:
            search_query = f"{keyword} Indonesia"
        
        search_url = f"https://www.google.com/maps/search/{search_query.replace(' ', '+')}"
        
        print(f"\n🔍 Mencari: {search_query}")
        print(f"🌐 URL: {search_url}")
        
        # Navigasi ke halaman search
        await self.page.goto(search_url, wait_until='networkidle')
        await asyncio.sleep(3)
        
        # Scroll untuk memuat semua hasil
        await self._scroll_results_panel()
        
        # Extract data dari panel hasil
        places = await self._extract_places_from_panel(max_results)
        
        # Ambil detail untuk setiap tempat
        detailed_places = []
        for idx, place in enumerate(places):
            print(f"📋 [{idx+1}/{len(places)}] Mengambil detail: {place.name[:50]}...")
            
            if place.website or place.phone:
                # Sudah punya detail dari panel
                detailed_places.append(place)
            else:
                # Buka detail page
                detail = await self._get_place_detail(place)
                if detail:
                    detailed_places.append(detail)
            
            # Delay untuk hindari rate limiting
            await asyncio.sleep(1.5)
        
        # Parse lokasi dari alamat
        for place in detailed_places:
            place.province, place.city, place.district, place.postal_code = \
                self._parse_location(place.address)
            place.search_keyword = keyword
            place.scraped_at = datetime.now().isoformat()
        
        print(f"\n✅ Selesai! Mendapatkan {len(detailed_places)} tempat")
        return detailed_places
    
    async def _scroll_results_panel(self):
        """Scroll panel hasil untuk memuat lebih banyak data"""
        try:
            # Cari panel scrollable
            scrollable_div = await self.page.query_selector('div[role="feed"]')
            
            if not scrollable_div:
                print("⚠️ Panel scrollable tidak ditemukan")
                return
            
            last_height = 0
            scroll_attempts = 0
            max_scrolls = 15  # Maksimal scroll
            
            while scroll_attempts < max_scrolls:
                # Scroll ke bawah
                await self.page.evaluate(
                    'arguments[0].scrollTop = arguments[0].scrollHeight',
                    scrollable_div
                )
                await asyncio.sleep(2)
                
                # Cek apakah sudah sampai bawah
                new_height = await self.page.evaluate(
                    'arguments[0].scrollHeight',
                    scrollable_div
                )
                
                if new_height == last_height:
                    break
                    
                last_height = new_height
                scroll_attempts += 1
                print(f"📜 Scroll {scroll_attempts}: memuat lebih banyak data...")
                
        except Exception as e:
            print(f"⚠️ Error saat scroll: {e}")
    
    async def _extract_places_from_panel(self, max_results: int) -> List[PlaceData]:
        """Ekstrak data dari panel hasil pencarian"""
        places = []
        
        try:
            # Tunggu hasil muncul
            await self.page.wait_for_selector('div[role="feed"] > div > div', timeout=10000)
            
            # Ambil semua elemen hasil
            result_elements = await self.page.query_selector_all('div[role="feed"] > div > div')
            
            for idx, elem in enumerate(result_elements[:max_results]):
                try:
                    place = PlaceData()
                    
                    # Nama tempat
                    name_elem = await elem.query_selector('.fontHeadlineSmall')
                    if name_elem:
                        place.name = (await name_elem.text_content()) or ""
                    
                    # Rating dan review count
                    rating_elem = await elem.query_selector('.fontBodyMedium span[aria-hidden="true"]')
                    if rating_elem:
                        rating_text = (await rating_elem.text_content()) or ""
                        # Format: "4.5 (123 reviews)"
                        match = re.search(r'([\d.]+).*?\((\d+)\)', rating_text)
                        if match:
                            place.rating = float(match.group(1))
                            place.reviews_count = int(match.group(2))
                    
                    # Kategori
                    category_elem = await elem.query_selector('.fontBodyMedium span:not([aria-hidden])')
                    if category_elem:
                        place.category = (await category_elem.text_content()) or ""
                    
                    # Alamat singkat
                    address_elem = await elem.query_selector('.W4Efsd:not(.fontBodyMedium)')
                    if address_elem:
                        place.address = (await address_elem.text_content()) or ""
                    
                    # Telepon (mungkin tidak ada di panel)
                    phone_elem = await elem.query_selector('span[aria-label*="telp"], span[aria-label*="Telepon"]')
                    if phone_elem:
                        place.phone = (await phone_elem.text_content()) or ""
                    
                    # Website
                    website_elem = await elem.query_selector('a[aria-label*="website"], a[aria-label*="situs"]')
                    if website_elem:
                        href = await website_elem.get_attribute('href')
                        if href:
                            place.website = href
                    
                    if place.name:  # Hanya tambah jika ada nama
                        places.append(place)
                        
                except Exception as e:
                    print(f"⚠️ Error extracting place {idx}: {e}")
                    continue
            
        except Exception as e:
            print(f"❌ Error extracting places: {e}")
        
        print(f"📊 Ditemukan {len(places)} tempat dari panel")
        return places
    
    async def _get_place_detail(self, place: PlaceData) -> Optional[PlaceData]:
        """
        Buka halaman detail tempat dan ambil info lengkap
        
        Args:
            place: PlaceData dengan info dasar
        
        Returns:
            PlaceData dengan detail lengkap
        """
        try:
            # Cari link detail dari nama tempat
            # Klik pada elemen tempat untuk buka panel detail
            # Ini adalah pendekatan alternatif karena Google Maps SPA
            
            # Simpan current URL untuk kembali
            current_url = self.page.url
            
            # Cari dan klik link ke detail
            detail_link = await self.page.query_selector(f'text="{place.name}"')
            if not detail_link:
                return place
            
            # Klik untuk buka detail panel (tanpa pindah halaman)
            await detail_link.click()
            await asyncio.sleep(2)
            
            # Tunggu panel detail muncul
            await self.page.wait_for_selector('div[role="main"]', timeout=5000)
            
            # Ambil informasi tambahan
            # Telepon
            phone_selectors = [
                'button[data-tooltip="Salin nomor telepon"] span',
                'button[aria-label*="Telepon"] span',
                'div[data-attrid*="phone"] span'
            ]
            for selector in phone_selectors:
                phone_elem = await self.page.query_selector(selector)
                if phone_elem:
                    place.phone = (await phone_elem.text_content()) or ""
                    break
            
            # Website
            website_selectors = [
                'a[data-tooltip="Buka situs web"]',
                'a[aria-label*="Website"]',
                'div[data-attrid*="website"] a'
            ]
            for selector in website_selectors:
                website_elem = await self.page.query_selector(selector)
                if website_elem:
                    href = await website_elem.get_attribute('href')
                    if href:
                        place.website = href
                    break
            
            # Alamat lengkap
            address_selectors = [
                'button[data-tooltip="Salin alamat"] span',
                'div[data-attrid*="address"] span',
                'div[aria-label*="Alamat"] span'
            ]
            for selector in address_selectors:
                address_elem = await self.page.query_selector(selector)
                if address_elem:
                    full_address = (await address_elem.text_content()) or ""
                    if full_address and len(full_address) > len(place.address):
                        place.address = full_address
                    break
            
            # Plus Code
            plus_code_elem = await self.page.query_selector('button[data-tooltip="Salin kode plus"] span')
            if plus_code_elem:
                place.plus_code = (await plus_code_elem.text_content()) or ""
            
            # Harga (price level)
            price_elem = await self.page.query_selector('span[aria-label*="rupiah"], span[aria-label*="harga"]')
            if price_elem:
                place.price_level = (await price_elem.text_content()) or ""
            
            # Jam operasional
            hours_elem = await self.page.query_selector('div[aria-label*="Jam"], div[data-attrid*="hours"]')
            if hours_elem:
                place.hours = (await hours_elem.text_content()) or ""
            
            # Koordinat dari URL
            lat, lng = self._extract_coordinates(self.page.url)
            if lat and lng:
                place.latitude = lat
                place.longitude = lng
            
        except Exception as e:
            print(f"⚠️ Error getting detail for {place.name}: {e}")
        
        return place
    
    def _extract_coordinates(self, url: str) -> Tuple[Optional[float], Optional[float]]:
        """Ekstrak koordinat dari URL Google Maps"""
        pattern = r'@(-?\d+\.\d+),(-?\d+\.\d+)'
        match = re.search(pattern, url)
        if match:
            return float(match.group(1)), float(match.group(2))
        return None, None
    
    def _parse_location(self, address: str) -> Tuple[str, str, str, str]:
        """
        Parse alamat untuk mendapatkan provinsi, kota, kecamatan, kode pos
        
        Returns:
            Tuple: (province, city, district, postal_code)
        """
        province = ""
        city = ""
        district = ""
        postal_code = ""
        
        if not address:
            return province, city, district, postal_code
        
        address_lower = address.lower()
        
        # Cari provinsi
        for prov in self.INDONESIAN_PROVINCES:
            if prov.lower() in address_lower:
                province = prov
                break
        
        # Cari kata kunci kecamatan
        kec_patterns = [r'kec(?:amatan)?\.?\s+([^,\d]+)', r'kec\.?\s+([^,\d]+)']
        for pattern in kec_patterns:
            match = re.search(pattern, address_lower, re.IGNORECASE)
            if match:
                district = match.group(1).strip().title()
                break
        
        # Cari kota (biasanya setelah kecamatan atau sebelum provinsi)
        parts = address.split(',')
        if province and len(parts) > 1:
            for i, part in enumerate(parts):
                if province.lower() in part.lower() and i > 0:
                    city = parts[i-1].strip()
                    break
        
        # Jika kota masih kosong, coba cari kata "Kota" atau "Kabupaten"
        if not city:
            kota_match = re.search(r'(?:kota|kabupaten)\s+([^,]+)', address_lower, re.IGNORECASE)
            if kota_match:
                city = kota_match.group(1).strip().title()
        
        # Cari kode pos (5 digit)
        postal_match = re.search(r'\b(\d{5})\b', address)
        if postal_match:
            postal_code = postal_match.group(1)
        
        return province, city, district, postal_code
    
    async def search_by_keyword_with_filter(self, keyword: str, filter_level: str = "nasional",
                                            filter_value: str = "", max_results: int = 100) -> List[PlaceData]:
        """
        Search dengan filter level lokasi
        
        Args:
            keyword: Keyword pencarian (masjid, toko sembako, dll)
            filter_level: 'nasional', 'provinsi', 'kota'
            filter_value: Nama provinsi atau kota
            max_results: Maksimal hasil
        """
        # Tentukan lokasi berdasarkan filter
        if filter_level == "provinsi" and filter_value:
            location = filter_value
        elif filter_level == "kota" and filter_value:
            location = filter_value
        else:
            location = "Indonesia"
        
        # Lakukan pencarian
        all_places = await self.search(keyword, location, max_results)
        
        # Filter ulang berdasarkan level (untuk memastikan akurasi)
        if filter_level == "provinsi" and filter_value:
            filtered = [p for p in all_places if filter_value.lower() in p.province.lower()]
            print(f"📌 Filter provinsi '{filter_value}': {len(filtered)} dari {len(all_places)}")
            return filtered
        elif filter_level == "kota" and filter_value:
            filtered = [p for p in all_places if filter_value.lower() in p.city.lower()]
            print(f"📌 Filter kota '{filter_value}': {len(filtered)} dari {len(all_places)}")
            return filtered
        
        return all_places
    
    def save_to_json(self, data: List[PlaceData], filename: str):
        """Simpan ke file JSON"""
        output = [p.to_dict() for p in data]
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        print(f"💾 Data tersimpan di {filename}")
    
    def save_to_csv(self, data: List[PlaceData], filename: str):
        """Simpan ke file CSV"""
        output = [p.to_dict() for p in data]
        df = pd.DataFrame(output)
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"💾 Data tersimpan di {filename}")
    
    def save_to_excel(self, data: List[PlaceData], filename: str):
        """Simpan ke file Excel"""
        output = [p.to_dict() for p in data]
        df = pd.DataFrame(output)
        df.to_excel(filename, index=False, engine='openpyxl')
        print(f"💾 Data tersimpan di {filename}")


# ========== FUNGSI UTAMA ==========

async def main():
    """Contoh penggunaan scraper"""
    
    # Inisialisasi scraper
    async with GoogleMapsPlaywrightScraper(headless=False, use_stealth=True) as scraper:
        
        # Contoh 1: Scrape semua masjid di Indonesia
        print("\n" + "="*60)
        print("CONTOH 1: Mencari Masjid di Seluruh Indonesia")
        print("="*60)
        
        masjid_data = await scraper.search_by_keyword_with_filter(
            keyword="masjid",
            filter_level="nasional",
            max_results=50
        )
        
        scraper.save_to_excel(masjid_data, "hasil_masjid_indonesia.xlsx")
        
        # Contoh 2: Scrape toko sembako di DKI Jakarta
        print("\n" + "="*60)
        print("CONTOH 2: Mencari Toko Sembako di DKI Jakarta")
        print("="*60)
        
        sembako_data = await scraper.search_by_keyword_with_filter(
            keyword="toko sembako",
            filter_level="provinsi",
            filter_value="DKI Jakarta",
            max_results=30
        )
        
        scraper.save_to_csv(sembako_data, "toko_sembako_jakarta.csv")
        
        # Contoh 3: Scrape restoran di Surabaya
        print("\n" + "="*60)
        print("CONTOH 3: Mencari Restoran di Surabaya")
        print("="*60)
        
        restoran_data = await scraper.search_by_keyword_with_filter(
            keyword="restoran",
            filter_level="kota",
            filter_value="Surabaya",
            max_results=40
        )
        
        scraper.save_to_json(restoran_data, "restoran_surabaya.json")
        
        # Tampilkan statistik
        print("\n" + "="*60)
        print("📊 STATISTIK SCRAPING")
        print("="*60)
        print(f"Total Masjid Indonesia : {len(masjid_data)}")
        print(f"Total Toko Sembako Jakarta : {len(sembako_data)}")
        print(f"Total Restoran Surabaya : {len(restoran_data)}")


if __name__ == "__main__":
    asyncio.run(main())
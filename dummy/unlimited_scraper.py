"""
Unlimited Google Maps Scraper
Bypass limit 120 hasil dengan multiple granular queries
"""

import asyncio
import json
from typing import List, Dict
from playwright_maps_scraper import GoogleMapsPlaywrightScraper, PlaceData


class UnlimitedGoogleMapsScraper:
    """
    Scraper yang bisa mengambil UNLIMITED data dengan strategi:
    1. Granular queries per kota/kecamatan
    2. Multiple keyword variations
    3. Pagination via coordinate grid
    """
    
    # Daftar kota besar Indonesia untuk granular search
    MAJOR_CITIES = [
        "Jakarta", "Surabaya", "Bandung", "Medan", "Semarang",
        "Denpasar", "Makassar", "Palembang", "Yogyakarta", "Malang",
        "Bekasi", "Depok", "Tangerang", "Bogor", "Solo"
    ]
    
    def __init__(self, headless: bool = False):
        self.headless = headless
        self.scraper = None
    
    async def scrape_unlimited(self, keyword: str, scope: str = "nasional",
                               location: str = "") -> List[PlaceData]:
        """
        Scrape unlimited data dengan granular approach
        
        Args:
            keyword: Keyword pencarian
            scope: 'nasional', 'provinsi', 'kota'
            location: Nama lokasi spesifik
        """
        all_results = []
        
        if scope == "nasional":
            # Scrape per kota besar
            print(f"🌍 Scrape nasional: {keyword} di {len(self.MAJOR_CITIES)} kota")
            for city in self.MAJOR_CITIES:
                print(f"\n📍 Mencari di {city}...")
                results = await self._scrape_city(keyword, city)
                all_results.extend(results)
                await asyncio.sleep(3)  # Delay antar kota
        
        elif scope == "provinsi" and location:
            # Dapatkan semua kota dalam provinsi
            cities_in_province = await self._get_cities_in_province(location)
            for city in cities_in_province:
                results = await self._scrape_city(keyword, city)
                all_results.extend(results)
                await asyncio.sleep(2)
        
        elif scope == "kota" and location:
            # Scrape satu kota dengan multiple sub-area
            results = await self._scrape_city_deep(keyword, location)
            all_results.extend(results)
        
        # Remove duplicates berdasarkan nama
        unique_results = self._deduplicate(all_results)
        print(f"\n✅ Total unique results: {len(unique_results)} dari {len(all_results)}")
        
        return unique_results
    
    async def _scrape_city(self, keyword: str, city: str) -> List[PlaceData]:
        """Scrape untuk satu kota"""
        async with GoogleMapsPlaywrightScraper(headless=self.headless) as scraper:
            results = await scraper.search_by_keyword_with_filter(
                keyword=keyword,
                filter_level="kota",
                filter_value=city,
                max_results=100
            )
            return results
    
    async def _scrape_city_deep(self, keyword: str, city: str) -> List[PlaceData]:
        """Scrape deep untuk satu kota dengan multiple area"""
        all_results = []
        
        # Area/kecamatan dalam kota (contoh untuk Jakarta)
        areas = await self._get_areas_in_city(city)
        
        for area in areas:
            print(f"  🔍 Sub-area: {area}")
            async with GoogleMapsPlaywrightScraper(headless=self.headless) as scraper:
                query = f"{keyword} {area} {city}"
                results = await scraper.search(query, max_results=50)
                all_results.extend(results)
            await asyncio.sleep(2)
        
        return all_results
    
    def _deduplicate(self, places: List[PlaceData]) -> List[PlaceData]:
        """Hapus duplikat berdasarkan nama"""
        seen = set()
        unique = []
        for place in places:
            if place.name not in seen:
                seen.add(place.name)
                unique.append(place)
        return unique
    
    async def _get_cities_in_province(self, province: str) -> List[str]:
        """Dapatkan daftar kota dalam provinsi (simplifikasi)"""
        # Ini bisa diperluas dengan data dari API eksternal
        province_cities = {
            "DKI Jakarta": ["Jakarta Pusat", "Jakarta Barat", "Jakarta Timur", 
                           "Jakarta Selatan", "Jakarta Utara", "Kepulauan Seribu"],
            "Jawa Barat": ["Bandung", "Bekasi", "Depok", "Bogor", "Cimahi", 
                          "Sukabumi", "Cirebon", "Tasikmalaya"],
            "Jawa Timur": ["Surabaya", "Malang", "Kediri", "Blitar", "Madiun", 
                          "Probolinggo", "Pasuruan", "Mojokerto"],
        }
        return province_cities.get(province, [province])
    
    async def _get_areas_in_city(self, city: str) -> List[str]:
        """Dapatkan daftar area/kecamatan dalam kota"""
        # Contoh untuk Jakarta
        if "Jakarta" in city:
            return ["Gambir", "Menteng", "Senayan", "Kemang", "Pondok Indah",
                   "Kelapa Gading", "Sunter", "Cilincing", "Cakung", "Pasar Rebo"]
        elif "Surabaya" in city:
            return ["Surabaya Pusat", "Surabaya Barat", "Surabaya Timur", 
                   "Surabaya Selatan", "Surabaya Utara"]
        else:
            return [city]  # Default: search tanpa sub-area


# Contoh penggunaan unlimited scraper
async def run_unlimited():
    scraper = UnlimitedGoogleMapsScraper(headless=False)
    
    # Scrape unlimited toko sembako di seluruh Indonesia
    results = await scraper.scrape_unlimited(
        keyword="toko sembako",
        scope="nasional"
    )
    
    # Simpan hasil
    async with GoogleMapsPlaywrightScraper() as s:
        s.save_to_excel(results, "toko_sembako_unlimited.xlsx")
        print(f"Total data terkumpul: {len(results)}")


if __name__ == "__main__":
    asyncio.run(run_unlimited())
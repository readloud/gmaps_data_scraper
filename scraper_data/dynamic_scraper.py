"""
Dynamic Google Maps Scraper - Fixed Version with Headless Mode
"""

import asyncio
import json
import re
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict, field

import pandas as pd
from playwright.async_api import async_playwright


@dataclass
class DynamicPlaceData:
    """Data class untuk tempat yang di-scrape"""
    name: str = ""
    keyword_used: str = ""
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
    scraped_at: str = ""
    raw_data: Dict = field(default_factory=dict)
    
    def to_dict(self):
        return {k: v for k, v in asdict(self).items() if k != 'raw_data'}


class DynamicGoogleMapsScraper:
    """
    Dynamic Scraper - Fixed to run in headless mode for servers
    """
    
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
    
    def __init__(self, headless: bool = True, max_results: int = 50):
        self.headless = True  # Always headless for server compatibility
        self.max_results = max_results
        self.scroll_count = 5
        self.delay_between_scroll = 2
        self.playwright = None
        self.browser = None
        self.page = None
        
    async def __aenter__(self):
        await self._start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._close()
    
    async def _start(self):
        """Start browser with headless mode enabled"""
        self.playwright = await async_playwright().start()
        
        # Launch with headless=True for server compatibility
        self.browser = await self.playwright.chromium.launch(
            headless=True,  # Always headless
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-features=IsolateOrigins,site-per-process',
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--disable-setuid-sandbox',
                '--no-first-run',
                '--no-zygote',
                '--single-process',
                '--disable-web-security',
            ]
        )
        
        context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='id-ID',
            timezone_id='Asia/Jakarta'
        )
        
        self.page = await context.new_page()
        
        await self.page.set_extra_http_headers({
            'Accept-Language': 'id-ID,id;q=0.9,en;q=0.8',
        })
        
        print(f"✅ Browser ready (Headless Mode enabled for server compatibility)")
    
    async def _close(self):
        """Tutup semua resource"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        print("🔒 Browser closed")
    
    async def scrape(self, keyword: str, location: str = "Indonesia", 
                     filter_level: str = "nasional", filter_value: str = "") -> List[DynamicPlaceData]:
        """Main scraping method"""
        print(f"\n{'='*60}")
        print(f"🔍 DYNAMIC SEARCH: '{keyword}'")
        print(f"{'='*60}")
        
        # Build search query
        if filter_level == "provinsi" and filter_value:
            search_query = f"{keyword} {filter_value}"
        elif filter_level == "kota" and filter_value:
            search_query = f"{keyword} {filter_value}"
        else:
            search_query = f"{keyword} {location}"
        
        search_url = f"https://www.google.com/maps/search/{search_query.replace(' ', '+')}"
        print(f"🌐 URL: {search_url}")
        
        try:
            await self.page.goto(search_url, wait_until='domcontentloaded', timeout=30000)
            await asyncio.sleep(5)
            
            await self._scroll_results()
            
            places_data = await self._extract_places_via_click()
            
            for place in places_data:
                place.province, place.city, place.district, place.postal_code = \
                    self._parse_address(place.address)
                place.scraped_at = datetime.now().isoformat()
                place.keyword_used = keyword
            
            print(f"\n✅ SCRAPING COMPLETE: {len(places_data)} results for '{keyword}'")
            return places_data[:self.max_results]
            
        except Exception as e:
            print(f"❌ Error during scraping: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    async def _scroll_results(self):
        """Scroll halaman untuk memuat lebih banyak hasil"""
        try:
            scroll_selectors = [
                'div[role="feed"]',
                'div.m6QErb',
                'div.DxyBCb',
            ]
            
            scrollable = None
            for selector in scroll_selectors:
                scrollable = await self.page.query_selector(selector)
                if scrollable:
                    print(f"Found scrollable panel: {selector}")
                    break
            
            if not scrollable:
                print("⚠️ Scrollable panel not found")
                return
            
            for i in range(self.scroll_count):
                try:
                    await self.page.evaluate('''
                        (element) => {
                            element.scrollTop = element.scrollHeight;
                        }
                    ''', scrollable)
                    await asyncio.sleep(self.delay_between_scroll)
                    print(f"📜 Scrolled {i+1}/{self.scroll_count}")
                except Exception as e:
                    print(f"Scroll error: {e}")
                    break
                    
        except Exception as e:
            print(f"⚠️ Scroll warning: {e}")
    
    async def _extract_places_via_click(self) -> List[DynamicPlaceData]:
        """Extract places by clicking each result"""
        places = []
        
        try:
            await self.page.wait_for_selector('a[href*="/maps/place/"]', timeout=15000)
            
            place_links = await self.page.query_selector_all('a[href*="/maps/place/"]')
            print(f"📊 Found {len(place_links)} place links")
            
            # Debug first few links
            for i, link in enumerate(place_links[:5]):
                text = await link.text_content()
                print(f"  Link {i+1} text: '{text[:50] if text else 'None'}'")
            
            unique_places = []
            seen_names = set()
            
            for link in place_links:
                name = await self._extract_name_from_link(link)
                
                if name and name not in seen_names and len(name) > 2 and len(name) < 100:
                    seen_names.add(name)
                    
                    rating, reviews = await self._extract_rating_from_parent(link)
                    
                    unique_places.append({
                        'name': name,
                        'rating': rating,
                        'reviews': reviews,
                        'element': link
                    })
            
            print(f"📊 Found {len(unique_places)} unique places")
            
            # If still 0, try sidebar extraction
            if len(unique_places) == 0:
                print("⚠️ Trying alternative extraction method...")
                unique_places = await self._extract_from_sidebar()
            
            # Get details for each place
            for idx, place_info in enumerate(unique_places[:self.max_results]):
                print(f"📋 [{idx+1}/{min(len(unique_places), self.max_results)}] Processing: {place_info['name'][:40]}...")
                
                try:
                    await place_info['element'].click()
                    await asyncio.sleep(2)
                    
                    place = await self._extract_detail_from_panel(place_info)
                    places.append(place)
                    
                except Exception as e:
                    print(f"⚠️ Error getting detail for {place_info['name']}: {e}")
                    places.append(DynamicPlaceData(
                        name=place_info['name'],
                        rating=place_info['rating'],
                        reviews_count=place_info['reviews']
                    ))
                
                await asyncio.sleep(1)
            
            return places
            
        except Exception as e:
            print(f"❌ Error extracting places: {e}")
            return []
    
    async def _extract_name_from_link(self, link) -> str:
        """Extract name from a place link"""
        name_selectors = [
            '[role="heading"]',
            '.fontHeadlineSmall',
            'h3',
            '.qBF1w',
            '.DUwDvf',
            'span:first-child'
        ]
        
        for selector in name_selectors:
            name_elem = await link.query_selector(selector)
            if name_elem:
                name = (await name_elem.text_content()) or ""
                if name and len(name) > 2:
                    return name.strip()
        
        # Fallback to text content
        text = await link.text_content()
        return text.strip() if text else ""
    
    async def _extract_rating_from_parent(self, link) -> Tuple[float, int]:
        """Extract rating from parent element"""
        rating = 0
        reviews = 0
        
        parent = await link.query_selector('xpath=..')
        if parent:
            parent_text = await parent.text_content()
            if parent_text:
                match = re.search(r'([\d,]+)\.?\s*\((\d+)\)', parent_text)
                if match:
                    rating = float(match.group(1).replace(',', '.'))
                    reviews = int(match.group(2))
        
        return rating, reviews
    
    async def _extract_from_sidebar(self) -> List[Dict]:
        """Extract from sidebar as fallback"""
        places = []
        
        try:
            sidebar_selectors = [
                'div[role="feed"] > div',
                'div[jsaction*="pane"] > div',
                '.Nv2PK',
                '.THOPZb'
            ]
            
            for selector in sidebar_selectors:
                items = await self.page.query_selector_all(selector)
                if items:
                    print(f"  Found {len(items)} items with selector: {selector}")
                    
                    for item in items[:self.max_results]:
                        try:
                            name = ""
                            name_selectors = ['h3', '.fontHeadlineSmall', '[role="heading"]']
                            for ns in name_selectors:
                                name_elem = await item.query_selector(ns)
                                if name_elem:
                                    name = (await name_elem.text_content()) or ""
                                    if name:
                                        break
                            
                            if not name or len(name) < 3:
                                continue
                            
                            rating = 0
                            reviews = 0
                            text = await item.text_content()
                            if text:
                                match = re.search(r'([\d,]+)\.?\s*\((\d+)\)', text)
                                if match:
                                    rating = float(match.group(1).replace(',', '.'))
                                    reviews = int(match.group(2))
                            
                            link_elem = await item.query_selector('a')
                            if not link_elem:
                                link_elem = item
                            
                            places.append({
                                'name': name,
                                'rating': rating,
                                'reviews': reviews,
                                'element': link_elem
                            })
                            
                        except Exception as e:
                            continue
                    
                    if places:
                        break
            
            return places
            
        except Exception as e:
            print(f"⚠️ Sidebar extraction error: {e}")
            return []
    
    async def _extract_detail_from_panel(self, place_info: Dict) -> DynamicPlaceData:
        """Extract details from panel after click"""
        
        place = DynamicPlaceData(
            name=place_info['name'],
            rating=place_info['rating'],
            reviews_count=place_info['reviews']
        )
        
        try:
            await self.page.wait_for_selector('[role="main"], .m6QErb', timeout=5000)
            await asyncio.sleep(1)
            
            # Extract address
            address_selectors = [
                'button[data-tooltip="Salin alamat"] span',
                'button[aria-label*="Alamat"] span',
                'div[data-attrid*="address"]',
                '[aria-label*="Alamat"]',
            ]
            
            for selector in address_selectors:
                try:
                    addr_elem = await self.page.query_selector(selector)
                    if addr_elem:
                        place.address = (await addr_elem.text_content()) or ""
                        if place.address and len(place.address) > 5:
                            print(f"  📍 Address: {place.address[:50]}")
                            break
                except:
                    continue
            
            # Extract phone
            phone_selectors = [
                'button[data-tooltip="Salin nomor telepon"] span',
                'button[aria-label*="Telepon"] span',
                'a[href^="tel:"]',
            ]
            
            for selector in phone_selectors:
                try:
                    phone_elem = await self.page.query_selector(selector)
                    if phone_elem:
                        if selector.startswith('a['):
                            place.phone = await phone_elem.get_attribute('href')
                            if place.phone:
                                place.phone = place.phone.replace('tel:', '')
                        else:
                            place.phone = (await phone_elem.text_content()) or ""
                        if place.phone:
                            print(f"  📞 Phone: {place.phone}")
                            break
                except:
                    continue
            
            # Extract website
            web_selectors = [
                'a[data-tooltip="Buka situs web"]',
                'a[aria-label*="Website"]',
            ]
            
            for selector in web_selectors:
                try:
                    web_elem = await self.page.query_selector(selector)
                    if web_elem:
                        href = await web_elem.get_attribute('href')
                        if href and 'google.com' not in href:
                            place.website = href
                            print(f"  🌐 Website: {href[:50]}")
                            break
                except:
                    continue
            
            # Extract category
            cat_selectors = [
                'button[jsaction*="category"]',
                'button[aria-label*="Kategori"]',
            ]
            
            for selector in cat_selectors:
                try:
                    cat_elem = await self.page.query_selector(selector)
                    if cat_elem:
                        place.category = (await cat_elem.text_content()) or ""
                        if place.category:
                            print(f"  📁 Category: {place.category}")
                            break
                except:
                    continue
            
            # Extract coordinates
            current_url = self.page.url
            lat, lng = self._extract_coordinates(current_url)
            if lat and lng:
                place.latitude = lat
                place.longitude = lng
                print(f"  🗺️ Coordinates: {lat}, {lng}")
            
        except Exception as e:
            print(f"  Detail extraction error: {e}")
        
        return place
    
    def _extract_coordinates(self, url: str) -> Tuple[Optional[float], Optional[float]]:
        """Extract coordinates from URL"""
        match = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', url)
        if match:
            return float(match.group(1)), float(match.group(2))
        return None, None
    
    def _parse_address(self, address: str) -> Tuple[str, str, str, str]:
        """Parse address for province, city, district, postal code"""
        province = ""
        city = ""
        district = ""
        postal_code = ""
        
        if not address:
            return province, city, district, postal_code
        
        address_lower = address.lower()
        
        for prov in self.INDONESIAN_PROVINCES:
            if prov.lower() in address_lower:
                province = prov
                break
        
        kec_match = re.search(r'kec(?:amatan)?\.?\s+([^,\d]+)', address_lower, re.IGNORECASE)
        if kec_match:
            district = kec_match.group(1).strip().title()
        
        parts = address.split(',')
        if province and len(parts) > 1:
            for i, part in enumerate(parts):
                if province.lower() in part.lower() and i > 0:
                    city = parts[i-1].strip()
                    break
        
        if not city:
            kota_match = re.search(r'(?:kota|kabupaten)\s+([^,]+)', address_lower, re.IGNORECASE)
            if kota_match:
                city = kota_match.group(1).strip().title()
        
        postal_match = re.search(r'\b(\d{5})\b', address)
        if postal_match:
            postal_code = postal_match.group(1)
        
        return province, city, district, postal_code
    
    def to_dataframe(self, data: List[DynamicPlaceData]) -> pd.DataFrame:
        return pd.DataFrame([p.to_dict() for p in data])
    
    def save_to_json(self, data: List[DynamicPlaceData], filename: str):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump([p.to_dict() for p in data], f, indent=2, ensure_ascii=False)
        print(f"💾 Saved to {filename}")
    
    def save_to_csv(self, data: List[DynamicPlaceData], filename: str):
        df = self.to_dataframe(data)
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"💾 Saved to {filename}")
    
    def save_to_excel(self, data: List[DynamicPlaceData], filename: str):
        df = self.to_dataframe(data)
        df.to_excel(filename, index=False, engine='openpyxl')
        print(f"💾 Saved to {filename}")

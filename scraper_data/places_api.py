"""
Google Places API Wrapper untuk Django
"""

import os
import googlemaps
from typing import List, Dict, Optional
from dataclasses import dataclass
from django.conf import settings


@dataclass
class PlaceData:
    """Data class untuk hasil dari Google Places API"""
    place_id: str = ""
    name: str = ""
    address: str = ""
    phone: str = ""
    website: str = ""
    rating: float = 0.0
    reviews_count: int = 0
    latitude: float = None
    longitude: float = None
    types: List[str] = None
    price_level: int = 0
    opening_hours: str = ""
    keyword_used: str = ""
    
    def to_dict(self):
        return {
            'place_id': self.place_id,
            'name': self.name,
            'address': self.address,
            'phone': self.phone,
            'website': self.website,
            'rating': self.rating,
            'reviews_count': self.reviews_count,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'types': ', '.join(self.types) if self.types else '',
            'price_level': self.price_level,
            'keyword_used': self.keyword_used
        }


class GooglePlacesAPIClient:
    """
    Wrapper untuk Google Places API
    """
    
    def __init__(self, api_key: str = None):
        """Initialize Google Places API client"""
        self.api_key = api_key or settings.GOOGLE_MAPS_API_KEY
        self.client = googlemaps.Client(key=self.api_key)
        
    def search_by_text(self, query: str, location_bias: str = None, 
                       max_results: int = 20) -> List[PlaceData]:
        """
        Text Search - Mencari tempat berdasarkan query teks
        
        Args:
            query: Keyword pencarian (contoh: "klinik kecantikan Karawang")
            location_bias: Lokasi preferensi ("Jakarta", dll)
            max_results: Maksimal hasil (max 20 per request)
        
        Returns:
            List of PlaceData objects
        """
        print(f"🔍 Searching Google Places API: '{query}'")
        
        # Build search parameters
        params = {
            'query': query,
            'max_results': min(max_results, 20)  # API max 20 per request
        }
        
        # Add location bias if specified
        if location_bias:
            params['location_bias'] = f'circle:10000@{location_bias}'
        
        # Execute search
        results = self.client.places(**params)
        
        places = []
        for place_data in results.get('results', []):
            place = self._parse_place_result(place_data, query)
            places.append(place)
        
        print(f"✅ Found {len(places)} places")
        return places
    
    def get_place_details(self, place_id: str, 
                          fields: List[str] = None) -> Optional[PlaceData]:
        """
        Get detailed information for a specific place
        
        Args:
            place_id: Google Place ID
            fields: List of fields to return (None = all basic fields)
        
        Returns:
            PlaceData with detailed information
        """
        if not fields:
            fields = [
                'place_id', 'name', 'formatted_address', 'formatted_phone_number',
                'website', 'rating', 'user_ratings_total', 'geometry',
                'types', 'price_level', 'opening_hours'
            ]
        
        try:
            result = self.client.place(place_id=place_id, fields=fields)
            place_data = result.get('result', {})
            return self._parse_place_result(place_data)
        except Exception as e:
            print(f"Error getting place details: {e}")
            return None
    
    def search_by_category(self, category: str, location: str, 
                           radius: int = 5000, max_results: int = 20) -> List[PlaceData]:
        """
        Nearby Search - Mencari tempat berdasarkan kategori di lokasi tertentu
        
        Args:
            category: Kategori (contoh: "mosque", "beauty_salon")
            location: Lokasi ("-6.2088,106.8456" atau "Jakarta")
            radius: Radius pencarian dalam meter
            max_results: Maksimal hasil
        """
        print(f"📍 Searching nearby: '{category}' near '{location}'")
        
        # Convert location name to coordinates if needed
        if not location.replace('-', '').replace('.', '').isdigit():
            geocode_result = self.client.geocode(location)
            if geocode_result:
                lat = geocode_result[0]['geometry']['location']['lat']
                lng = geocode_result[0]['geometry']['location']['lng']
                location = f"{lat},{lng}"
        
        # Execute nearby search
        results = self.client.places_nearby(
            location=location,
            radius=radius,
            type=category,
            max_results=min(max_results, 20)
        )
        
        places = []
        for place_data in results.get('results', []):
            place = self._parse_place_result(place_data)
            places.append(place)
        
        print(f"✅ Found {len(places)} places")
        return places
    
    def _parse_place_result(self, place_data: Dict, keyword: str = "") -> PlaceData:
        """Parse raw API response to PlaceData object"""
        
        # Get coordinates
        geometry = place_data.get('geometry', {})
        location = geometry.get('location', {})
        
        # Get opening hours as string
        opening_hours = ""
        hours_data = place_data.get('opening_hours', {})
        if hours_data:
            if 'weekday_text' in hours_data:
                opening_hours = '; '.join(hours_data['weekday_text'][:3])
            elif 'open_now' in hours_data:
                opening_hours = "Buka" if hours_data['open_now'] else "Tutup"
        
        return PlaceData(
            place_id=place_data.get('place_id', ''),
            name=place_data.get('name', ''),
            address=place_data.get('formatted_address', place_data.get('vicinity', '')),
            phone=place_data.get('formatted_phone_number', ''),
            website=place_data.get('website', ''),
            rating=place_data.get('rating', 0.0),
            reviews_count=place_data.get('user_ratings_total', 0),
            latitude=location.get('lat'),
            longitude=location.get('lng'),
            types=place_data.get('types', []),
            price_level=place_data.get('price_level', 0),
            opening_hours=opening_hours,
            keyword_used=keyword
        )
    
    def search_multiple_pages(self, query: str, max_results: int = 100) -> List[PlaceData]:
        """
        Search dengan pagination untuk mendapatkan lebih dari 20 hasil
        
        Args:
            query: Keyword pencarian
            max_results: Total maksimal hasil yang diinginkan (max 60 dengan free tier)
        """
        all_places = []
        next_page_token = None
        
        while len(all_places) < max_results:
            # Build parameters
            params = {'query': query, 'max_results': 20}
            if next_page_token:
                params['page_token'] = next_page_token
            
            # Execute search
            results = self.client.places(**params)
            
            # Parse results
            for place_data in results.get('results', []):
                place = self._parse_place_result(place_data, query)
                all_places.append(place)
            
            # Check for next page
            next_page_token = results.get('next_page_token')
            if not next_page_token:
                break
            
            # Delay required for next page token to become valid
            import time
            time.sleep(2)
        
        print(f"✅ Total found: {len(all_places)} places from pagination")
        return all_places[:max_results]


# Django integration function
def scrape_with_places_api(keyword: str, location: str = "Indonesia", 
                           max_results: int = 20) -> List[PlaceData]:
    """
    Main function to scrape using Google Places API
    
    Args:
        keyword: Keyword pencarian (contoh: "klinik kecantikan")
        location: Lokasi (contoh: "Karawang" atau biarkan kosong)
        max_results: Maksimal hasil
    """
    api_key = settings.GOOGLE_MAPS_API_KEY
    client = GooglePlacesAPIClient(api_key)
    
    # Build search query
    if location and location.lower() != "indonesia":
        query = f"{keyword} {location}"
    else:
        query = keyword
    
    return client.search_by_text(query, max_results=max_results)
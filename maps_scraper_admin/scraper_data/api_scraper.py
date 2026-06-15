import googlemaps
from django.conf import settings
from .models import Place

def scrape_with_google_api(keyword, location, max_results=20):
    """
    Scrape menggunakan Google Places API resmi
    Data LENGKAP: alamat, telepon, rating, website, dll
    """
    gmaps = googlemaps.Client(key=settings.GOOGLE_MAPS_API_KEY)
    
    # Build query
    if location:
        query = f"{keyword} {location}"
    else:
        query = keyword
    
    # Search places
    places_result = gmaps.places(query, max_results=max_results)
    
    saved_count = 0
    for place in places_result.get('results', []):
        # Get place_id untuk detail lengkap
        place_id = place.get('place_id')
        
        # Get detail (termasuk telepon, website, dll)
        detail = gmaps.place(place_id, fields=[
            'name', 'formatted_address', 'formatted_phone_number',
            'website', 'rating', 'user_ratings_total', 
            'geometry', 'types', 'opening_hours'
        ])
        
        detail_result = detail.get('result', {})
        
        # Simpan ke database
        place_obj, created = Place.objects.update_or_create(
            place_id=place_id,
            defaults={
                'name': detail_result.get('name', ''),
                'keyword': keyword,
                'address': detail_result.get('formatted_address', ''),
                'phone': detail_result.get('formatted_phone_number', ''),
                'website': detail_result.get('website', ''),
                'rating': detail_result.get('rating', 0),
                'reviews_count': detail_result.get('user_ratings_total', 0),
                'latitude': detail_result.get('geometry', {}).get('location', {}).get('lat'),
                'longitude': detail_result.get('geometry', {}).get('location', {}).get('lng'),
                'is_active': True
            }
        )
        saved_count += 1
        print(f"✅ Saved: {place_obj.name}")
    
    return saved_count
# scraper_data/views.py
import asyncio
import json
import os
from datetime import datetime, timedelta
from io import BytesIO
from django.utils import timezone
from django.db.models import Count, Avg, Q
from django.shortcuts import render, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import HttpResponse, JsonResponse
from django.conf import settings
from .forms import DynamicScrapeForm
from .models import Place, ScrapingLog
from .models import ScraperConfig
from .dynamic_scraper import DynamicGoogleMapsScraper
import pandas as pd
from django.urls import re_path
from .places_api import scrape_with_places_api, GooglePlacesAPIClient

@staff_member_required
def scrape_with_api(request):
    """Scrape menggunakan Google Places API (resmi & stabil)"""
    
    if request.method == 'POST':
        keyword = request.POST.get('keyword')
        location = request.POST.get('location', '')
        max_results = int(request.POST.get('max_results', 20))
        
        try:
            # Panggil Google Places API
            results = scrape_with_places_api(keyword, location, max_results)
            
            # Simpan ke database
            saved_count = 0
            for place_data in results:
                place, created = Place.objects.update_or_create(
                    place_id=place_data.place_id,  # Tambahkan field place_id di model
                    defaults={
                        'name': place_data.name,
                        'keyword': keyword,
                        'address': place_data.address,
                        'phone': place_data.phone,
                        'website': place_data.website,
                        'rating': place_data.rating,
                        'reviews_count': place_data.reviews_count,
                        'latitude': place_data.latitude,
                        'longitude': place_data.longitude,
                        'is_active': True
                    }
                )
                saved_count += 1
            
            messages.success(request, f"✅ API scraping berhasil! {saved_count} data untuk '{keyword}'")
            
        except Exception as e:
            messages.error(request, f"❌ Error: {str(e)}")
        
        return redirect('scraper_data:dashboard')
    
    return render(request, 'scraper_data/api_scrape.html')

@staff_member_required
def admin_dashboard(request):
    """Dashboard utama admin"""
    
    # Total statistik
    total_places = Place.objects.filter(is_active=True).count()
    total_cities = Place.objects.filter(is_active=True).values('city').distinct().count()
    avg_rating = Place.objects.filter(rating__isnull=False).aggregate(Avg('rating'))['rating__avg'] or 0
    total_scrapes = ScrapingLog.objects.count()
    
    # Weekly growth
    week_ago = datetime.now() - timedelta(days=7)
    new_places_week = Place.objects.filter(scraped_date__gte=week_ago).count()
    weekly_growth = new_places_week
    
    # Last scrape
    last_scrape = ScrapingLog.objects.filter(status='completed').order_by('-completed_at').first()
    last_scrape_date = last_scrape.completed_at.strftime('%d %b %Y') if last_scrape else 'Belum ada'
    
    # Statistik per kategori
    category_stats = list(Place.objects.filter(is_active=True)
                         .values('category')
                         .annotate(total=Count('id'))
                         .order_by('-total'))
    
    # Statistik per provinsi
    province_stats = list(Place.objects.filter(is_active=True)
                         .exclude(province='')
                         .values('province')
                         .annotate(total=Count('id'))
                         .order_by('-total')[:10])
    
    # Aktivitas 7 hari terakhir
    activity_stats = []
    for i in range(7, 0, -1):
        date = datetime.now() - timedelta(days=i)
        date_start = date.replace(hour=0, minute=0, second=0)
        date_end = date.replace(hour=23, minute=59, second=59)
        count = ScrapingLog.objects.filter(started_at__range=(date_start, date_end)).count()
        activity_stats.append({
            'date': date.strftime('%d/%m'),
            'count': count
        })
    
    # Distribusi rating
    rating_distribution = []
    for rating in [5, 4, 3, 2, 1]:
        if rating > 1:
            count = Place.objects.filter(
                rating__gte=rating - 0.5,
                rating__lt=rating + 0.5,
                is_active=True
            ).count()
        else:
            count = Place.objects.filter(rating__lt=1.5, is_active=True).count()
        rating_distribution.append({
            'rating': rating,
            'count': count
        })
    
    # Top places
    top_places = Place.objects.filter(is_active=True, rating__isnull=False).order_by('-rating')[:15]
    
    # Recent logs
    recent_logs = ScrapingLog.objects.order_by('-started_at')[:10]
    
    # JSON untuk chart
    category_stats_json = json.dumps(list(category_stats))
    province_stats_json = json.dumps(list(province_stats))
    activity_stats_json = json.dumps(activity_stats)
    rating_distribution_json = json.dumps(rating_distribution)
    
    context = {
        'total_places': total_places,
        'total_cities': total_cities,
        'avg_rating': round(avg_rating, 1),
        'total_scrapes': total_scrapes,
        'weekly_growth': weekly_growth,
        'last_scrape_date': last_scrape_date,
        'category_stats': category_stats,
        'province_stats': province_stats[:5],
        'activity_stats': activity_stats,
        'rating_distribution': rating_distribution,
        'top_places': top_places,
        'recent_logs': recent_logs,
        'category_stats_json': category_stats_json,
        'province_stats_json': province_stats_json,
        'activity_stats_json': activity_stats_json,
        'rating_distribution_json': rating_distribution_json,
    }
    
    return render(request, 'admin/dashboard.html', context)
        

@staff_member_required
def dynamic_scrape_view(request):
    """Halaman untuk scraping dinamis"""
    if request.method == 'POST':
        form = DynamicScrapeForm(request.POST)
        if form.is_valid():
            keyword = form.cleaned_data['keyword']
            filter_level = form.cleaned_data['filter_level']
            filter_value = form.cleaned_data.get('filter_value', '')
            max_results = form.cleaned_data['max_results']
            
            # Jika filter level nasional atau value kosong, gunakan 'none'
            if filter_level == 'nasional' or not filter_value:
                filter_value = 'none'
            
            # Simpan ke session
            request.session['last_scrape'] = {
                'keyword': keyword,
                'filter_level': filter_level,
                'filter_value': filter_value,
                'max_results': max_results,
                'timestamp': datetime.now().isoformat()
            }
            
            # Redirect ke scrape_results
            return redirect('scraper_data:scrape_results', 
                           keyword=keyword,
                           level=filter_level,
                           value=filter_value,
                           max=max_results)
    else:
        form = DynamicScrapeForm()
    
    # Get recent keywords
    recent_keywords = list(Place.objects.exclude(keyword='')
                          .values_list('keyword', flat=True)
                          .distinct()[:10])
    
    return render(request, 'scraper_data/dynamic_scrape.html', {
        'form': form,
        'recent_keywords': recent_keywords,
    })

@staff_member_required
def scrape_results(request, keyword, level, value='', max=50):
    """Execute scraping dengan browser VISIBLE MODE"""
    
    config = ScraperConfig.get_config()
    
    log = ScrapingLog.objects.create(
        keyword=f"{keyword} - {level}:{value}" if value else keyword,
        status='running'
    )
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def run_scraper():
            # headless = False (selalu visible)
            async with DynamicGoogleMapsScraper(
                headless=False,  # ← SELALU FALSE
                max_results=int(max) if max else config.default_max_results
            ) as scraper:
                scraper.scroll_count = config.scroll_count
                scraper.delay_between_scroll = config.delay_between_scroll
                
                results = await scraper.scrape(
                    keyword=keyword,
                    filter_level=level,
                    filter_value=value
                )
                return results
        
        results = loop.run_until_complete(run_scraper())
        loop.close()
        
        # Simpan ke database
        saved_count = 0
        for place_data in results:
            print(f"Saving: {place_data.name}")
            print(f"  - Address: {place_data.address}")
            print(f"  - Rating: {place_data.rating}")
            print(f"  - Phone: {place_data.phone}")
            
            place, created = Place.objects.update_or_create(
                name=place_data.name,
                defaults={
                    'keyword': keyword,
                    'category': place_data.category if place_data.category else '',
                    'address': place_data.address,  # Pastikan ini terisi
                    'province': place_data.province if place_data.province else '',
                    'city': place_data.city if place_data.city else '',
                    'district': place_data.district if place_data.district else '',
                    'postal_code': place_data.postal_code if place_data.postal_code else '',
                    'phone': place_data.phone if place_data.phone else '',
                    'website': place_data.website if place_data.website else '',
                    'rating': place_data.rating if place_data.rating > 0 else None,
                    'reviews_count': place_data.reviews_count if place_data.reviews_count > 0 else 0,
                    'latitude': place_data.latitude,
                    'longitude': place_data.longitude,
                    'is_active': True
                }
            )
            saved_count += 1
            print(f"  - Saved: {created and 'NEW' or 'UPDATED'}")
        
        # Update log
        log.total_found = len(results)
        log.total_saved = saved_count
        log.status = 'completed'
        log.completed_at = datetime.now()
        log.save()
        
        messages.success(request, f"✅ Berhasil scrape {saved_count} data untuk '{keyword}'")
        
        # Pagination
        paginator = Paginator(results, 25)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
        
        return render(request, 'scraper_data/results.html', {
            'results': page_obj,
            'keyword': keyword,
            'filter_level': level,
            'filter_value': value if value else 'Semua',
            'total_count': len(results),
            'export_url': f"/scraper/scrape/export/{keyword}/"
        })
        
    except Exception as e:
        log.status = 'failed'
        log.error_message = str(e)
        log.save()
        messages.error(request, f"❌ Gagal scraping: {str(e)}")
        return redirect('scraper_data:dynamic_scrape')


@staff_member_required
def scrape_results_novalue(request, keyword, level, max):
    """Wrapper untuk scrape_results dengan value kosong"""
    return scrape_results(request, keyword, level, 'none', max)

@staff_member_required
def export_scrape_results(request, keyword):
    """Export hasil scraping ke Excel dengan format yang benar"""
    from django.http import HttpResponse
    import pandas as pd
    from io import BytesIO
    
    # Ambil data berdasarkan keyword
    places = Place.objects.filter(keyword=keyword, is_active=True)
    
    if not places.exists():
        messages.error(request, f"Tidak ada data untuk keyword '{keyword}'")
        return redirect('scraper_data:dynamic_scrape')
    
    # Prepare data untuk Excel
    data = []
    for place in places:
        # Debug print
        print(f"Exporting: {place.name}")
        print(f"  Address: {place.address}")
        print(f"  Rating: {place.rating}")
        print(f"  Phone: {place.phone}")
        
        data.append({
            'Nama Tempat': place.name,
            'Kategori': place.get_category_display() if place.category else '-',
            'Alamat': place.address if place.address else '-',
            'Provinsi': place.province if place.province else '-',
            'Kota/Kabupaten': place.city if place.city else '-',
            'Kecamatan': place.district if place.district else '-',
            'Kode Pos': place.postal_code if place.postal_code else '-',
            'Telepon': place.phone if place.phone else '-',
            'Website': place.website if place.website else '-',
            'Rating': place.rating if place.rating else '-',
            'Jumlah Review': place.reviews_count if place.reviews_count else 0,
            'Latitude': place.latitude if place.latitude else '-',
            'Longitude': place.longitude if place.longitude else '-',
            'Tanggal Scrape': place.scraped_date.strftime('%Y-%m-%d %H:%M') if place.scraped_date else '-',
        })
    
    # Buat DataFrame
    df = pd.DataFrame(data)
    
    # Buat response Excel
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    filename = f"{keyword}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    # Write to Excel dengan formatting
    with BytesIO() as output:
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name=f'Hasil Scrape {keyword}', index=False)
            
            # Auto-adjust column widths
            worksheet = writer.sheets[f'Hasil Scrape {keyword}']
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
        
        response.write(output.getvalue())
    
    messages.success(request, f"✅ Berhasil export {len(data)} data ke {filename}")
    return response


@staff_member_required
def ajax_suggest_keyword(request):
    """Auto-suggest keyword berdasarkan history"""
    query = request.GET.get('q', '')
    if query:
        keywords = Place.objects.filter(
            keyword__icontains=query
        ).values_list('keyword', flat=True).distinct()[:10]
        return JsonResponse(list(keywords), safe=False)
    return JsonResponse([], safe=False)


@staff_member_required
def quick_stats_api(request):
    """API untuk quick stats di sidebar"""
    total_places = Place.objects.filter(is_active=True).count()
    total_scrapes = ScrapingLog.objects.count()
    avg_rating = Place.objects.filter(rating__isnull=False).aggregate(Avg('rating'))['rating__avg'] or 0
    
    return JsonResponse({
        'total_places': total_places,
        'total_scrapes': total_scrapes,
        'avg_rating': round(avg_rating, 1)
    })
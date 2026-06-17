# scraper_data/admin.py
from django.contrib import admin  # Add this import!
from django.urls import path, re_path
from django.shortcuts import redirect, render
from django.contrib import messages
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from import_export.admin import ImportExportModelAdmin
from .models import ScraperConfig, Place, ScrapingLog
import asyncio


@admin.register(Place)
class PlaceAdmin(ImportExportModelAdmin):
    """Admin untuk model Place"""
    
    list_display = ['name', 'category', 'city', 'province', 'rating', 'phone']
    list_filter = ['category', 'province', 'city', 'is_active']
    search_fields = ['name', 'address', 'phone', 'keyword']
    
    actions = []
 
    def scrape_manual_visible(self, request, queryset):
        """Paksa scraping dalam mode manual (browser terlihat)"""
        self.message_user(
            request,
            "👁️ Untuk scraping dengan browser, "
            "gunakan form scraping di halaman utama → Dynamic Scrape",
            level='WARNING'
        )
    scrape_manual_visible.short_description = "👁️ Scrape dengan browser (Manual)"


@admin.register(ScraperConfig)
class ScraperConfigAdmin(admin.ModelAdmin):
    """
    Admin panel untuk konfigurasi scraper
    """
    
    fieldsets = (
        ('⚙️ Pengaturan Scraping', {
            'fields': ('default_max_results', 'scroll_count', 'delay_between_scroll'),
            'description': """
            <div style="background: #f8f9fa; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
                <strong>💡 Informasi:</strong><br>
                • Browser akan selalu tampil (Visible Mode) untuk memastikan scraping berjalan optimal.<br>
                • Jika ingin scraping di background, gunakan server dengan display (Xvfb) atau Docker.<br>
            </div>
            """
        }),
    )
    
    list_display = ['id', 'default_max_results', 'scroll_count', 'updated_at']
    list_editable = ['default_max_results', 'scroll_count']
  
    def changelist_view(self, request, extra_context=None):
        """Override untuk menambahkan tombol test scrape"""
        extra_context = extra_context or {}
        extra_context['test_scrape_url'] = '/admin/scraper_data/test-scrape/'
        return super().changelist_view(request, extra_context=extra_context)
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('test-scrape/', self.test_scrape_view, name='test_scrape'),
        ]
        return custom_urls + urls
    
    def test_scrape_view(self, request):
        """View untuk test scraping"""
        if request.method == 'POST':
            config = ScraperConfig.get_config()
            keyword = request.POST.get('keyword', 'masjid')
            
            messages.info(request, f"🧪 Test scraping dengan browser VISIBLE MODE")
            
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                async def run_test():
                    # headless = False (selalu visible)
                    async with DynamicGoogleMapsScraper(
                        headless=False,  # ← SELALU FALSE
                        max_results=5
                    ) as scraper:
                        results = await scraper.scrape(
                            keyword=keyword,
                            filter_level="nasional"
                        )
                        return results
                
                results = loop.run_until_complete(run_test())
                loop.close()
                
                messages.success(request, f"✅ Test berhasil! Mendapatkan {len(results)} data untuk '{keyword}'")
                
            except Exception as e:
                messages.error(request, f"❌ Test gagal: {str(e)}")
            
            return redirect('/admin/scraper_data/scraperconfig/')
        
        return render(request, 'admin/test_scrape.html', {
            'config': ScraperConfig.get_config(),
            'title': 'Test Scraping Google Maps'
        })


@admin.register(ScrapingLog)
class ScrapingLogAdmin(admin.ModelAdmin):
    """Admin untuk log scraping"""
    
    list_display = ['keyword', 'total_found', 'total_saved', 'status', 'started_at']
    list_filter = ['status', 'started_at']
    readonly_fields = ['started_at', 'completed_at', 'error_message']
    search_fields = ['keyword', 'error_message']
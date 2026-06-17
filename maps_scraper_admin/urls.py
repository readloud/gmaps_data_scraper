# maps_scraper_admin/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect

urlpatterns = [
    # Django Admin
    path('admin/', admin.site.urls),
    
    # Root redirect to admin-dashboard
    path('', lambda request: redirect('/admin-dashboard/')),
    
    # Admin dashboard - using scraper_data.urls with namespace
    path('admin-dashboard/', include('scraper_data.urls', namespace='admin_dashboard')),
    
    # Scraper app - using scraper_data.urls with namespace
    path('scraper/', include('scraper_data.urls', namespace='scraper')),
]

# Serve static files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
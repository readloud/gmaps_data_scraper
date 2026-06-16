# maps_scraper_admin/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # 1. Single Root Redirect (Points cleanly to your dashboard app)
    path('', lambda request: redirect('scraper_data:dashboard')),  
    
    # 2. Main Dashboard Routes (Registered only ONCE to prevent namespace collisions)
    path('admin-dashboard/', include('scraper_data.urls')),  
]

# Serve static files in development AND production fallback if needed
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

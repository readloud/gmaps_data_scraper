# maps_scraper_admin/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Redirect root clean to scraper dashboard
    path('', lambda request: redirect('scraper_data:dashboard')),  
    
    # Change 'admin-dashboard/' to 'scraper/' so your old links work!
    path('scraper/', include('scraper_data.urls')),
]

# Serve static files in development AND production fallback if needed
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

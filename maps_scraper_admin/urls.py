# maps_scraper_admin/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', lambda request: redirect('/admin-dashboard/')),  # Redirect root ke dashboard
    path('', lambda request: redirect('scraper_data:dashboard')),  # Redirect ke dashboard
    path('admin-dashboard/', include('scraper_data.urls')),  # Dashboard di /admin-dashboard/
    path('scraper/', include('scraper_data.urls')),
]
# Serve static files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
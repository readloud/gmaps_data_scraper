# maps_scraper_admin/urls.py
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView  # ← TAMBAHKAN INI!
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', RedirectView.as_view(url='/admin-dashboard/', permanent=False)),
    path('admin-dashboard/', include('scraper_data.urls')),
]

# Serve static files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

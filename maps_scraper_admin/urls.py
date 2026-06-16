"""
URL configuration for maps_scraper_admin project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', RedirectView.as_view(url='/admin-dashboard/', permanent=False)),
    path('', lambda request: redirect('/admin-dashboard/')),  # Redirect root ke dashboard
    path('', lambda request: redirect('scraper_data:dashboard')),  # Redirect ke dashboard
    path('admin-dashboard/', include('scraper_data.urls')),  # Dashboard di /admin-dashboard/
    path('scraper/', include('scraper_data.urls')),
]

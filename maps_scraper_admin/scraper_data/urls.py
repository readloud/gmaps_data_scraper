# scraper_data/urls.py
from django.urls import path, re_path
from . import views

app_name = 'scraper_data'

urlpatterns = [
    # Dashboard home
    path('', views.admin_dashboard, name='dashboard'),
    
    # Dynamic Scrape Form
    path('scrape/', views.dynamic_scrape_view, name='dynamic_scrape'),
    
    # Scrape Results - pattern yang lebih fleksibel
    re_path(r'^scrape/results/(?P<keyword>[^/]+)/(?P<level>[^/]+)/(?P<value>[^/]*)/(?P<max>\d+)/$', 
            views.scrape_results, 
            name='scrape_results'),
    
    # Alternative pattern tanpa value
    re_path(r'^scrape/results/(?P<keyword>[^/]+)/(?P<level>[^/]+)/(?P<max>\d+)/$', 
            views.scrape_results, 
            {'value': ''}, 
            name='scrape_results_no_value'),
    
    # Export results
    path('scrape/export/<str:keyword>/', views.export_scrape_results, name='export_results'),
    
    # AJAX suggest keyword
    path('scrape/suggest/', views.ajax_suggest_keyword, name='suggest_keyword'),
    
    # API quick stats
    path('quick-stats/', views.quick_stats_api, name='quick_stats'),
]
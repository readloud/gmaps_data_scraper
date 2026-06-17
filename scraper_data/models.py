# scraper_data/models.py
from django.db import models
from django.utils import timezone

class Place(models.Model):
    """Model untuk menyimpan data tempat dari Google Maps"""
    
    CATEGORY_CHOICES = [
        ('masjid', 'Masjid'),
        ('toko_sembako', 'Toko Sembako'),
        ('restaurant', 'Restoran'),
        ('cafe', 'Cafe'),
        ('hotel', 'Hotel'),
        ('lainnya', 'Lainnya'),
    ]
    
    # Informasi dasar
    name = models.CharField(max_length=500, verbose_name="Nama Tempat")
    category = models.CharField(
        max_length=50, 
        choices=CATEGORY_CHOICES, 
        blank=True, 
        null=True,
        verbose_name="Kategori"
    )
    keyword = models.CharField(
        max_length=200, 
        blank=True,
        verbose_name="Keyword Pencarian",
        help_text="Keyword yang digunakan saat scraping"
    )
    
    # Alamat dan lokasi
    address = models.TextField(verbose_name="Alamat Lengkap", blank=True)
    province = models.CharField(
        max_length=100, 
        db_index=True, 
        blank=True,
        verbose_name="Provinsi"
    )
    city = models.CharField(
        max_length=100, 
        db_index=True, 
        blank=True,
        verbose_name="Kota/Kabupaten"
    )
    district = models.CharField(
        max_length=100, 
        blank=True,
        verbose_name="Kecamatan"
    )
    postal_code = models.CharField(
        max_length=10, 
        blank=True,
        verbose_name="Kode Pos"
    )
    
    # Kontak
    phone = models.CharField(
        max_length=50, 
        blank=True,
        verbose_name="Telepon"
    )
    website = models.URLField(
        blank=True,
        verbose_name="Website"
    )
    
    # Rating dan review
    rating = models.DecimalField(
        max_digits=3, 
        decimal_places=2, 
        blank=True, 
        null=True,
        verbose_name="Rating"
    )
    reviews_count = models.IntegerField(
        default=0,
        verbose_name="Jumlah Review"
    )
    
    # Koordinat
    latitude = models.DecimalField(
        max_digits=10, 
        decimal_places=7, 
        blank=True, 
        null=True,
        verbose_name="Latitude"
    )
    longitude = models.DecimalField(
        max_digits=10, 
        decimal_places=7, 
        blank=True, 
        null=True,
        verbose_name="Longitude"
    )
    place_id = models.CharField(
        max_length=255, 
        blank=True, 
        db_index=True,
        verbose_name="Google Place ID",
        help_text="Unique identifier from Google Places API"
    )
    
    # Metadata
    scraped_date = models.DateTimeField(
        default=timezone.now,
        verbose_name="Tanggal Scrape"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Terakhir Diupdate"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Aktif"
    )

    class Meta:
        ordering = ['-rating', 'name']
        verbose_name = "Tempat"
        verbose_name_plural = "Tempat-tempat"
        indexes = [
            models.Index(fields=['province', 'city']),
            models.Index(fields=['category', 'keyword']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.city if self.city else 'Lokasi tidak diketahui'}"
    
    def get_category_display(self):
        """Mendapatkan display name dari kategori"""
        return dict(self.CATEGORY_CHOICES).get(self.category, self.category or '-')


class ScrapingLog(models.Model):
    """Model untuk mencatat log scraping"""
    
    STATUS_CHOICES = [
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    keyword = models.CharField(max_length=200, verbose_name="Keyword")
    total_found = models.IntegerField(default=0, verbose_name="Total Ditemukan")
    total_saved = models.IntegerField(default=0, verbose_name="Total Tersimpan")
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='running',
        verbose_name="Status"
    )
    error_message = models.TextField(blank=True, verbose_name="Pesan Error")
    started_at = models.DateTimeField(auto_now_add=True, verbose_name="Mulai")
    completed_at = models.DateTimeField(blank=True, null=True, verbose_name="Selesai")
    
    class Meta:
        ordering = ['-started_at']
        verbose_name = "Log Scraping"
        verbose_name_plural = "Log Scraping"
    
    def __str__(self):
        return f"{self.keyword} - {self.status} - {self.started_at.strftime('%Y-%m-%d %H:%M')}"
    
    @property
    def duration(self):
        """Menghitung durasi scraping"""
        if self.completed_at and self.started_at:
            delta = self.completed_at - self.started_at
            return str(delta).split('.')[0]
        return "Masih berjalan"

class ScraperConfig(models.Model):
    """Model untuk konfigurasi scraper"""
    
    headless_mode = models.BooleanField(
        default=True,  # Default to True for server compatibility
        verbose_name="Headless Mode",
        help_text="Jalankan browser tanpa GUI (latar belakang)"
    )
    
    default_max_results = models.IntegerField(
        default=50,
        verbose_name="Maksimal Hasil Default",
        help_text="Jumlah default tempat yang diambil setiap scraping"
    )
    scroll_count = models.IntegerField(
        default=8,
        verbose_name="Jumlah Scroll",
        help_text="Berapa kali scroll untuk memuat lebih banyak hasil"
    )
    delay_between_scroll = models.FloatField(
        default=1.5,
        verbose_name="Delay Antar Scroll (detik)",
        help_text="Jeda antar scroll untuk menghindari block"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Terakhir Diupdate"
    )
    
    class Meta:
        verbose_name = "Konfigurasi Scraper"
        verbose_name_plural = "Konfigurasi Scraper"
    
    def __str__(self):
        mode = "Headless" if self.headless_mode else "Visible"
        return f"Konfigurasi Scraper - {mode}"
    
    @classmethod
    def get_config(cls):
        """Mendapatkan atau membuat konfigurasi default"""
        config, created = cls.objects.get_or_create(
            id=1,
            defaults={
                'headless_mode': True,  # Default to True
                'default_max_results': 50,
                'scroll_count': 8,
                'delay_between_scroll': 1.5
            }
        )
        return config

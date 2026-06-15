# Google Maps Scraper - Google Map API Integration

![screenshoot](dummy/screenshot/Screenshot (201).png)

```
# Buat virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# atau
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Install packages
pip install django django-import-export pandas openpyxl asyncio
pip install playwright playwright-stealth tf-playwright-stealth fake-useragent
pip install pkg-resources 
pip install whitenoise
pip install googlemaps

# Install Playwright browser
playwright install chromium
playwright install firefox  # Opsional, lebih stealth

# Buat project
django-admin startproject maps_scraper_admin

# Masuk ke project
cd maps_scraper_admin

# Buat app
python manage.py startapp scraper_data

#Set API Key

# Windows
set GOOGLE_MAPS_API_KEY=your_api_key_here

# Linux/Mac
export GOOGLE_MAPS_API_KEY=your_api_key_here

# Update Django Settings (maps_scraper_admin/settings.py)

# Google Maps API Key
GOOGLE_MAPS_API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY', 'your_api_key_here')

# Jalankan migrasi pertama
python manage.py makemigrations
python manage.py migrate

# Buat superuser
python manage.py createsuperuser

# Jalankan server
python manage.py runserver
```

# Akses Admin Panel

- ✅ Akses: http://127.0.0.1:8000/scraper/api-scrape/

# Akses Admin Panel (Debugging)

- ✅ Dashboard: http://127.0.0.1:8000/admin-dashboard/
- ✅ Dynamic Scrape: http://127.0.0.1:8000/scraper/scrape/
- ✅ Admin Panel: http://127.0.0.1:8000/admin/


# Test API di Terminal

python manage.py shell

>>from scraper_data.api_scraper import scrape_with_google_api

# Test untuk taman bermain di Karawang
>>result = scrape_with_google_api("taman bermain", "Karawang", 10)
>>print(f"Saved {result} places")

# Hasil dengan API
Untuk "THE NICE PLAYLAND KARAWANG", API akan menghasilkan:
```json
{
    "name": "THE NICE PLAYLAND KARAWANG",
    "address": "Jl. Alternatif Cikampek No.1, Karawang, Jawa Barat",
    "phone": "(0267) 123456",
    "rating": 4.5,
    "reviews_count": 234,
    "website": "https://niceplayland.com",
    "latitude": -6.1234,
    "longitude": 107.1234
}
```

**Fitur:**
- ✅ **Scrape otomatis** dari Google Maps
- ✅ **Filter data** berdasarkan provinsi/kota
- ✅ **Export** ke Excel/CSV
- ✅ **Dashboard** statistik
- ✅ **Log** riwayat scraping
- ✅ **Database Koordinat Kota** Mencakup 30+ kota besar di Indonesia dengan koordinat lengkap
- ✅ **Auto-location** Otomatis set lokasi berdasarkan filter kota/provinsi
- ✅ **Radius Search** Cari dalam radius tertentu (km) dari titik pusat
- ✅ **Distance Calculation** Hitung dan tampilkan jarak dari pusat kota
- ✅ **Geolocation Permission** Set permission browser untuk akses lokasi
- ✅ **Smart Filtering** Filter hasil berdasarkan radius

## ✅ Keunggulan Google Places API

1. **Data Akurat** - Langsung dari database Google
2. **Tidak Kena Block** - Resmi dan legal
3. **Rating & Review** - Data rating dan jumlah review akurat
4. **Foto** - Bisa akses foto tempat
5. **Jam Operasional** - Data jam buka/tutup
6. **Koordinat GPS** - Akurat untuk mapping

## ⚠️ Catatan Penting

1. **API Key Wajib Dibatasi (Restrict)** - Untuk keamanan 
2. **Gunakan Field Mask** - Hanya ambil data yang diperlukan untuk menghemat biaya 
3. **Cache Hasil** - Simpan ke database untuk menghindari request berulang
---

## 📊 HASIL YANG DIDAPAT

Data yang akan tersimpan di database:

| Field | Deskripsi |
|-------|-----------|
| name | Nama tempat (Masjid Istiqlal, dll) |
| rating | Rating Google Maps (1-5) |
| reviews_count | Jumlah review |
| phone | Nomor telepon |
| website | Website/URL |
| full_address | Alamat lengkap |
| province | Provinsi (auto-detect) |
| city | Kota/Kabupaten (auto-detect) |
| latitude/longitude | Koordinat GPS |
| category | Kategori (masjid, toko sembako, dll) |

---

## ⚠️ CATATAN PENTING

1. **Rate Limiting**: Google Maps memiliki proteksi, jangan scraping terlalu cepat
2. **Proxy**: Untuk skala besar, gunakan rotating proxies
3. **Legal**: Pastikan scraping sesuai dengan ketentuan Google
4. **Captcha**: Mungkin akan muncul captcha, perlu solusi manual atau 2Captcha

---

## 🔧 TROUBLESHOOTING

**Error: ChromeDriver not found**
```bash
pip install --upgrade webdriver-manager
```

**Error: Module not found**
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

**Google Maps block detection**
- Kurangi kecepatan scraping (tambah `time.sleep()`)
- Gunakan mode headless dengan user agent random

**Jalankan Script Standalone**

```bash
# Jalankan scraper langsung
python playwright_maps_scraper.py
```

**Jalankan via Django (jika sudah terintegrasi)**

```bash
# Scrape masjid seluruh Indonesia
python manage.py scrape_playwright masjid --level nasional --max 50

# Scrape toko sembako di DKI Jakarta
python manage.py scrape_playwright "toko sembako" --level provinsi --value "DKI Jakarta" --max 100

# Scrape restoran di Surabaya (headless mode untuk server)
python manage.py scrape_playwright restoran --level kota --value "Surabaya" --headless
```
---

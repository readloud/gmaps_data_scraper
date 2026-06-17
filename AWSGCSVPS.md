### 🧭 AWS vs. GCP (Cloud Run)

Sebelum masuk ke teknis, penting untuk pilih jalur yang sesuai dengan kebutuhan Anda.

*   **Google Cloud Run (GCP)**: Ini adalah opsi **paling direkomendasikan** untuk Django karena sifatnya yang **serverless**. Anda hanya perlu mengemas aplikasi dalam container Docker, dan Google akan mengelola infrastruktur serta penskalaan secara otomatis berdasarkan lalu lintas (bahkan bisa skala ke nol untuk menghemat biaya) . Platform ini juga terintegrasi secara native dengan layanan GCP lainnya seperti Cloud SQL dan Secret Manager, yang akan memudahkan Anda mengelola konfigurasi dan database .
*   **Amazon Web Services (AWS)**: Dengan AWS, Anda memiliki beberapa opsi. Untuk **kemudahan**, **AWS App Runner** adalah pilihan PaaS yang mirip dengan Cloud Run. Untuk **kontrol penuh**, Anda bisa deploy di **EC2 (virtual server)**  atau menggunakan **ECS** dengan **Application Load Balancer** untuk skala enterprise . EC2 memberi Anda server yang bisa diakses via SSH, sehingga Anda bisa menginstal semua kebutuhan, termasuk Playwright untuk web scraping, secara manual .

### ⚙️ Persiapan Awal: Containerization (Docker)

Apapun platform yang Anda pilih, **langkah pertama adalah mengemas aplikasi Anda ke dalam Docker container**. Ini membuat proses deployment menjadi konsisten dan portabel di mana saja . Buat file `Dockerfile` di root project Anda:

```dockerfile
# Menggunakan base image Python resmi
FROM python:3.11-slim

# Menentukan working directory di dalam container
WORKDIR /app

# Copy file requirements dan install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright dan browser-nya untuk web scraping (sangat penting untuk aplikasi Anda!)
RUN playwright install chromium

# Copy seluruh kode aplikasi
COPY . .

# Kumpulkan file statis Django
RUN python manage.py collectstatic --noinput

# Ekspose port yang digunakan
EXPOSE 8000

# Perintah untuk menjalankan aplikasi
CMD ["gunicorn", "maps_scraper_admin.wsgi:application", "--bind", "0.0.0.0:8000"]
```

### 🚀 Deploy ke Google Cloud Run

Ini adalah panduan singkat, untuk panduan lengkap bisa cek [Codelab resmi Google](https://codelabs.developers.google.com/codelabs/cloud-run-django) .

1.  **Aktifkan API**: Aktifkan Cloud Run, Cloud SQL, Artifact Registry, dan Secret Manager di project GCP Anda .
    ```bash
    gcloud services enable run.googleapis.com sqladmin.googleapis.com artifactregistry.googleapis.com secretmanager.googleapis.com
    ```
2.  **Siapkan Database (Cloud SQL)**: Buat instance PostgreSQL dan database di Cloud SQL. Catat nama instance-nya (misal: `myinstance`) dan kredensialnya .
    ```bash
    gcloud sql instances create myinstance --database-version POSTGRES_14 --tier db-f1-micro --region asia-southeast2
    gcloud sql databases create mydatabase --instance myinstance
    ```
3.  **Simpan Konfigurasi Rahasia (Secret Manager)**: Jangan simpan password atau `SECRET_KEY` di kode. Gunakan Secret Manager .
    ```bash
    echo "SECRET_KEY='django-insecure-...'" > .env
    echo "DATABASE_URL='postgres://user:pass@/cloudsql/PROJECT_ID:REGION:INSTANCE_NAME/DB_NAME'" >> .env
    gcloud secrets create application_settings --data-file .env
    ```
4.  **Build dan Deploy Image**:
    ```bash
    # Build image dan push ke Artifact Registry
    gcloud builds submit --tag asia-southeast2-docker.pkg.dev/PROJECT_ID/containers/django-scraper .

    # Deploy ke Cloud Run
    gcloud run deploy django-scraper \
      --image asia-southeast2-docker.pkg.dev/PROJECT_ID/containers/django-scraper \
      --platform managed \
      --region asia-southeast2 \
      --allow-unauthenticated \
      --update-secrets=/app/.env=application_settings:latest \
      --add-cloudsql-instances PROJECT_ID:asia-southeast2:myinstance
    ```
    > **Note**: Parameter `--add-cloudsql-instances` menghubungkan Cloud Run ke database Cloud SQL Anda.

### 🚀 Deploy ke AWS EC2

Ini adalah opsi paling "tradisional" dan ekonomis untuk memulai di AWS .

1.  **Siapkan EC2**: Luncurkan instance EC2 dengan OS Ubuntu. Pastikan port **22 (SSH)** dan **80 (HTTP)** terbuka di Security Group-nya .
2.  **Hubungkan via SSH**:
    ```bash
    ssh -i /path/to/your-key.pem ubuntu@your-instance-public-ip
    ```
3.  **Instal Dependencies di Server**:
    ```bash
    sudo apt update && sudo apt upgrade -y
    sudo apt install -y python3-pip python3-venv nginx supervisor
    ```
4.  **Clone Project dan Setup Virtual Environment** :
    ```bash
    git clone https://github.com/yourusername/your-repo.git
    cd your-repo
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    # Penting: Pastikan playwright terinstall di server
    playwright install chromium
    ```
5.  **Konfigurasi Gunicorn dengan Supervisor**: Buat file konfigurasi di `/etc/supervisor/conf.d/gunicorn.conf` agar Gunicorn berjalan sebagai service .
6.  **Konfigurasi Nginx**: Buat file konfigurasi di `/etc/nginx/sites-available/` dan aktifkan. Nginx akan bertindak sebagai proxy dan melayani file statis .
    ```nginx
    server {
        listen 80;
        server_name your-domain.com;

        location /static/ {
            alias /home/ubuntu/your-repo/staticfiles/;
        }

        location / {
            include proxy_params;
            proxy_pass http://unix:/home/ubuntu/your-repo/app.sock;
        }
    }
    ```
7.  **Jalankan Service**:
    ```bash
    sudo supervisorctl reread && sudo supervisorctl update
    sudo systemctl restart nginx
    ```

### 📁 Handling Media & Static Files

Untuk aplikasi production, file statis dan media tidak boleh disimpan di server lokal. Gunakan layanan penyimpanan cloud:

*   **Untuk GCP**: Gunakan **Cloud Storage**. Integrasikan dengan Django menggunakan `django-storages[google]` untuk menyimpan file media .
*   **Untuk AWS**: Gunakan **S3** dengan library `django-storages[s3]`.

### 🎯 **VPS (Virtual Private Server)**

Untuk menjalankan Django dengan Playwright dengan stabil, pastikan VPS Anda memiliki spesifikasi minimal:

*   **OS**: Ubuntu 20.04 LTS atau 22.04 LTS (paling direkomendasikan) .
*   **RAM**: Minimal 2GB, tetapi **4GB sangat disarankan** (Playwright membutuhkan memori yang cukup) .
*   **CPU**: 1 vCPU minimum, tetapi 2 vCPU akan memberikan performa yang lebih baik saat scraping .
*   **Storage**: 20GB SSD atau lebih .

### ⚙️ Metode Deployment: `Dokploy` vs. Manual

Ada dua pendekatan utama untuk deployment di VPS. Saya sangat merekomendasikan **Dokploy** karena kemudahan dan fitur manajemennya yang modern.

| Aspek | Deployment dengan **Dokploy** (Rekomendasi) | Deployment Manual (Apache/Nginx) |
| :--- | :--- | :--- |
| **Kemudahan** | **Sangat Mudah** - Web UI untuk deploy, manage SSL, dan scaling . | **Kompleks** - Butuh konfigurasi manual untuk setiap komponen . |
| **Manajemen** | **Terpusat** - Semua aplikasi dan layanan (DB, Redis) di satu dashboard . | **Tersebar** - Perlu kelola service systemd, Nginx, dan lainnya secara terpisah. |
| **SSL/HTTPS** | **Otomatis** - Let's Encrypt terintegrasi . | **Manual** - Perlu setup dan renew certificate sendiri. |
| **Rollback & CI/CD** | **Mudah** - Hanya dengan klik dari dashboard . | **Kompleks** - Perlu script custom atau CI/CD pipeline. |
| **Cocok Untuk** | Indie hacker, developer yang ingin fokus pada kode, deployment production modern . | Developer yang ingin kontrol penuh atau sedang belajar administrasi server . |

### 🚀 Panduan Deploy dengan Dokploy (Metode Terbaik)

Berikut langkah-langkah detailnya :

#### **1. Setup Awal VPS**

*   **Koneksi SSH**: Hubungkan ke server Anda.
    ```bash
    ssh root@your-vps-ip
    ```
*   **Update System**: Pastikan semua paket terbaru.
    ```bash
    sudo apt update && sudo apt upgrade -y
    sudo apt install -y curl wget git htop ufw
    ```
*   **Konfigurasi Firewall**: Buka port yang diperlukan.
    ```bash
    sudo ufw allow ssh
    sudo ufw allow 80
    sudo ufw allow 443
    sudo ufw allow 3000 # Port untuk dashboard Dokploy
    sudo ufw enable
    ```

#### **2. Install Docker dan Dokploy**

*   **Install Docker**:
    ```bash
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    newgrp docker
    ```
*   **Install Dokploy**:
    ```bash
    curl -sSL https://dokploy.com/install.sh | sh
    ```
*   **Akses Dashboard**: Buka `http://your-vps-ip:3000` di browser dan selesaikan setup awal.

#### **3. Konfigurasi Domain dan SSL**

*   Arahkan domain (misal, `api.your-domain.com`) ke IP VPS Anda melalui DNS.
*   Di dashboard Dokploy, masuk ke **Settings → SSL**, tambahkan domain Anda, dan aktifkan Let's Encrypt untuk SSL otomatis .

#### **4. Deploy Aplikasi Django**

*   **Buat Aplikasi Baru**: Di dashboard Dokploy, klik **"New Application"** dan pilih **"Git Repository"**.
*   **Konfigurasi Environment Variables**: Tambahkan variabel penting berikut :
    ```env
    # Django
    SECRET_KEY=your-super-secret-production-key
    DEBUG=False
    ALLOWED_HOSTS=your-domain.com,your-vps-ip
    
    # Database
    DB_NAME=scraper_db
    DB_USER=scraper_user
    DB_PASSWORD=your-secure-db-password
    ```
*   **Setup Docker Compose**: Di dashboard, atur file `docker-compose.prod.yml`. Berikut adalah contoh minimal untuk kebutuhan Anda :
    ```yaml
    version: '3.8'

    services:
      web:
        build: .
        command: gunicorn --bind 0.0.0.0:8000 --workers 3 maps_scraper_admin.wsgi:application
        volumes:
          - static_volume:/app/staticfiles
          - media_volume:/app/media
        ports:
          - "8000:8000"
        depends_on:
          - db
        env_file:
          - .env
        restart: unless-stopped

      db:
        image: postgres:15
        volumes:
          - postgres_data:/var/lib/postgresql/data/
        env_file:
          - .env
        restart: unless-stopped
        ports:
          - "5432:5432"

    volumes:
      postgres_data:
      static_volume:
      media_volume:
    ```
*   **Deploy**: Klik tombol **"Deploy Application"** di dashboard. Pantau log untuk memastikan tidak ada error .

#### **5. Setup Database dan Static Files**

Setelah aplikasi berhasil di-deploy, jalankan perintah berikut (dapat diakses melalui terminal di dashboard Dokploy atau via SSH) :

```bash
# Migrasi Database
docker-compose exec web python manage.py migrate

# Buat Superuser Admin
docker-compose exec web python manage.py createsuperuser

# Kumpulkan Static Files
docker-compose exec web python manage.py collectstatic --noinput
```

### 📁 Tips Penting untuk Playwright di Docker

Karena aplikasi Anda menggunakan Playwright, ada beberapa hal penting yang perlu diperhatikan dalam `Dockerfile` :

1.  **Pastikan untuk menginstall Playwright dan browser-nya** di dalam Docker image.
2.  **Install semua dependencies sistem** yang dibutuhkan Playwright untuk berjalan di Linux (seperti `libnss3`, `libatk-bridge2.0-0`, `libx11-xcb1`, dll.) .

Contoh perintah dalam `Dockerfile` yang sudah dimodifikasi:

```dockerfile
FROM python:3.11-slim

# Install system dependencies untuk Playwright
RUN apt-get update && apt-get install -y \
    libnss3 \
    libatk-bridge2.0-0 \
    libdrm-dev \
    libxkbcommon-dev \
    libgbm-dev \
    libasound-dev \
    libxshmfence1 \
    libgtk-3-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright dan browser Chromium
RUN playwright install chromium

COPY . .
RUN python manage.py collectstatic --noinput

EXPOSE 8000
CMD ["gunicorn", "maps_scraper_admin.wsgi:application", "--bind", "0.0.0.0:8000"]
```

### 🎯 Ringkasan

*   Untuk **kemudahan dan biaya fleksibel**, pilih **Google Cloud Run**. Proses deployment-nya lebih sederhana karena Anda hanya fokus pada kode dan container .
*   Untuk **kontrol penuh atas lingkungan**, terutama jika aplikasi Anda membutuhkan konfigurasi Playwright yang rumit, pilih **AWS EC2**. Ini memberikan akses server langsung untuk debugging dan instalasi software tambahan .


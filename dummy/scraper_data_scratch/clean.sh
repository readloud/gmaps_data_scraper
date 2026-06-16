# Hapus database
rm db.sqlite3

# Hapus file hasil scraping
rm *.xlsx *.csv 2>/dev/null

# Hapus folder venv
rm -rf venv/

# Hapus folder __pycache__
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null

# Hapus file .env (jangan upload ke GitHub!)
rm .env 2>/dev/null
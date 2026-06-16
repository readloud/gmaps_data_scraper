# scraper_data/forms.py
from django import forms

class DynamicScrapeForm(forms.Form):
    """
    Form untuk input scraping dinamis
    User bisa input APAPUN keyword
    """
    
    keyword = forms.CharField(
        max_length=200,
        label='🔍 Keyword Pencarian',
        help_text='Contoh: masjid, toko sembako, klinik kecantikan, bengkel motor, sekolah musik, dll. <strong>APAPUN BISA!</strong>',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Cari apapun... (masjid, toko sembako, klinik, dll)',
            'style': 'font-size: 16px; padding: 12px;',
            'autofocus': 'autofocus'
        })
    )
    
    filter_level = forms.ChoiceField(
        choices=[
            ('nasional', '🇮🇩 Nasional (Seluruh Indonesia)'),
            ('provinsi', '📍 Provinsi'),
            ('kota', '🏙️ Kota/Kabupaten')
        ],
        label='Level Filter Lokasi',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    filter_value = forms.CharField(
        required=False,
        label='Nama Provinsi/Kota',
        help_text='Isi jika memilih Provinsi atau Kota (contoh: DKI Jakarta, Surabaya, Bandung)',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Contoh: DKI Jakarta'
        })
    )
    
    max_results = forms.IntegerField(
        initial=50,
        min_value=5,
        max_value=200,
        label='Maksimal Hasil',
        help_text='Jumlah maksimal data yang diambil (5-200)',
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    
    get_details = forms.BooleanField(
        required=False,
        initial=True,
        label='Ambil detail lengkap (telepon, website, jam operasional)',
        help_text='Membutuhkan waktu lebih lama tapi data lebih lengkap',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    def clean(self):
        cleaned_data = super().clean()
        filter_level = cleaned_data.get('filter_level')
        filter_value = cleaned_data.get('filter_value')
        
        if filter_level in ['provinsi', 'kota'] and not filter_value:
            raise forms.ValidationError("Nama provinsi/kota harus diisi untuk filter lokasi")
        
        return cleaned_data
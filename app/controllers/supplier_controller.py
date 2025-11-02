
import logging
import uuid
import time
import os
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from fastapi import HTTPException, status
from app.config import get_settings

logger = logging.getLogger(__name__)

PLACES_API_BASE_URL = "https://places.googleapis.com/v1"

# Daftar kota di Sumatera Barat
KOTA_SUMBAR = [
    "Padang",
    "Bukittinggi",
    "Padang Panjang",
    "Pariaman",
    "Payakumbuh",
    "Sawahlunto",
    "Solok",
    "Padang Pariaman",
    "Agam",
    "Dharmasraya",
    "Kepulauan Mentawai",
    "Lima Puluh Kota",
    "Pasaman",
    "Pasaman Barat",
    "Pesisir Selatan",
    "Sijunjung",
    "Solok Selatan",
    "Tanah Datar"
]

def generate_search_keywords(tipe_produk: List[str], jenis_ikan: List[str], kota: List[str]) -> List[str]:
    """
    Generate keywords pencarian dari kombinasi tipe produk, jenis ikan, dan kota
    Dengan keyword yang lebih spesifik untuk akurasi lebih baik
    """
    keywords = []
    
    # Mapping tipe produk ke keyword yang lebih spesifik
    tipe_keywords = {
        'pakan': ['pakan', 'jual pakan', 'toko pakan', 'supplier pakan', 'distributor pakan'],
        'bibit': ['bibit', 'jual bibit', 'toko bibit', 'supplier bibit', 'penjual bibit']
    }
    
    for tipe in tipe_produk:
        for ikan in jenis_ikan:
            for k in kota:
                # Gunakan keyword spesifik sesuai tipe
                if tipe in tipe_keywords:
                    for kw in tipe_keywords[tipe]:
                        keyword = f"{kw} {ikan} {k}"
                        keywords.append(keyword)
                else:
                    keyword = f"{tipe} {ikan} {k}"
                    keywords.append(keyword)
    
    return keywords

def is_relevant_place(place: Dict, tipe_produk: List[str], jenis_ikan: List[str]) -> bool:
    """
    Filter apakah tempat relevan dengan tipe produk dan jenis ikan yang dicari
    """
    # Ambil nama tempat
    display_name = place.get('displayName', {})
    nama_toko = display_name.get('text', '') if isinstance(display_name, dict) else str(display_name)
    nama_toko_lower = nama_toko.lower()
    
    # Kata kunci yang harus dihindari (bukan supplier/toko pakan-bibit)
    exclude_keywords = [
        'pecel', 'warung', 'restoran', 'rumah makan', 'kedai', 
        'cafe', 'kuliner', 'makanan', 'goreng', 'sambal',
        'ayam goreng', 'ayam bakar', 'ikan bakar', 'ikan goreng',
        'abon', 'sop', 'bakso', 'sate', 'gudeg'
    ]
    
    # Cek apakah mengandung kata yang harus dihindari - langsung filter out
    for exclude in exclude_keywords:
        if exclude in nama_toko_lower:
            return False
    
    # Kata kunci yang menunjukkan relevan dengan tipe produk
    relevant_keywords_pakan = ['pakan', 'ternak', 'pet shop', 'dunia pet', 'dunia unggas', 'makmur', 'distributor', 'supplier']
    relevant_keywords_bibit = ['bibit', 'benih', 'breeding']
    
    # Cek apakah nama mengandung keyword relevan
    has_pakan_keyword = any(kw in nama_toko_lower for kw in relevant_keywords_pakan)
    has_bibit_keyword = any(kw in nama_toko_lower for kw in relevant_keywords_bibit)
    
    # Normalize tipe produk ke lowercase untuk perbandingan
    tipe_produk_lower = [t.lower() for t in tipe_produk]
    
    # Logika filter:
    # 1. Jika mencari "pakan" saja (tanpa "bibit"), harus ada keyword pakan
    # 2. Jika mencari "bibit" saja (tanpa "pakan"), harus ada keyword bibit
    # 3. Jika mencari keduanya, harus ada salah satu keyword
    
    if 'pakan' in tipe_produk_lower and 'bibit' not in tipe_produk_lower:
        # Hanya mencari pakan, jadi harus ada keyword pakan
        return has_pakan_keyword
    
    if 'bibit' in tipe_produk_lower and 'pakan' not in tipe_produk_lower:
        # Hanya mencari bibit, jadi harus ada keyword bibit
        return has_bibit_keyword
    
    if 'pakan' in tipe_produk_lower and 'bibit' in tipe_produk_lower:
        # Mencari keduanya, harus ada salah satu keyword
        return has_pakan_keyword or has_bibit_keyword
    
    # Jika tidak ada tipe produk yang spesifik (tidak seharusnya terjadi), return True
    return True

def filter_relevant_places(places: List[Dict], tipe_produk: List[str], jenis_ikan: List[str]) -> List[Dict]:
    """
    Filter places yang relevan dengan tipe produk dan jenis ikan
    """
    filtered = []
    for place in places:
        if is_relevant_place(place, tipe_produk, jenis_ikan):
            filtered.append(place)
    return filtered

def search_places(keyword: str, location: str = None, google_maps_api_key: str = None) -> List[Dict]:
    """
    Mencari tempat menggunakan Google Places API (New) - Text Search
    """
    try:
        if not google_maps_api_key:
            raise ValueError("Google Maps API Key tidak ditemukan")
        
        url = f"{PLACES_API_BASE_URL}/places:searchText"
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": google_maps_api_key,
            "X-Goog-FieldMask": "places.id,places.displayName,places.formattedAddress,places.location,places.rating,places.nationalPhoneNumber,places.internationalPhoneNumber"
        }
        
        # Format location jika belum ada
        if not location:
            location = "Sumatera Barat, Indonesia"
        elif location and "Sumatera Barat" not in location:
            location = f"{location}, Sumatera Barat, Indonesia"
        
        payload = {
            "textQuery": f"{keyword} {location}",
            "languageCode": "id"
        }
        
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code != 200:
            error_text = response.text
            logger.error(f"Error API: {response.status_code} - {error_text}")
            
            # Parse error response untuk memberikan pesan yang lebih jelas
            try:
                error_json = response.json()
                error_detail = error_json.get('error', {})
                error_message = error_detail.get('message', 'Unknown error')
                error_code = error_detail.get('code', response.status_code)
                
                # Cek jika error terkait API key
                if 'API_KEY' in error_message or 'api key' in error_message.lower() or 'INVALID_ARGUMENT' in str(error_code):
                    logger.error(f"❌ Masalah dengan API Key: {error_message}")
                    logger.error(f"🔍 API Key yang digunakan (preview): {google_maps_api_key[:10]}...{google_maps_api_key[-5:] if len(google_maps_api_key) > 15 else ''}")
                    raise ValueError(f"Google Maps API Key tidak valid: {error_message}")
                    
            except (ValueError, KeyError, AttributeError):
                pass
            
            return []
        
        data = response.json()
        results = data.get('places', [])
        
        # Jika ada nextPageToken, ambil hasil berikutnya
        next_page_token = data.get('nextPageToken')
        while next_page_token:
            time.sleep(1)  # Delay untuk menunggu token siap (dikurangi dari 2 detik)
            payload_with_token = {
                **payload,
                "pageToken": next_page_token
            }
            response = requests.post(url, json=payload_with_token, headers=headers)
            
            if response.status_code != 200:
                break
                
            page_data = response.json()
            results.extend(page_data.get('places', []))
            next_page_token = page_data.get('nextPageToken')
        
        return results
    
    except Exception as e:
        logger.error(f"Error saat mencari tempat dengan keyword '{keyword}': {str(e)}")
        return []

def get_place_details(place_id: str, google_maps_api_key: str = None) -> Optional[Dict]:
    """
    Mengambil detail lengkap tempat berdasarkan place_id menggunakan Places API (New)
    """
    try:
        if not google_maps_api_key:
            raise ValueError("Google Maps API Key tidak ditemukan")
        
        # Strip whitespace dari API key untuk memastikan tidak ada spasi tersembunyi
        google_maps_api_key = google_maps_api_key.strip()
        
        if not google_maps_api_key:
            raise ValueError("Google Maps API Key kosong setelah strip")
        
        url = f"{PLACES_API_BASE_URL}/places/{place_id}"
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": google_maps_api_key,
            "X-Goog-FieldMask": "id,displayName,formattedAddress,location,rating,nationalPhoneNumber,internationalPhoneNumber,websiteUri"
        }
        params = {
            "languageCode": "id"
        }
        
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code != 200:
            error_text = response.text
            logger.error(f"Error API: {response.status_code} - {error_text}")
            
            # Parse error response untuk memberikan pesan yang lebih jelas
            try:
                error_json = response.json()
                error_detail = error_json.get('error', {})
                error_message = error_detail.get('message', 'Unknown error')
                
                # Cek jika error terkait API key
                if 'API_KEY' in error_message or 'api key' in error_message.lower():
                    logger.error(f"❌ Masalah dengan API Key: {error_message}")
                    raise ValueError(f"Google Maps API Key tidak valid: {error_message}")
                    
            except (ValueError, KeyError):
                pass
            
            return None
        
        return response.json()
    
    except Exception as e:
        logger.error(f"Error saat mengambil detail place_id {place_id}: {str(e)}")
        return None

def extract_phone_number(place_details: Dict) -> str:
    """
    Mengambil nomor telepon dari detail tempat (Places API New format)
    """
    phone = (
        place_details.get('nationalPhoneNumber') or 
        place_details.get('internationalPhoneNumber') or 
        ''
    )
    # Bersihkan format nomor telepon
    phone = phone.replace(' ', '').replace('-', '').replace('+62', '0').strip()
    return phone

def convert_to_supplier_data(place_details: Dict) -> Dict:
    """
    Konversi data dari Google Places (New) ke format Supplier
    """
    location = place_details.get('location', {})
    
    supplier_id = str(uuid.uuid4())
    
    # Places API New menggunakan displayName bukan name
    nama_toko = place_details.get('displayName', {}).get('text', '') if isinstance(place_details.get('displayName'), dict) else place_details.get('displayName', '')
    
    # Places API New menggunakan formattedAddress bukan formatted_address
    alamat = place_details.get('formattedAddress', '')
    
    return {
        'id': supplier_id,
        'lang': str(location.get('longitude', '')),  # longitude
        'lat': str(location.get('latitude', '')),   # latitude
        'namaToko': nama_toko,
        'rating': int(place_details.get('rating', 0)) if place_details.get('rating') else 0,
        'alamat': alamat,
        'noHp': extract_phone_number(place_details),
    }

def fetch_suppliers(
    tipe_produk: List[str] = None,
    jenis_ikan: List[str] = None,
    kota: List[str] = None,
    google_maps_api_key: str = None,
    verbose: bool = True
) -> List[Dict]:
    """
    Mengambil data supplier ikan berdasarkan parameter
    
    Args:
        tipe_produk: List tipe produk ['pakan', 'bibit']
        jenis_ikan: List jenis ikan ['lele', 'nila', 'kerapu']
        kota: List kota di Sumbar
        google_maps_api_key: Google Maps API Key
        verbose: Print progress atau tidak
    
    Returns:
        List data supplier
    """
    # Default values
    if not tipe_produk:
        tipe_produk = ['pakan', 'bibit']
    if not jenis_ikan:
        jenis_ikan = ['lele', 'nila', 'kerapu']
    if not kota:
        kota = ['Padang']
    
    # Generate keywords
    search_keywords = generate_search_keywords(tipe_produk, jenis_ikan, kota)
    
    if verbose:
        logger.info(f"Mencari supplier dengan parameter:")
        logger.info(f"  Tipe Produk: {', '.join(tipe_produk)}")
        logger.info(f"  Jenis Ikan: {', '.join(jenis_ikan)}")
        logger.info(f"  Kota: {', '.join(kota)}")
        logger.info(f"Menggunakan {len(search_keywords)} keyword pencarian")
    
    all_places = {}
    seen_place_ids = set()
    
    for i, keyword in enumerate(search_keywords, 1):
        if verbose:
            logger.info(f"[{i}/{len(search_keywords)}] Mencari: {keyword}")
        
        # Extract kota dari keyword untuk location parameter
        location = None
        for k in kota:
            if k.lower() in keyword.lower():
                location = f"{k}, Sumatera Barat, Indonesia"
                break
        
        places = search_places(keyword, location, google_maps_api_key)
        
        # Filter hasil yang relevan dengan tipe produk
        relevant_places = filter_relevant_places(places, tipe_produk, jenis_ikan)
        
        for place in relevant_places:
            place_id = place.get('id')
            if place_id and place_id not in seen_place_ids:
                seen_place_ids.add(place_id)
                all_places[place_id] = place
        
        if verbose and len(relevant_places) < len(places):
            logger.info(f"  → Filtered: {len(places)} → {len(relevant_places)} relevan")
        
        time.sleep(0.2)  # Delay untuk menghindari rate limit (dikurangi dari 1 detik)
    
    if verbose:
        logger.info(f"\nDitemukan {len(all_places)} tempat unik")
        logger.info("Mengambil detail lengkap untuk setiap tempat (parallel)...")
    
    suppliers = []
    
    # Gunakan parallel processing untuk fetch detail (max 10 concurrent requests)
    def fetch_and_convert(place_item):
        place_id, place = place_item
        # Ambil nama dari displayName (Places API New format)
        display_name = place.get('displayName', {})
        nama_toko = display_name.get('text', 'Unknown') if isinstance(display_name, dict) else display_name or 'Unknown'
        
        place_details = get_place_details(place_id, google_maps_api_key)
        if place_details:
            supplier = convert_to_supplier_data(place_details)
            return supplier, nama_toko
        return None, nama_toko
    
    # Parallel processing dengan ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(fetch_and_convert, item): item for item in all_places.items()}
        
        completed = 0
        for future in as_completed(futures):
            completed += 1
            supplier, nama_toko = future.result()
            
            if verbose:
                logger.info(f"[{completed}/{len(all_places)}] Memproses: {nama_toko}")
            
            if supplier:
                suppliers.append(supplier)
    
    return suppliers

def get_kota_sumbar() -> List[str]:
    """
    Mengembalikan daftar kota di Sumatera Barat
    """
    return KOTA_SUMBAR

def scrape_suppliers_controller(
    tipe_produk: List[str] = None,
    jenis_ikan: List[str] = None,
    kota: List[str] = None
) -> Dict:
    """
    Controller untuk scraping supplier ikan
    
    Args:
        tipe_produk: List tipe produk ['pakan', 'bibit']
        jenis_ikan: List jenis ikan ['lele', 'nila', 'kerapu']
        kota: List kota di Sumbar
    
    Returns:
        Dict dengan success, count, dan data suppliers
    """
    try:
        # Hardcode API key untuk testing
        google_maps_api_key = "AIzaSyAg29NTRIfDxTLOfenIdX-ezjpEoIgJEoc"
        
        # Strip whitespace untuk memastikan tidak ada spasi tersembunyi
        google_maps_api_key = google_maps_api_key.strip()
        
        logger.info(f"✅ Menggunakan hardcoded Google Maps API Key (panjang: {len(google_maps_api_key)} karakter)")
        masked_key = f"{google_maps_api_key[:4]}...{google_maps_api_key[-4:]}"
        logger.info(f"🔑 API Key preview: {masked_key}")
        
        # Validasi input
        if not tipe_produk:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="tipeProduk tidak boleh kosong"
            )
        if not jenis_ikan:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="jenisIkan tidak boleh kosong"
            )
        if not kota:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="kota tidak boleh kosong"
            )
        
        # Validasi tipe produk
        valid_tipe = ['pakan', 'bibit']
        invalid_tipe = [t for t in tipe_produk if t not in valid_tipe]
        if invalid_tipe:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"tipeProduk tidak valid: {invalid_tipe}. Hanya boleh: {valid_tipe}"
            )
        
        # Fetch suppliers dengan API key yang sudah di-strip
        logger.info("🚀 Memulai scraping suppliers...")
        suppliers = fetch_suppliers(
            tipe_produk=tipe_produk,
            jenis_ikan=jenis_ikan,
            kota=kota,
            google_maps_api_key=google_maps_api_key,  # Sudah di-strip di atas
            verbose=False
        )
        logger.info(f"✅ Scraping selesai, ditemukan {len(suppliers)} supplier")
        
        return {
            'success': True,
            'count': len(suppliers),
            'data': suppliers
        }
    
    except HTTPException:
        raise
    except ValueError as e:
        # Error dari validasi API key
        error_msg = str(e)
        if "Google Maps API Key" in error_msg or "API key" in error_msg.lower():
            logger.error(f"❌ Masalah dengan API Key: {error_msg}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"{error_msg}. Pastikan:\n1. API key valid di Google Cloud Console\n2. Places API (New) sudah diaktifkan di Google Cloud Project\n3. API key tidak memiliki restriksi yang terlalu ketat\n4. Cek di: https://console.cloud.google.com/apis/library/places.googleapis.com"
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error validasi: {error_msg}"
        )
    except Exception as e:
        error_msg = str(e)
        logger.error(f"❌ Error saat scraping suppliers: {error_msg}", exc_info=True)
        
        # Cek jika error terkait Places API belum diaktifkan atau API key invalid
        if "API key" in error_msg.lower() or "API_KEY" in error_msg or "INVALID_ARGUMENT" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Google Maps API Key tidak valid atau Places API (New) belum diaktifkan. Error: {error_msg}. Silakan:\n1. Pastikan API key benar di file .env\n2. Aktifkan Places API (New) di: https://console.cloud.google.com/apis/library/places.googleapis.com\n3. Cek apakah API key memiliki restriksi yang sesuai"
            )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gagal scraping suppliers: {error_msg}"
        )


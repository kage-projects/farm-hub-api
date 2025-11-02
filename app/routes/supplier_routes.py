from fastapi import APIRouter, Query, status, HTTPException
from typing import List, Optional
from app.controllers.supplier_controller import scrape_suppliers_controller, get_kota_sumbar, KOTA_SUMBAR

router = APIRouter()

@router.get(
    "/suppliers",
    status_code=status.HTTP_200_OK,
    tags=["suppliers"]
)
async def fetch_suppliers(
    tipeProduk: Optional[str] = Query(default="pakan,bibit", description="Tipe produk: pakan, bibit (comma-separated)"),
    jenisIkan: Optional[str] = Query(default="lele,nila,kerapu", description="Jenis ikan: lele, nila, kerapu (comma-separated)"),
    kota: Optional[str] = Query(default="Padang", description="Kota di Sumatera Barat (comma-separated)")
):

    try:
        if isinstance(tipeProduk, list):
            tipe_produk = tipeProduk
        else:
            tipe_produk = [t.strip() for t in tipeProduk.split(',') if t.strip()]
        
        if isinstance(jenisIkan, list):
            jenis_ikan = jenisIkan
        else:
            jenis_ikan = [j.strip() for j in jenisIkan.split(',') if j.strip()]
        
        if isinstance(kota, list):
            kota_list = kota
        else:
            kota_list = [k.strip() for k in kota.split(',') if k.strip()]
        
        return scrape_suppliers_controller(
            tipe_produk=tipe_produk,
            jenis_ikan=jenis_ikan,
            kota=kota_list
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gagal fetch suppliers: {str(e)}"
        )

@router.get(
    "/suppliers/kota-sumbar",
    status_code=status.HTTP_200_OK,
    tags=["suppliers"]
)
async def get_kota_sumbar_list():
    """
    API endpoint untuk mendapatkan daftar kota di Sumatera Barat
    """
    return {
        'success': True,
        'data': get_kota_sumbar()
    }


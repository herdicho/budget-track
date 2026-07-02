import os
import json
from datetime import datetime
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from typing import List

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

class ReceiptItem(BaseModel):
    name: str = Field(description="Nama barang yang dibeli")
    quantity: int = Field(description="Jumlah barang yang dibeli")
    price: float = Field(description="Harga total untuk item ini dalam Rupiah")

class ReceiptDetails(BaseModel):
    merchant: str = Field(description="Nama toko, restoran, merchant, atau tempat pembelian")
    date: str = Field(description="Tanggal pembelian dalam format YYYY-MM-DD. Jika tanggal tidak ditemukan, gunakan tanggal hari ini")
    category: str = Field(description="Kategori pengeluaran. Harus bernilai salah satu dari: 'Makanan', 'Transportasi', 'Kebutuhan Bulanan', 'Kebutuhan Bayi', 'Hiburan', 'Lain-lain'")
    payment_source: str = Field(description="Sumber pembayaran jika terdeteksi di nota, contoh: 'BCA', 'Mandiri', 'Gopay', 'OVO', 'Cash'. Jika tidak terdeteksi, gunakan 'Cash'")
    amount: float = Field(description="Total nominal uang yang dibayarkan dalam Rupiah")
    items: List[ReceiptItem] = Field(description="Rincian barang/jasa yang dibeli")

def extract_receipt_details(image_bytes: bytes, mime_type: str = "image/jpeg") -> dict:
    """
    Sends receipt image bytes to Gemini API to extract transaction details in structured JSON.
    """
    if not GEMINI_API_KEY:
        # Fallback return when API key is missing, to allow testing backend flow
        return {
            "merchant": "[Demo] Toko Kelontong",
            "date": datetime.today().strftime('%Y-%m-%d'),
            "category": "Kebutuhan Bulanan",
            "payment_source": "Cash",
            "amount": 125000.0,
            "items": [
                {"name": "Minyak Goreng 2L", "quantity": 1, "price": 45000.0},
                {"name": "Beras 5kg", "quantity": 1, "price": 80000.0}
            ]
        }

    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        prompt = (
            "Analisis gambar nota belanja ini dan ekstrak informasi transaksi secara terperinci. "
            "Isi bidang 'category' dengan memilih salah satu dari: Makanan, Transportasi, Kebutuhan Bulanan, "
            "Kebutuhan Bayi, Hiburan, atau Lain-lain. Jika ada metode pembayaran yang tertulis di nota (seperti debit BCA, QRIS Gopay, cash, dll), "
            "tebak payment_source-nya. Jika tidak ada, kembalikan 'Cash'."
        )
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[
                types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                prompt
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=ReceiptDetails,
            ),
        )
        
        if response.text:
            return json.loads(response.text)
        else:
            raise ValueError("Respons Gemini kosong.")
            
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        # Fallback fallback
        return {
            "merchant": "Gagal Ekstraksi",
            "date": datetime.today().strftime('%Y-%m-%d'),
            "category": "Lain-lain",
            "payment_source": "Cash",
            "amount": 0.0,
            "items": []
        }

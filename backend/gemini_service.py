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
    category: str = Field(description="Kategori spesifik untuk item ini. Harus bernilai salah satu dari: 'Makanan', 'Transportasi', 'Kebutuhan Bulanan', 'Kebutuhan Bayi', 'Sosial & Ibadah', 'Hiburan', 'Liburan & Perjalanan', 'Perlengkapan & Acara', 'Lain-lain'")

class ReceiptDetails(BaseModel):
    merchant: str = Field(description="Nama toko, restoran, merchant, atau tempat pembelian")
    date: str = Field(description="Tanggal pembelian dalam format YYYY-MM-DD. Jika tanggal tidak ditemukan, gunakan tanggal hari ini")
    category: str = Field(description="Kategori pengeluaran. Harus bernilai salah satu dari: 'Makanan', 'Transportasi', 'Kebutuhan Bulanan', 'Kebutuhan Bayi', 'Sosial & Ibadah', 'Hiburan', 'Liburan & Perjalanan', 'Perlengkapan & Acara', 'Lain-lain'")
    payment_source: str = Field(description="Sumber pembayaran jika terdeteksi di nota, contoh: 'BCA', 'Mandiri', 'Gopay', 'OVO', 'Cash'. Jika tidak terdeteksi, gunakan 'Cash'")
    amount: float = Field(description="Total nominal uang yang dibayarkan dalam Rupiah")
    items: List[ReceiptItem] = Field(description="Rincian barang/jasa yang dibeli")

class ParsedEmailTransaction(BaseModel):
    is_valid_transaction: bool = Field(description="Set True jika email ini berisi bukti transaksi/pembayaran/transfer riil dengan nominal tertentu. Set False jika ini email promosi, newsletter, atau notifikasi non-keuangan.")
    merchant: str = Field(description="Nama toko, penyedia jasa, merchant, atau penerima transfer (contoh: 'GrabBike', 'GrabFood', 'Shopee', 'Indomaret', 'Gojek', 'BCA', 'Mandiri Livin').")
    date: str = Field(description="Tanggal transaksi dalam format YYYY-MM-DD. Jika tanggal tidak ditemukan di email, gunakan tanggal hari ini.")
    category: str = Field(description="Kategori pengeluaran. Harus bernilai salah satu dari: 'Makanan', 'Transportasi', 'Kebutuhan Bulanan', 'Kebutuhan Bayi', 'Sosial & Ibadah', 'Hiburan', 'Liburan & Perjalanan', 'Perlengkapan & Acara', 'Keluarga', 'Transfer', 'Pendapatan', 'Lain-lain'.")
    payment_source: str = Field(description="Sumber pembayaran jika terdeteksi di email, contoh: 'Mandiri', 'BNI', 'BCA', 'Gopay', 'OVO', 'ShopeePay', 'Cash'. Jika tidak terdeteksi, gunakan 'Mandiri'.")
    amount: float = Field(description="Total nominal uang transaksi dalam Rupiah (tanpa titik/koma).")
    transfer_to: Optional[str] = Field(default=None, description="Nama atau nomor rekening tujuan transfer jika kategori adalah 'Transfer'.")

def parse_email_transaction(subject: str, sender: str = "", body: str = "") -> dict:
    """
    Sends email subject, sender, and text body to Gemini API to parse transaction details into structured JSON.
    """
    if not GEMINI_API_KEY:
        return {
            "is_valid_transaction": True,
            "merchant": "Demo GrabBike",
            "date": datetime.today().strftime('%Y-%m-%d'),
            "category": "Transportasi",
            "payment_source": "Gopay",
            "amount": 14000.0,
            "transfer_to": None
        }

    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        prompt = (
            f"Analisis email bukti transaksi/struk pembayaran berikut dan ekstrak detail transaksinya:\n\n"
            f"Subject: {subject}\n"
            f"Pengirim (From): {sender}\n"
            f"Isi Email:\n{body[:4000]}\n\n"
            f"Tentukan apakah email ini merupakan resi/struk/bukti pembayaran/transfer keuangan asli. "
            f"PILIHAN KATEGORI: 'Makanan', 'Transportasi', 'Kebutuhan Bulanan', 'Kebutuhan Bayi', 'Sosial & Ibadah', 'Hiburan', 'Liburan & Perjalanan', 'Perlengkapan & Acara', 'Keluarga', 'Transfer', 'Pendapatan', atau 'Lain-lain'. "
            f"Petunjuk Kategori:\n"
            f"- GrabBike / GrabCar / GoRide / GoCar / Parkir / Bensin → 'Transportasi'\n"
            f"- GrabFood / GoFood / Resto / Cafe / Makanan → 'Makanan'\n"
            f"- Indomaret / Alfamart / Superindo / Belanja Bulanan → 'Kebutuhan Bulanan'\n"
            f"- Susu Bayi / Popok / Perlengkapan Bayi → 'Kebutuhan Bayi'\n"
            f"- Transfer uang / kirim saldo → Kategori 'Transfer', isi field transfer_to nama penerimanya."
        )
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[prompt],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=ParsedEmailTransaction,
            ),
        )
        
        if response.text:
            return json.loads(response.text)
        else:
            raise ValueError("Respons Gemini kosong.")
            
    except Exception as e:
        print(f"Error calling Gemini API for email parsing: {e}")
        return {
            "is_valid_transaction": False,
            "merchant": "Error Parsing",
            "date": datetime.today().strftime('%Y-%m-%d'),
            "category": "Lain-lain",
            "payment_source": "Cash",
            "amount": 0.0,
            "transfer_to": None
        }

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
                {"name": "Minyak Goreng 2L", "quantity": 1, "price": 45000.0, "category": "Kebutuhan Bulanan"},
                {"name": "Beras 5kg", "quantity": 1, "price": 80000.0, "category": "Makanan"}
            ]
        }

    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        prompt = (
            "Analisis gambar nota belanja ini dan ekstrak informasi transaksi secara terperinci. "
            "PENTING: Untuk setiap item/barang di nota, tentukan kategori SPESIFIK per-item di field 'category' pada masing-masing item. "
            "Contoh: telur, beras, mie instan → 'Makanan'; sabun, shampo, detergen → 'Kebutuhan Bulanan'; popok, susu bayi → 'Kebutuhan Bayi'; bak mandi, stroller, mainan → 'Perlengkapan & Acara'; tiket wisata, kereta liburan → 'Liburan & Perjalanan'. "
            "Field 'category' di level atas (bukan item) diisi dengan kategori yang paling dominan/banyak di nota. "
            "Pilihan kategori: Makanan, Transportasi, Kebutuhan Bulanan, Kebutuhan Bayi, Sosial & Ibadah, Hiburan, Liburan & Perjalanan, Perlengkapan & Acara, atau Lain-lain. "
            "Jika ada metode pembayaran yang tertulis di nota (seperti debit BCA, QRIS Gopay, cash, dll), "
            "tebak payment_source-nya."
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

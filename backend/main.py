import os
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, Depends, HTTPException, Header, UploadFile, File, Form, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

import supabase_service
import gemini_service

load_dotenv()

app = FastAPI(title="Budget Tracker API", version="1.0.0")

# Allow CORS for Vue frontend (Vite default is http://localhost:5173, but let's allow all in local or specify)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict to frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

APP_PASSWORD = os.getenv("APP_PASSWORD", "1234")

# Health check endpoint — ping this every 10 min to keep Render awake
@app.get("/health")
def health_check():
    return {"status": "ok"}


# Security Dependency
def verify_app_password(x_app_password: Optional[str] = Header(None)):
    if not x_app_password or x_app_password != APP_PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Akses Ditolak: Password/PIN tidak valid"
        )
    return True

class LoginRequest(BaseModel):
    password: str

class BudgetRequest(BaseModel):
    month: str # YYYY-MM
    amount: float
    income: Optional[float] = 0.0

class TransactionRequest(BaseModel):
    merchant: str
    date: str
    category: str
    payment_source: str
    amount: float
    user_name: str = "Suami"
    items: Optional[list] = []
    receipt_url: Optional[str] = None
    transfer_to: Optional[str] = None

class PaymentSourceCreate(BaseModel):
    name: str
    type: str # 'bank', 'ewallet', 'cash'

class CategoryCreate(BaseModel):
    name: str
    emoji: str = "📦"
    color: str = "#ff5555"

@app.post("/api/auth/verify")
def verify_auth(req: LoginRequest):
    if req.password == APP_PASSWORD:
        return {"status": "success", "message": "Autentikasi berhasil"}
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="PIN/Password salah!"
    )

@app.get("/api/dashboard/summary", dependencies=[Depends(verify_app_password)])
def get_summary(month: Optional[str] = None):
    if not month:
        month = datetime.today().strftime('%Y-%m')
    try:
        summary = supabase_service.get_dashboard_summary(month)
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/transactions", dependencies=[Depends(verify_app_password)])
def read_transactions(month: Optional[str] = None):
    try:
        txs = supabase_service.get_transactions(month)
        return txs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/transactions", dependencies=[Depends(verify_app_password)])
def create_new_transaction(tx: TransactionRequest):
    try:
        data = tx.model_dump()
        result = supabase_service.create_transaction(data)
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/transactions/{transaction_id}", dependencies=[Depends(verify_app_password)])
def remove_transaction(transaction_id: str):
    try:
        supabase_service.delete_transaction(transaction_id)
        return {"status": "success", "message": "Transaksi berhasil dihapus"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/transactions/{tx_id}", dependencies=[Depends(verify_app_password)])
def update_transaction(tx_id: str, req: TransactionRequest):
    try:
        t = supabase_service.update_transaction(
            tx_id=tx_id,
            merchant=req.merchant,
            date=req.date,
            category=req.category,
            payment_source=req.payment_source,
            amount=req.amount,
            user_name=req.user_name,
            items=req.items,
            receipt_url=req.receipt_url,
            transfer_to=req.transfer_to
        )
        if not t:
            raise HTTPException(status_code=404, detail="Transaksi tidak ditemukan")
        return {"status": "success", "data": t}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/budget", dependencies=[Depends(verify_app_password)])
def read_budget(month: str):
    try:
        b = supabase_service.get_budget(month)
        return b or {"month": month, "amount": 0}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/budget", dependencies=[Depends(verify_app_password)])
def update_budget(req: BudgetRequest):
    try:
        b = supabase_service.set_budget(req.month, req.amount, req.income)
        return {"status": "success", "data": b}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/payment-sources")
def get_payment_sources():
    try:
        sources = supabase_service.get_payment_sources()
        return sources
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/payment-sources", dependencies=[Depends(verify_app_password)])
def create_payment_source(req: PaymentSourceCreate):
    try:
        if req.type not in ('bank', 'ewallet', 'cash'):
            raise HTTPException(status_code=400, detail="Tipe harus bernilai: bank, ewallet, atau cash")
        source = supabase_service.create_payment_source(req.name, req.type)
        return {"status": "success", "data": source}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/categories")
def get_categories():
    try:
        cats = supabase_service.get_categories()
        return cats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/categories", dependencies=[Depends(verify_app_password)])
def create_category(req: CategoryCreate):
    try:
        c = supabase_service.create_category(req.name, req.emoji, req.color)
        return {"status": "success", "data": c}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/receipts/process", dependencies=[Depends(verify_app_password)])
async def process_receipt(file: UploadFile = File(...)):
    """
    Receives receipt image, uploads it to Supabase Storage (if configured),
    sends to Gemini OCR API, and returns JSON of details.
    """
    try:
        contents = await file.read()
        
        # 1. Upload to Supabase Storage in the background
        # If Supabase storage isn't fully set up or errors, we log and continue without failing the OCR
        receipt_url = ""
        try:
            receipt_url = supabase_service.upload_receipt(
                file_bytes=contents,
                file_name=file.filename,
                content_type=file.content_type
            )
        except Exception as se:
            print(f"Skipping Supabase Storage upload: {se}")
            
        # 2. Extract details using Gemini API
        extracted = gemini_service.extract_receipt_details(
            image_bytes=contents,
            mime_type=file.content_type
        )
        
        # Inject receipt URL into results
        extracted["receipt_url"] = receipt_url
        
        return extracted
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal memproses nota: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)

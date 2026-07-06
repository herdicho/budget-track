import os
import uuid
import time
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "").strip()

# Auto-clean trailing /rest/v1/ or /rest/v1 from Data API URL copy-paste
if SUPABASE_URL.endswith("/rest/v1/"):
    SUPABASE_URL = SUPABASE_URL[:-9]
elif SUPABASE_URL.endswith("/rest/v1"):
    SUPABASE_URL = SUPABASE_URL[:-8]

# Check if Supabase credentials are valid (not placeholders)
_has_supabase_config = bool(
    SUPABASE_URL and SUPABASE_KEY 
    and "your-supabase" not in SUPABASE_URL 
    and SUPABASE_URL != ""
)

# Lazy client with auto-reconnect
_supabase_client: Client = None
_client_created_at: float = 0
_CLIENT_MAX_AGE_SECONDS = 300  # Recreate client every 5 minutes to prevent stale connections

def _create_client() -> Client:
    """Create a fresh Supabase client."""
    global _supabase_client, _client_created_at
    try:
        _supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
        _client_created_at = time.time()
        print("Supabase client (re)initialized successfully.")
        return _supabase_client
    except Exception as e:
        print(f"Failed to initialize Supabase client: {e}")
        _supabase_client = None
        return None

# Initialize on first load if config is available
if _has_supabase_config:
    _create_client()
else:
    print("Running backend in mock/local mode (Supabase URL/Key not configured or placeholders used).")

# For backward compat: module-level reference
supabase_client = _supabase_client

def get_client() -> Client:
    """Get Supabase client with auto-reconnect if stale or dead."""
    global supabase_client, _supabase_client
    
    if not _has_supabase_config:
        return None
    
    # Recreate client if it's too old (prevents stale connections after HF sleep)
    age = time.time() - _client_created_at
    if _supabase_client is None or age > _CLIENT_MAX_AGE_SECONDS:
        print(f"Supabase client is stale ({age:.0f}s old) or missing. Reconnecting...")
        _create_client()
        supabase_client = _supabase_client
    
    if not _supabase_client:
        raise ValueError("Supabase client is not initialized. Please set SUPABASE_URL and SUPABASE_KEY in .env.")
    
    return _supabase_client

def execute_with_retry(query_fn):
    """
    Executes a query function that takes a Supabase client.
    If it fails, recreates the client and retries once.
    """
    client = get_client()
    try:
        return query_fn(client)
    except Exception as e:
        print(f"Supabase query failed: {e}. Reconnecting client and retrying once...")
        global _client_created_at
        _client_created_at = 0  # Force recreation on the next get_client call
        client = get_client()
        return query_fn(client)

# Mock database for fallback local testing
mock_transactions = [
    {
        "id": "mock-income-1",
        "merchant": "Gaji Bulanan",
        "date": datetime.today().strftime('%Y-%m-%d'),
        "category": "Pendapatan",
        "payment_source": "BCA",
        "amount": 7500000.0,
        "user_name": "Suami",
        "items": [],
        "receipt_url": None,
        "transfer_to": None,
        "created_at": datetime.today().strftime('%Y-%m-%dT07:00:00Z')
    },
    {
        "id": "1",
        "merchant": "Supermarket Indomaret",
        "date": datetime.today().strftime('%Y-%m-%d'),
        "category": "Makanan",
        "payment_source": "Cash",
        "amount": 150000.0,
        "user_name": "Suami",
        "items": [{"name": "Beras", "quantity": 1, "price": 85000}, {"name": "Minyak Goreng", "quantity": 2, "price": 32500}],
        "receipt_url": None,
        "transfer_to": None,
        "created_at": datetime.today().strftime('%Y-%m-%dT10:00:00Z')
    },
    {
        "id": "2",
        "merchant": "Bensin Pertamina",
        "date": datetime.today().strftime('%Y-%m-%d'),
        "category": "Transportasi",
        "payment_source": "Bank",
        "amount": 200000.0,
        "user_name": "Istri",
        "items": [],
        "receipt_url": None,
        "transfer_to": None,
        "created_at": datetime.today().strftime('%Y-%m-%dT08:30:00Z')
    },
    {
        "id": "3",
        "merchant": "Susu Bayi & Diapers",
        "date": datetime.today().strftime('%Y-%m-%d'),
        "category": "Kebutuhan Bayi",
        "payment_source": "E-Wallet",
        "amount": 350000.0,
        "user_name": "Istri",
        "items": [],
        "receipt_url": None,
        "transfer_to": None,
        "created_at": datetime.today().strftime('%Y-%m-%dT11:15:00Z')
    }
]

# Set budget dynamically for the current month
current_month = datetime.today().strftime('%Y-%m')
mock_budgets = {
    current_month: {"month": current_month, "amount": 5000000.0, "income": 7000000.0}
}

mock_payment_sources = [
    {"name": "Cash", "type": "cash"},
    {"name": "BCA", "type": "bank"},
    {"name": "Mandiri", "type": "bank"},
    {"name": "Gopay", "type": "ewallet"},
    {"name": "OVO", "type": "ewallet"},
    {"name": "ShopeePay", "type": "ewallet"}
]

mock_categories = [
    {"name": "Makanan", "emoji": "🍔", "color": "#ff79c6"},
    {"name": "Transportasi", "emoji": "🚗", "color": "#8be9fd"},
    {"name": "Kebutuhan Bulanan", "emoji": "🛒", "color": "#50fa7b"},
    {"name": "Kebutuhan Bayi", "emoji": "👶", "color": "#ffb86c"},
    {"name": "Hiburan", "emoji": "🎬", "color": "#bd93f9"},
    {"name": "Transfer", "emoji": "🔄", "color": "#0ea5e9"},
    {"name": "Pendapatan", "emoji": "💰", "color": "#50fa7b"},
    {"name": "Saldo Awal", "emoji": "🏁", "color": "#6272a4"},
    {"name": "Lain-lain", "emoji": "📦", "color": "#ff5555"}
]

def upload_receipt(file_bytes: bytes, file_name: str, content_type: str = "image/jpeg") -> str:
    """
    Uploads a receipt image to the 'receipts' bucket in Supabase Storage.
    Returns the public URL. If storage fails or client is mock, returns fallback URL.
    """
    if not _has_supabase_config:
        print("Mock Mode: upload_receipt called. Returning dummy placeholder image.")
        return "https://images.unsplash.com/photo-1554415707-6e8cfc93fe23?w=500"

    client = get_client()
    try:
        ext = file_name.split(".")[-1] if "." in file_name else "jpg"
        unique_name = f"{uuid.uuid4()}.{ext}"
        
        # Try to upload file
        client.storage.from_("receipts").upload(
            path=unique_name,
            file=file_bytes,
            file_options={"content-type": content_type}
        )
        
        # Get public URL
        public_url = client.storage.from_("receipts").get_public_url(unique_name)
        return public_url
    except Exception as e:
        print(f"Error uploading receipt to Supabase storage: {e}")
        return ""

def get_transactions(month: str = None):
    """
    Get all transactions. If month is provided (format YYYY-MM),
    filter transactions for that month.
    """
    if not _has_supabase_config:
        # Sort local mock transactions descending by date and created_at
        res = sorted(mock_transactions, key=lambda t: (t["date"], t.get("created_at", "")), reverse=True)
        if month:
            res = [t for t in res if t["date"].startswith(month)]
        return res

    def run_query(client):
        query = client.table("transactions").select("*").order("date", desc=True).order("created_at", desc=True)
        if month:
            start_date = f"{month}-01"
            year, m = map(int, month.split("-"))
            if m == 12:
                end_date = f"{year+1}-01-01"
            else:
                end_date = f"{year}-{m+1:02d}-01"
            query = query.gte("date", start_date).lt("date", end_date)
        return query.execute()

    res = execute_with_retry(run_query)
    return res.data

def create_transaction(data: dict):
    if not _has_supabase_config:
        # In-memory save
        new_tx = data.copy()
        new_tx["id"] = str(uuid.uuid4())
        new_tx["created_at"] = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        mock_transactions.append(new_tx)
        print(f"Mock Mode: Transaction created successfully: {new_tx['merchant']}")
        return new_tx

    res = execute_with_retry(lambda c: c.table("transactions").insert(data).execute())
    return res.data[0] if res.data else None

def delete_transaction(transaction_id: str):
    if not _has_supabase_config:
        global mock_transactions
        mock_transactions = [t for t in mock_transactions if t["id"] != transaction_id]
        print(f"Mock Mode: Deleted transaction: {transaction_id}")
        return [{"id": transaction_id}]

    res = execute_with_retry(lambda c: c.table("transactions").delete().eq("id", transaction_id).execute())
    return res.data

def update_transaction(tx_id: str, merchant: str, date: str, category: str, payment_source: str, amount: float, user_name: str, items: list = None, receipt_url: str = None, transfer_to: str = None):
    if not _has_supabase_config:
        for idx, t in enumerate(mock_transactions):
            if t.get("id") == tx_id or str(t.get("id")) == tx_id:
                mock_transactions[idx] = {
                    "id": tx_id,
                    "created_at": t.get("created_at"),
                    "merchant": merchant,
                    "date": date,
                    "category": category,
                    "payment_source": payment_source,
                    "amount": amount,
                    "user_name": user_name,
                    "items": items or [],
                    "receipt_url": receipt_url or t.get("receipt_url"),
                    "transfer_to": transfer_to
                }
                print(f"Mock Mode: Updated transaction: {tx_id}")
                return mock_transactions[idx]
        return None

    data = {
        "merchant": merchant,
        "date": date,
        "category": category,
        "payment_source": payment_source,
        "amount": amount,
        "user_name": user_name,
        "items": items or [],
        "receipt_url": receipt_url,
        "transfer_to": transfer_to
    }
    res = execute_with_retry(lambda c: c.table("transactions").update(data).eq("id", tx_id).execute())
    return res.data[0] if res.data else None

def get_budget(month: str):
    """
    Get budget for a specific month (YYYY-MM).
    If no budget exists, return None.
    """
    if not _has_supabase_config:
        return mock_budgets.get(month)

    res = execute_with_retry(lambda c: c.table("budgets").select("*").eq("month", month).execute())
    return res.data[0] if res.data else None

def set_budget(month: str, amount: float, income: float = 0.0):
    if not _has_supabase_config:
        mock_budgets[month] = {"month": month, "amount": amount, "income": income}
        print(f"Mock Mode: Budget for {month} set to {amount}, income to {income}")
        return mock_budgets[month]

    existing = get_budget(month)
    if existing:
        res = execute_with_retry(lambda c: c.table("budgets").update({"amount": amount, "income": income}).eq("month", month).execute())
    else:
        res = execute_with_retry(lambda c: c.table("budgets").insert({"month": month, "amount": amount, "income": income}).execute())
    return res.data[0] if res.data else None

def sort_sources(sources_list):
    type_order = {'cash': 0, 'bank': 1, 'ewallet': 2}
    return sorted(sources_list, key=lambda x: (type_order.get(x.get('type', ''), 3), x.get('name', '').lower()))

def get_payment_sources():
    if not _has_supabase_config:
        return sort_sources(mock_payment_sources)
    try:
        res = execute_with_retry(lambda c: c.table("payment_sources").select("*").execute())
        return sort_sources(res.data or [])
    except Exception as e:
        print(f"Error fetching payment_sources table: {e}. Falling back to mock sources.")
        return sort_sources(mock_payment_sources)

def create_payment_source(name: str, type: str):
    if not _has_supabase_config:
        new_source = {"name": name, "type": type}
        mock_payment_sources.append(new_source)
        print(f"Mock Mode: Created payment source: {name} ({type})")
        return new_source
    try:
        res = execute_with_retry(lambda c: c.table("payment_sources").insert({"name": name, "type": type}).execute())
        return res.data[0] if res.data else None
    except Exception as e:
        print(f"Error creating payment source in Supabase: {e}. Saving locally in mock fallback.")
        new_source = {"name": name, "type": type}
        mock_payment_sources.append(new_source)
        return new_source
def get_categories():
    if not _has_supabase_config:
        return mock_categories
    try:
        res = execute_with_retry(lambda c: c.table("categories").select("*").order("name").execute())
        return res.data
    except Exception as e:
        print(f"Error fetching categories table: {e}. Falling back to mock categories.")
        return mock_categories

def create_category(name: str, emoji: str = "📦", color: str = "#ff5555"):
    if not _has_supabase_config:
        new_cat = {"name": name, "emoji": emoji, "color": color}
        mock_categories.append(new_cat)
        print(f"Mock Mode: Created category: {name}")
        return new_cat
    try:
        res = execute_with_retry(lambda c: c.table("categories").insert({"name": name, "emoji": emoji, "color": color}).execute())
        return res.data[0] if res.data else None
    except Exception as e:
        print(f"Error creating category in Supabase: {e}. Saving locally in mock fallback.")
        new_cat = {"name": name, "emoji": emoji, "color": color}
        mock_categories.append(new_cat)
        return new_cat
def get_balances():
    """
    Calculate current balance for all payment sources based on all transactions.
    """
    # Get registered payment sources
    sources = get_payment_sources()
    balances = {s["name"]: 0.0 for s in sources}

    if not _has_supabase_config:
        txs = mock_transactions
    else:
        res = execute_with_retry(lambda c: c.table("transactions").select("category, payment_source, transfer_to, amount").execute())
        txs = res.data or []

    for t in txs:
        cat = t.get("category")
        source = t.get("payment_source")
        dest = t.get("transfer_to")
        amount = float(t.get("amount") or 0.0)

        # Standardize source name capitalization
        if source:
            source = source.strip()
            # Find matching case-insensitive key
            matched_key = next((k for k in balances.keys() if k.lower() == source.lower()), None)
            if matched_key:
                source = matched_key
            else:
                balances[source] = 0.0

        if dest:
            dest = dest.strip()
            matched_key = next((k for k in balances.keys() if k.lower() == dest.lower()), None)
            if matched_key:
                dest = matched_key
            else:
                balances[dest] = 0.0

        if cat in ("Pendapatan", "Saldo Awal"):
            if source:
                balances[source] += amount
        elif cat == "Transfer":
            if source:
                balances[source] -= amount
            if dest:
                balances[dest] += amount
        else:
            # Regular expense
            if source:
                balances[source] -= amount

    return balances

def get_cumulative_net_balance(selected_month: str):
    """
    Calculate the cumulative net balance up to the selected month.
    """
    # 1. Parse selected month to find end_date
    year, m = map(int, selected_month.split("-"))
    if m == 12:
        end_date = f"{year+1}-01-01"
    else:
        end_date = f"{year}-{m+1:02d}-01"
        
    # 2. Get all transactions up to end_date
    if not _has_supabase_config:
        all_txs = [t for t in mock_transactions if t["date"] < end_date]
        budgets = list(mock_budgets.values())
    else:
        res = execute_with_retry(lambda c: c.table("transactions").select("*").lt("date", end_date).execute())
        all_txs = res.data
        res_b = execute_with_retry(lambda c: c.table("budgets").select("*").lte("month", selected_month).execute())
        budgets = res_b.data

    # Map budget planned incomes
    budget_map = {b["month"]: float(b["income"]) for b in budgets if "income" in b}
    
    # 3. Group transactions by month (YYYY-MM)
    txs_by_month = {}
    for tx in all_txs:
        tx_month = tx["date"][:7] # Get YYYY-MM
        if tx_month <= selected_month:
            if tx_month not in txs_by_month:
                txs_by_month[tx_month] = []
            txs_by_month[tx_month].append(tx)
            
    # Include selected_month in grouping even if empty
    if selected_month not in txs_by_month:
        txs_by_month[selected_month] = []
        
    # 4. For each month up to selected_month, calculate monthly net
    cumulative_net = 0.0
    all_months = sorted(list(txs_by_month.keys()))
    
    for month_str in all_months:
        month_txs = txs_by_month[month_str]
        
        # Actual income in month_str
        act_income = sum(float(t["amount"]) for t in month_txs if t.get("category") in ("Pendapatan", "Saldo Awal"))
        
        # Planned income from budget table
        plan_income = budget_map.get(month_str, 0.0)
        
        # Display income
        m_income = act_income if act_income > 0.0 else plan_income
        
        # Total spent
        m_spent = sum(float(t["amount"]) for t in month_txs if t.get("category") not in ("Transfer", "Pendapatan", "Saldo Awal"))
        
        cumulative_net += (m_income - m_spent)
        
    return cumulative_net

def get_dashboard_summary(month: str):
    """
    Retrieve financial summary for the dashboard.
    """
    # Get budget
    budget_data = get_budget(month)
    budget_amount = float(budget_data["amount"]) if budget_data else 0.0
    income_amount = float(budget_data["income"]) if budget_data and "income" in budget_data else 0.0
    
    # Get all transactions for the month
    txs = get_transactions(month)
    
    # Calculate actual income from transactions categorized as 'Pendapatan' or 'Saldo Awal'
    actual_income = sum(float(t["amount"]) for t in txs if t.get("category") in ("Pendapatan", "Saldo Awal"))
    display_income = actual_income if actual_income > 0.0 else income_amount
    
    # Exclude transfers, income, and Saldo Awal from total spent
    total_spent = sum(float(t["amount"]) for t in txs if t.get("category") not in ("Transfer", "Pendapatan", "Saldo Awal"))
    
    # Breakdown by category
    categories_breakdown = {}
    # Breakdown by payment source
    sources_breakdown = {}
    # Breakdown by user
    users_breakdown = {"Suami": 0.0, "Istri": 0.0}
    
    for t in txs:
        # Skip transfers, income, and Saldo Awal in category/spent breakdown
        if t.get("category") in ("Transfer", "Pendapatan", "Saldo Awal"):
            continue
            
        cat = t.get("category") or "Lain-lain"
        amount = float(t["amount"])
        categories_breakdown[cat] = categories_breakdown.get(cat, 0.0) + amount
        
        source = t.get("payment_source") or "Cash"
        sources_breakdown[source] = sources_breakdown.get(source, 0.0) + amount
        
        user = t.get("user_name") or "Suami"
        users_breakdown[user] = users_breakdown.get(user, 0.0) + amount
        
    return {
        "month": month,
        "budget": budget_amount,
        "income": display_income,
        "total_spent": total_spent,
        "remaining": budget_amount - total_spent,
        "net_balance": get_cumulative_net_balance(month),
        "categories": categories_breakdown,
        "sources": sources_breakdown,
        "users": users_breakdown,
        "balances": get_balances(),  # Return cumulative balances
        "recent_transactions": txs[:10]  # Limit to top 10
    }

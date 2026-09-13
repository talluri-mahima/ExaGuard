"""
ExaGuard - Minimal FastAPI service
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
import pyexasol
from datetime import datetime
import hashlib
import json

load_dotenv()

app = FastAPI(title="ExaGuard API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DSN = os.getenv("EXASOL_DSN", "localhost:8563")
USER = os.getenv("EXASOL_USER", "SYS")
PASSWORD = os.getenv("EXASOL_PASSWORD", "")
SCHEMA = os.getenv("EXASOL_SCHEMA", "EXAGUARD")

def get_connection():
    return pyexasol.connect(dsn=DSN, user=USER, password=PASSWORD, schema=SCHEMA)

@app.get("/")
def root():
    return {"message": "ExaGuard API is running", "status": "ok"}

@app.get("/api/v1/health")
def health():
    try:
        conn = get_connection()
        result = conn.execute("SELECT COUNT(*) FROM transactions").fetchone()
        conn.close()
        return {"status": "healthy", "transactions": result[0]}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

@app.get("/api/v1/accounts")
def list_accounts(limit: int = 20):
    conn = get_connection()
    rows = conn.execute(f"SELECT * FROM accounts LIMIT {limit}").fetchall()
    columns = [c[0] for c in conn.columns]
    conn.close()
    return [dict(zip(columns, row)) for row in rows]

@app.get("/api/v1/transactions")
def list_transactions(limit: int = 50):
    conn = get_connection()
    rows = conn.execute(f"SELECT * FROM transactions ORDER BY TS DESC LIMIT {limit}").fetchall()
    columns = [c[0] for c in conn.columns]
    conn.close()
    return [dict(zip(columns, row)) for row in rows]

@app.post("/api/v1/detect")
def run_detection():
    """Very simple topology detection example"""
    conn = get_connection()

    # Example: find accounts with high outgoing activity
    query = """
    SELECT SRC_ACCT, COUNT(*) as txn_count, SUM(AMOUNT) as total_amount
    FROM transactions
    GROUP BY SRC_ACCT
    HAVING COUNT(*) > 5
    ORDER BY txn_count DESC
    LIMIT 10
    """
    rows = conn.execute(query).fetchall()

    evidence_list = []
    for i, row in enumerate(rows):
        evidence_id = f"EVD-{i+1:03d}"
        payload = {
            "account": row[0],
            "txn_count": row[1],
            "total_amount": float(row[2])
        }
        hash_val = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()

        conn.execute(
            """
            INSERT INTO evidence (EVIDENCE_ID, RING_ID, TYPOLOGY, ACCOUNT_LIST, TXN_LIST, HASH)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (evidence_id, f"R{i+1:03d}", "HIGH_ACTIVITY", row[0], str(row[1]), hash_val)
        )
        evidence_list.append({"evidence_id": evidence_id, "account": row[0], "hash": hash_val})

    conn.commit()
    conn.close()
    return {"detected": len(evidence_list), "evidence": evidence_list}

@app.get("/api/v1/evidence")
def get_evidence():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM evidence ORDER BY CREATED_TS DESC").fetchall()
    columns = [c[0] for c in conn.columns]
    conn.close()
    return [dict(zip(columns, row)) for row in rows]
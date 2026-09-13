"""
Load generated synthetic data into Exasol Personal.
"""
import os
from pathlib import Path
import pandas as pd
from dotenv import load_dotenv
import pyexasol

load_dotenv()

DSN = os.getenv("EXASOL_DSN", "localhost:8563")
USER = os.getenv("EXASOL_USER", "SYS")
PASSWORD = os.getenv("EXASOL_PASSWORD", "")
SCHEMA = os.getenv("EXASOL_SCHEMA", "EXAGUARD")

def main():
    data_dir = Path("data/generated")
    if not data_dir.exists():
        print("ERROR: data/generated folder not found.")
        print("First run: py -m data.generate_dataset --rows 20000 --accounts 5000 --out data/generated")
        return

    print(f"Connecting to Exasol at {DSN} ...")
    conn = pyexasol.connect(dsn=DSN, user=USER, password=PASSWORD, schema=SCHEMA)

    # Create schema and tables
    schema_sql = Path("sql/schema.sql").read_text(encoding="utf-8")
    for statement in schema_sql.split(";"):
        stmt = statement.strip()
        if stmt:
            try:
                conn.execute(stmt)
            except Exception as e:
                print(f"Note: {e}")

    print("Loading accounts...")
    accounts = pd.read_csv(data_dir / "accounts.csv")
    conn.import_from_pandas(accounts, (SCHEMA, "accounts"))

    print("Loading transactions...")
    transactions = pd.read_csv(data_dir / "transactions.csv")
    conn.import_from_pandas(transactions, (SCHEMA, "transactions"))

    print("Done! Data loaded into Exasol.")
    conn.close()

if __name__ == "__main__":
    main()
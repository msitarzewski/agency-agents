"""
Migrate legacy paper_accounts documents where 'cash' or 'realized_pnl' are scalars
to a multi-currency object structure: {'CNY': ..., 'HKD': 0.0, 'USD': 0.0}.

Idempotent: safe to run multiple times; only updates records with scalar fields.

Usage:
    python scripts/migration/migrate_paper_accounts_cash_structure.py

Environment variables:
    MONGO_URI: e.g. mongodb://user:pass@host:27017
    MONGODB_DATABASE or MONGO_DB: database name
"""

import os
import sys
from datetime import datetime

from pymongo import MongoClient


def get_mongo_params():
    uri = os.environ.get("MONGO_URI") or os.environ.get("MONGODB_URI") or "mongodb://localhost:27017"
    db_name = (
        os.environ.get("MONGODB_DATABASE")
        or os.environ.get("MONGO_DB")
        or os.environ.get("MONGODB_DB")
        or "tradingagents"
    )
    return uri, db_name


def is_scalar(value):
    return isinstance(value, (int, float))


def migrate_one(doc, coll):
    updates = {}
    cash = doc.get("cash")
    pnl = doc.get("realized_pnl")

    if is_scalar(cash):
        updates["cash"] = {"CNY": float(cash or 0.0), "HKD": 0.0, "USD": 0.0}

    if is_scalar(pnl):
        updates["realized_pnl"] = {"CNY": float(pnl or 0.0), "HKD": 0.0, "USD": 0.0}

    if updates:
        updates["updated_at"] = datetime.utcnow().isoformat()
        coll.update_one({"_id": doc["_id"]}, {"$set": updates})
        return True, updates
    return False, {}


def main():
    uri, db_name = get_mongo_params()
    print(f"Connecting to MongoDB: uri={uri}, db={db_name}")
    client = MongoClient(uri)
    db = client[db_name]
    coll = db["paper_accounts"]

    # Find candidates: either cash or realized_pnl not an object
    # We filter in Python for clarity/idempotency
    total = 0
    migrated = 0

    for doc in coll.find({}, {"cash": 1, "realized_pnl": 1}):
        total += 1
        changed, updates = migrate_one(doc, coll)
        if changed:
            migrated += 1
            print(f"Migrated _id={doc['_id']}: {updates}")

    print(f"Done. Scanned={total}, migrated={migrated}")


if __name__ == "__main__":
    try:
        main()
        sys.exit(0)
    except Exception as e:
        print(f"Migration failed: {e}")
        sys.exit(1)
import asyncio
from app.core.config import settings
from app.services.data_sources.manager import DataSourceManager
from app.core.database import init_db, get_mongo_db, close_db
from app.services.quotes_ingestion_service import QuotesIngestionService

async def main():
    print("Settings:")
    print("  QUOTES_BACKFILL_ON_STARTUP=", settings.QUOTES_BACKFILL_ON_STARTUP)
    print("  QUOTES_BACKFILL_ON_OFFHOURS=", settings.QUOTES_BACKFILL_ON_OFFHOURS)

    m = DataSourceManager()
    available = [a.name for a in m.get_available_adapters()]
    print("Available adapters:", available)

    await init_db()
    db = get_mongo_db()
    coll = db["market_quotes"]
    try:
        n = await coll.estimated_document_count()
    except Exception as e:
        print("Count error:", e)
        n = None
    print("Before backfill, doc count =", n)

    svc = QuotesIngestionService()
    await svc.ensure_indexes()
    await svc.backfill_last_close_snapshot_if_needed()

    try:
        n2 = await coll.estimated_document_count()
    except Exception as e:
        print("Count2 error:", e)
        n2 = None
    print("After backfill, doc count =", n2)

    try:
        docs = await coll.find({}, {'_id':0,'code':1,'close':1,'pct_chg':1,'amount':1,'trade_date':1,'updated_at':1}).sort('updated_at', -1).limit(5).to_list(length=5)
        print("Sample docs:")
        for d in docs:
            print(d)
    except Exception as e:
        print("Fetch sample error:", e)

    await close_db()

if __name__ == "__main__":
    asyncio.run(main())


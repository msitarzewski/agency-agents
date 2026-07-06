import asyncio


def test_database_screening_builds_roe_query():
    from app.services.database_screening_service import DatabaseScreeningService

    svc = DatabaseScreeningService()

    async def _run():
        query = await svc._build_query([
            {"field": "roe", "operator": "between", "value": [10, 20]},
        ])
        # Should map to direct 'roe' field with $gte/$lte
        assert "roe" in query
        assert query["roe"]["$gte"] == 10
        assert query["roe"]["$lte"] == 20

    asyncio.run(_run())


def test_database_screening_formats_roe_in_result(monkeypatch):
    from app.services.database_screening_service import DatabaseScreeningService
    import app.services.database_screening_service as mod

    # Fake collection returning docs that contain 'roe'
    class _FakeCursor:
        def __init__(self, docs):
            self._docs = docs
        def sort(self, *_args, **_kwargs):
            return self
        def skip(self, *_args, **_kwargs):
            return self
        def limit(self, *_args, **_kwargs):
            return self
        async def __aiter__(self):
            for d in self._docs:
                yield d

    class _FakeColl:
        def __init__(self, docs):
            self._docs = docs
        async def count_documents(self, _query):
            return len(self._docs)
        def find(self, _query):
            return _FakeCursor(self._docs)

    class _FakeDB:
        def __init__(self, docs):
            self._coll = _FakeColl(docs)
        def __getitem__(self, name: str):
            return self._coll

    docs = [
        {"code": "000001", "name": "平安银行", "roe": 12.3},
        {"code": "600000", "name": "浦发银行", "roe": 8.9},
    ]

    def _fake_get_db():
        return _FakeDB(docs)

    monkeypatch.setattr(mod, "get_mongo_db", _fake_get_db, raising=True)

    async def _run():
        svc = DatabaseScreeningService()
        items, total = await svc.screen_stocks(
            conditions=[{"field": "roe", "operator": ">=", "value": 5}],
            limit=50,
            offset=0,
            order_by=None,
        )
        assert total == 2
        # Ensure roe is present in formatted result
        by_code = {it["code"]: it for it in items}
        assert by_code["000001"]["roe"] == 12.3
        assert by_code["600000"]["roe"] == 8.9

    asyncio.run(_run())


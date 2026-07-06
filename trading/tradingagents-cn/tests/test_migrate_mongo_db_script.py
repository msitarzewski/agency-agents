import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from app.scripts.migrate_mongo_db import (
    DEFAULT_EXCLUDED_COLLECTIONS,
    _build_since_query,
    _iter_collections,
    _parse_since,
    _write_summary_json,
    main,
)


class _FakeDb:
    def __init__(self, names):
        self._names = names

    def list_collection_names(self):
        return list(self._names)


class MigrateMongoDbScriptTests(unittest.TestCase):
    def test_parse_since(self):
        parsed = _parse_since("2026-01-02T03:04:05")
        self.assertEqual(parsed.year, 2026)
        self.assertEqual(parsed.month, 1)

    def test_build_since_query(self):
        since = _parse_since("2026-01-02T03:04:05")
        query = _build_since_query(since)
        self.assertIn("$or", query)
        self.assertEqual(len(query["$or"]), 4)

    def test_iter_collections_respects_include_and_exclude(self):
        db = _FakeDb(["llm_providers", "system_configs", "historical_data"])
        names = _iter_collections(db, {"llm_providers", "historical_data"}, {"historical_data"})
        self.assertEqual(names, ["llm_providers"])

    def test_default_excluded_contains_large_collections(self):
        self.assertIn("historical_data", DEFAULT_EXCLUDED_COLLECTIONS)
        self.assertIn("analysis_tasks", DEFAULT_EXCLUDED_COLLECTIONS)

    def test_show_default_excludes_returns_success(self):
        self.assertEqual(main(["--show-default-excludes"]), 0)

    def test_write_summary_json(self):
        with TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "summary.json"
            _write_summary_json(str(output), {"ok": True, "count": 2})
            self.assertTrue(output.exists())
            self.assertIn('"ok": true', output.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()

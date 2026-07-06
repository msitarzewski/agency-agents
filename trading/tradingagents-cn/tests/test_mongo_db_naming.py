import os
import unittest


class MongoDbNamingTests(unittest.TestCase):
    def test_auto_scope_debug_uses_major_instance(self):
        from app.core.config import Settings

        env = {
            "DEBUG": "true",
            "MONGODB_DATABASE": "tradingagentscn",
            "MONGODB_DATABASE_SCOPE": "auto",
            "TRADINGAGENTS_VERSION": "1.2.3",
            "MONGODB_DATABASE_INSTANCE": "devx",
        }

        old = {k: os.environ.get(k) for k in env}
        try:
            os.environ.update(env)
            s = Settings()
            self.assertEqual(s.MONGO_DB, "tradingagentscn_v1_devx")
            identity = s.MONGO_DB_IDENTITY
            self.assertEqual(identity["scope_effective"], "major_instance")
            self.assertEqual(identity["major_version"], "1")
        finally:
            for k, v in old.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v

    def test_auto_scope_prod_uses_explicit(self):
        from app.core.config import Settings

        env = {
            "DEBUG": "false",
            "MONGODB_DATABASE": "tradingagentscn",
            "MONGODB_DATABASE_SCOPE": "auto",
            "TRADINGAGENTS_VERSION": "9.0.0",
        }

        old = {k: os.environ.get(k) for k in env}
        try:
            os.environ.update(env)
            s = Settings()
            self.assertEqual(s.MONGO_DB, "tradingagentscn")
            identity = s.MONGO_DB_IDENTITY
            self.assertEqual(identity["scope_effective"], "explicit")
        finally:
            for k, v in old.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v

    def test_debug_shared_db_requires_explicit_override(self):
        from app.core.config import Settings

        env = {
            "DEBUG": "true",
            "MONGODB_DATABASE": "tradingagentscn",
            "MONGODB_DATABASE_SCOPE": "explicit",
            "ALLOW_SHARED_DB_IN_DEBUG": "false",
        }

        old = {k: os.environ.get(k) for k in env}
        try:
            os.environ.update(env)
            s = Settings()
            self.assertEqual(s.MONGO_DB_IDENTITY["scope_effective"], "explicit")
            self.assertFalse(s.ALLOW_SHARED_DB_IN_DEBUG)
        finally:
            for k, v in old.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v


if __name__ == "__main__":
    unittest.main()

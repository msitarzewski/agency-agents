from app.core.config import Settings


def test_settings_defaults_and_env_override(monkeypatch):
    # Override a few env vars
    monkeypatch.setenv("PORT", "8123")
    monkeypatch.setenv("DEBUG", "false")
    monkeypatch.setenv("MONGODB_USERNAME", "user")
    monkeypatch.setenv("MONGODB_PASSWORD", "pass")
    monkeypatch.setenv("MONGODB_HOST", "dbhost")
    monkeypatch.setenv("MONGODB_PORT", "27018")
    monkeypatch.setenv("MONGODB_DATABASE", "testdb")
    monkeypatch.setenv("MONGODB_AUTH_SOURCE", "admin")

    s = Settings()  # instantiate fresh to pick up env

    assert s.PORT == 8123
    assert s.DEBUG is False

    # URI should include credentials when provided
    uri = s.MONGO_URI
    assert uri.startswith("mongodb://user:pass@dbhost:27018/")
    assert uri.endswith("testdb?authSource=admin")


def test_redis_url_builds(monkeypatch):
    # Without password
    monkeypatch.setenv("REDIS_HOST", "127.0.0.1")
    monkeypatch.setenv("REDIS_PORT", "6379")
    monkeypatch.setenv("REDIS_DB", "2")
    # Ensure no password from .env leaks into this test
    monkeypatch.setenv("REDIS_PASSWORD", "")

    s = Settings()
    assert s.REDIS_URL == "redis://127.0.0.1:6379/2"

    # With password
    monkeypatch.setenv("REDIS_PASSWORD", "p@ss")
    s = Settings()
    assert s.REDIS_URL == "redis://:p@ss@127.0.0.1:6379/2"


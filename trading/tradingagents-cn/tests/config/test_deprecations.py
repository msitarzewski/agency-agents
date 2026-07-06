import importlib
import warnings


def test_legacy_env_aliases_map_to_new(monkeypatch):
    # Ensure new keys are not set so aliasing triggers
    monkeypatch.delenv("HOST", raising=False)
    monkeypatch.delenv("PORT", raising=False)
    monkeypatch.delenv("DEBUG", raising=False)

    # Set only legacy keys
    monkeypatch.setenv("API_HOST", "127.0.0.1")
    monkeypatch.setenv("API_PORT", "8123")
    monkeypatch.setenv("API_DEBUG", "false")

    # Reload module under warning capture to assert deprecation warnings
    import app.core.config as cfg
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always", DeprecationWarning)
        importlib.reload(cfg)

    # At least one deprecation warning should be emitted
    assert any(isinstance(x.message, DeprecationWarning) for x in w), "No DeprecationWarning captured"

    # Verify values are mapped correctly
    s = cfg.Settings()
    assert s.HOST == "127.0.0.1"
    assert s.PORT == 8123
    assert s.DEBUG is False


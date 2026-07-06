from importlib import reload
import logging


def test_json_console_formatter_enabled(monkeypatch, tmp_path):
    # Arrange: TOML with json flag
    cfg_dir = tmp_path / "config"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    (cfg_dir / "logging.toml").write_text(
        """
[logging]
level = "INFO"

[logging.format]
json = true
        """.strip(),
        encoding="utf-8",
    )

    # Set CWD to temp
    monkeypatch.chdir(tmp_path)

    # Import module fresh
    from app.core import logging_config as lc
    reload(lc)

    # Act
    lc.setup_logging("INFO")

    # Assert: console handler uses SimpleJsonFormatter
    logger = logging.getLogger("webapi")
    # find console handler
    console_handlers = [h for h in logger.handlers if isinstance(h, logging.StreamHandler)]
    assert console_handlers, "no console handler found"
    formatter_names = {h.formatter.__class__.__name__ for h in console_handlers if h.formatter}
    assert "SimpleJsonFormatter" in formatter_names


import re
import logging
import io
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.middleware.request_id import RequestIDMiddleware
from app.core.logging_config import setup_logging
from app.core.logging_context import LoggingContextFilter


UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")


def create_app():
    app = FastAPI()
    app.add_middleware(RequestIDMiddleware)

    @app.get("/t")
    async def t():
        logging.getLogger("webapi").info("trace test log")
        return {"ok": True}

    return app


def test_trace_id_header_and_logging():
    # Arrange
    setup_logging("INFO")
    app = create_app()
    client = TestClient(app)

    # Attach a temporary stream handler to capture only webapi logs with trace_id
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setLevel(logging.INFO)
    handler.addFilter(LoggingContextFilter())
    handler.setFormatter(logging.Formatter("%(trace_id)s|%(message)s"))

    logger = logging.getLogger("webapi")
    logger.addHandler(handler)

    try:
        # Act
        resp = client.get("/t")

        # Assert headers
        trace_id = resp.headers.get("X-Trace-ID")
        assert trace_id and UUID_RE.match(trace_id)
        assert resp.headers.get("X-Request-ID") == trace_id

        # Assert our captured log contains trace_id
        output = stream.getvalue()
        assert f"{trace_id}|trace test log" in output
    finally:
        logger.removeHandler(handler)
        handler.close()


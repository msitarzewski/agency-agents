# syntax=docker/dockerfile:1.6
#
# Build:  docker build -f runtime/Dockerfile -t agency-runtime .
# Serve:  docker run --rm -p 8765:8765 -e ANTHROPIC_API_KEY=... agency-runtime
# CLI:    docker run --rm -e ANTHROPIC_API_KEY=... agency-runtime agency list

FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Copy the whole repo — the runtime loads persona files from the other
# category directories at import time.
COPY . /app/

RUN pip install --upgrade pip \
 && pip install -e /app/runtime

EXPOSE 8765

# Default to the web UI; override the CMD to run the CLI instead.
CMD ["agency", "serve", "--host", "0.0.0.0", "--port", "8765"]

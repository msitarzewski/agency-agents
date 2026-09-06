FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

# The xct-agents repo must be mounted at /agents-repo at runtime
ENV AGENTS_REPO_PATH=/agents-repo
ENV LITELLM_API_BASE=http://litellm:4000
ENV LITELLM_API_KEY=sk-1234
ENV DEFAULT_MODEL=deepseek-v3.2

EXPOSE 9000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "9000"]

FROM python:3.11-slim

WORKDIR /app

# Install uv (fast pip replacement)
RUN pip install --no-cache-dir uv

# Install Python dependencies
COPY pyproject.toml .
RUN uv pip install --system --no-cache .

# Copy application source
COPY . .

EXPOSE 8000

CMD ["sh", "-c", \
  "python app/backend_pre_start.py && \
  uvicorn app.main:app --host 0.0.0.0 --port 8000"]

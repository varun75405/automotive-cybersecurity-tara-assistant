FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Copy .env.example as default .env if not exists
RUN cp -n .env.example .env 2>/dev/null || true

# Create data directories
RUN mkdir -p data/chroma_db data/sqlite data/exports

# Expose ports
EXPOSE 8000 8501

# Start both backend and frontend
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port 8000 & streamlit run frontend/streamlit_app.py --server.port 8501 --server.address 0.0.0.0"]

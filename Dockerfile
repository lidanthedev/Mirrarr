FROM python:3.14-slim-bookworm

# Install uv from the official image
COPY --from=ghcr.io/astral-sh/uv:0.9.7 /uv /bin/uv

WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
# --frozen: Sync with uv.lock exactly
# --no-install-project: Install only dependencies, not the project itself yet
RUN uv sync --frozen --no-install-project --no-dev

# Copy application code
COPY . .

# Install the project itself
RUN uv sync --frozen --no-dev

# Place the virtual environment path in the PATH
ENV PATH="/app/.venv/bin:$PATH"

# Create directories for mounted volumes
RUN mkdir -p /app/downloads /app/data

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

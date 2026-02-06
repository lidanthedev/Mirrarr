---
description: Initialize and run the Mirarr application for development
---

# Mirarr Project Initialization

Mirarr is a Python FastAPI-based media streaming application that integrates with TMDB for movie/TV data and provides various streaming providers.

## Prerequisites

- Python 3.14+
- [uv](https://docs.astral.sh/uv/) package manager
- Redis server (for Celery task queue)
- TMDB API key (set in `.env` as `TMDB_API_KEY`)

## Project Structure

```
Mirarr/
├── app/                    # Main application package
│   ├── api/                # API routes (routes_api.py, routes_ui.py)
│   ├── core/               # Core config and database
│   ├── models/             # Data models (media.py)
│   ├── providers/          # Streaming providers
│   ├── services/           # Business logic (search, tmdb)
│   ├── static/             # Static assets
│   └── templates/          # Jinja2 templates
├── tests/                  # Test suite
├── main.py                 # Entry point script
└── pyproject.toml          # Project configuration
```

## Setup Steps

1. **Install dependencies** using uv:
// turbo
```bash
uv sync
```

2. **Ensure Redis is running** (required for Celery):
```bash
redis-cli ping
# Should return: PONG
```

3. **Configure environment variables** - ensure `.env` file contains:
```
TMDB_API_KEY=your_tmdb_api_key_here
```

## Running the Application

// turbo
4. **Start the FastAPI development server**:
```bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The application will be available at: http://localhost:8000

## Running Tests

// turbo
5. **Run the test suite**:
```bash
uv run pytest
```

## Key Dependencies

- **FastAPI** - Web framework
- **Uvicorn** - ASGI server
- **Jinja2** - Template engine
- **SQLModel** - Database ORM
- **Celery + Redis** - Task queue
- **Niquests** - HTTP client with HTTP/2 and HTTP/3 support
- **tmdbsimple** - TMDB API wrapper
- **Pydantic Settings** - Configuration management

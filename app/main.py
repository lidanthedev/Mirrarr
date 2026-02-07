"""Mirrarr - DDL PVR Application."""

from app.providers.vadapav_provider import VadapavProvider
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api.routes_ui import router as ui_router
from app.api.routes_api import router as api_router
from app.providers import register_provider
from app.providers.dummy_provider import DummyProvider
from app.providers.test_provider import TestProvider

load_dotenv()

# Paths
BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

# Initialize FastAPI
app = FastAPI(
    title="Mirrarr",
    description="A Sonarr-like PVR for Direct Download content",
    version="0.1.0",
)

# Mount static files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Initialize Jinja2 templates (shared across routers)
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# Register providers
register_provider(DummyProvider())
register_provider(TestProvider())
register_provider(VadapavProvider())

# Include routers
app.include_router(ui_router)
app.include_router(api_router, prefix="/api")

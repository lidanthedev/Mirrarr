## 1. Project Identity & Goal

* **Project Name:** Mirrarr
* **Description:** A "Sonarr-like" personal video recorder (PVR) for Direct Download (DDL) content.
* **Core Philosophy:** Modular "Provider" architecture with a lightweight, server-side rendered frontend.
* **User Interface:** Simple, functional dashboard using standard HTML/CSS, rendered server-side.

## 2. Technical Stack

* **Language:** Python 3.14+
* **Web Framework:** FastAPI (Async)
* **Templating:** **Jinja2** (Server-Side Rendering)
* **Interactivity:** **HTMX** (For AJAX replacements, polling progress bars, and search without page reloads).
* **Styling:** **TailwindCSS** (via CDN for simplicity) or Bootstrap.
* **Task Queue:** In python with thread pool.
* **Database:** SQLite (SQLModel).
* **Metadata:** TMDB API.

## 3. Architecture Rules

1. **Hybrid Routes:**
* **UI Routes:** Return `templates.TemplateResponse` (HTML).
* **API Routes:** Return JSON (consumed by HTMX or external tools).


2. **No Full Reloads:** Use HTMX to swap parts of the page (e.g., `<div id="search-results">`) instead of reloading the whole page.
3. **Provider Isolation:** The core logic must never know how a specific site works. It communicates strictly through the `ProviderInterface`.
4. **Task Offloading:** Searching and Downloading are **background tasks**. The UI should trigger them and then poll for status updates.

## 4. The Provider Interface (Contract)

*Remains unchanged. Providers should focus on data; the UI renders that data.*

```python
from abc import ABC, abstractmethod
from pydantic import BaseModel
from typing import List, Optional

class SearchResult(BaseModel):
    title: str
    size_mb: float
    download_url: str
    source_site: str

class ProviderInterface(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    async def get_movie(self, movie: Movie) -> List[MovieResult]:
        pass

    @abstractmethod
    async def get_series_episode(
        self,
        series: TVSeries,
        season: Season,
        episode: Episode,
    ) -> List[EpisodeResult]:
        pass


```

## 5. Directory Structure

Updated to include `templates` and `static` folders.

```text
/mirrarr
├── /app
│   ├── main.py              # FastAPI entry point (mounts static/templates)
│   ├── /api
│   │   ├── routes_api.py    # JSON endpoints (for HTMX/AJAX)
│   │   └── routes_ui.py     # HTML endpoints (Jinja2)
│   ├── /core
│   │   ├── config.py
│   │   └── database.py
│   ├── /models              # SQLModel Database Models
│   ├── /providers           # Plugin directory
│   │   ├── __init__.py
│   │   └── base.py
│   ├── /services            # Business logic
│   ├── /templates           # Jinja2 HTML files
│   │   ├── base.html        # Master layout (includes HTMX script)
│   │   ├── dashboard.html   # Main view
│   │   └── /partials        # Small HTML fragments for HTMX swaps
│   │       └── search_results.html
│   └── /static              # CSS, Images, JS
│       └── style.css
├── /tests
└── .env
```

## 6. Coding Style Guidelines

* **HTMX Pattern:** When an HTMX request comes in (e.g., "Search"), return a **HTML Partial** (just the `<li>` rows), not the full page, nor JSON.
* *Example:* `return templates.TemplateResponse("partials/search_results.html", {"request": request, "results": results})`


* **Error Handling:** UI routes should catch errors and render an "error.html" template or a toaster notification partial.

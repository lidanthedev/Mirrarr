"""Download Manager using yt_dlp with async queue processing."""

import os
import shutil
import re
import asyncio
import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import Any, TypedDict, NotRequired
from contextlib import asynccontextmanager

import yt_dlp


def _format_bytes(num_bytes: int | float) -> str:
    """Format bytes to human readable string."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if abs(num_bytes) < 1024.0:
            return f"{num_bytes:.1f} {unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:.1f} PB"


def _strip_ansi(text: str) -> str:
    """Strip ANSI escape codes from a string."""
    ansi_pattern = re.compile(r"\x1b\[[0-9;]*m")
    return ansi_pattern.sub("", text)


def _rename_downloaded_file(downloaded_file: str, custom_filename: str) -> str | None:
    """Rename a downloaded file to the custom filename, preserving extension.

    Returns the new path if successful, None otherwise.
    """
    if not downloaded_file or not os.path.exists(downloaded_file):
        return None

    # Sanitize custom_filename to prevent path traversal
    custom_filename = os.path.basename(custom_filename)
    # Allow only alphanumeric, underscores, hyphens, and dots
    custom_filename = re.sub(r"[^\w\.-]", "_", custom_filename)
    if not custom_filename:
        return None

    # Get directory and extension from downloaded file
    download_dir = os.path.dirname(downloaded_file)

    # Create new filename with proper extension
    new_path = os.path.join(download_dir, f"{custom_filename}")

    try:
        shutil.move(downloaded_file, new_path)
        print(f"Renamed: {downloaded_file} -> {new_path}")
        return new_path
    except Exception as rename_err:
        print(f"Failed to rename file: {rename_err}")
        return None


class DownloadStatus(TypedDict):
    """Structure for download progress tracking."""

    id: str
    url: str
    status: str  # 'queued', 'downloading', 'processing', 'completed', 'error'
    percent: str
    filename: NotRequired[str | None]
    title: NotRequired[str | None]
    speed: NotRequired[str | None]
    eta: NotRequired[str | None]
    total_bytes: NotRequired[str | None]
    error: NotRequired[str | None]
    metadata: NotRequired[dict[str, Any] | None]


class DownloadJob(TypedDict):
    """Structure for items in the queue."""

    id: str
    url: str
    opts: dict[str, Any]
    custom_filename: NotRequired[str | None]
    attempt: NotRequired[int]
    metadata: NotRequired[dict[str, Any] | None]


# Global state: mapping download IDs to their status
download_status: dict[str, DownloadStatus] = {}
# Private mapping for temporary filenames (not exposed in API)
_temp_filenames: dict[str, str] = {}


class DownloadManager:
    """Async download manager using yt_dlp with concurrent workers."""

    def __init__(self, max_concurrent_downloads: int = 2) -> None:
        self.queue: asyncio.Queue[DownloadJob] = asyncio.Queue()
        self.max_workers: int = max_concurrent_downloads
        self.executor: ThreadPoolExecutor = ThreadPoolExecutor(
            max_workers=max_concurrent_downloads
        )
        self._worker_tasks: list[asyncio.Task[None]] = []
        self._requeue_tasks: set[asyncio.Task] = set()

        # Default yt_dlp options
        self.default_opts: dict[str, Any] = {
            "outtmpl": "downloads/%(title)s.%(ext)s",
            "restrictfilenames": True,
            "retries": 20,
            "fragment_retries": 20,
            "skip_unavailable_fragments": False,
            "quiet": True,
            "noplaylist": True,
            "concurrent_fragment_downloads": 8,  # Speed up downloads
        }

    async def start_workers(self) -> None:
        """Start background workers to process the queue."""
        print(f"🚀 Starting {self.max_workers} download workers...")
        for i in range(self.max_workers):
            task = asyncio.create_task(self._worker(f"Worker-{i + 1}"))
            self._worker_tasks.append(task)

    async def shutdown(self) -> None:
        """Cancel all worker tasks and shut down the executor."""
        for task in self._worker_tasks:
            task.cancel()
        # Wait for all tasks to finish cancellation
        await asyncio.gather(*self._worker_tasks, return_exceptions=True)
        self._worker_tasks.clear()

        # Cancel any pending requeue tasks
        for task in self._requeue_tasks:
            task.cancel()
        if self._requeue_tasks:
            await asyncio.gather(*self._requeue_tasks, return_exceptions=True)
        self._requeue_tasks.clear()
        self.executor.shutdown(wait=False)

    async def _worker(self, worker_name: str) -> None:
        """Continuously pull tasks from the queue and process them."""
        while True:
            job: DownloadJob = await self.queue.get()

            download_id = job["id"]
            url = job["url"]
            custom_opts = job["opts"]
            custom_filename = job.get("custom_filename")
            attempt = job.get("attempt", 0)

            print(f"[{worker_name}] Starting: {url} (Attempt {attempt + 1})")

            if download_id in download_status:
                download_status[download_id]["status"] = "downloading"

            # Run blocking yt_dlp in thread pool
            loop = asyncio.get_running_loop()
            retry_delay = await loop.run_in_executor(
                self.executor,
                self._run_yt_dlp,
                url,
                download_id,
                custom_opts,
                custom_filename,
                attempt,
            )

            if retry_delay:
                # Re-queue the job after delay (non-blocking)
                task = asyncio.create_task(self._requeue_job(job, retry_delay))
                self._requeue_tasks.add(task)
                task.add_done_callback(self._requeue_tasks.discard)
            else:
                # Success or fatal error
                print(f"[{worker_name}] Finished: {url}")

            self.queue.task_done()

    async def _requeue_job(self, job: DownloadJob, delay: float) -> None:
        """Wait for delay then put job back in queue."""
        await asyncio.sleep(delay)
        job["attempt"] = job.get("attempt", 0) + 1
        await self.queue.put(job)

    def _run_yt_dlp(
        self,
        url: str,
        download_id: str,
        custom_opts: dict[str, Any],
        custom_filename: str | None = None,
        attempt: int = 0,
    ) -> float | None:
        """Run yt_dlp download (blocking). Returns retry delay in seconds if needed, else None."""

        def progress_hook(d: dict[str, Any]) -> None:
            if download_id not in download_status:
                return

            if d["status"] == "downloading":
                # Clean ANSI escape codes from percent string
                p = _strip_ansi(d.get("_percent_str", "0%"))

                download_status[download_id]["status"] = "downloading"
                download_status[download_id]["percent"] = p
                # Only update filename if no custom filename was set
                if not custom_filename:
                    download_status[download_id]["filename"] = d.get("filename")
                download_status[download_id]["speed"] = _strip_ansi(
                    d.get("_speed_str", "N/A")
                )
                download_status[download_id]["eta"] = _strip_ansi(
                    d.get("_eta_str", "N/A")
                )

                # Track file size
                total_bytes = d.get("total_bytes") or d.get("total_bytes_estimate")
                if total_bytes:
                    download_status[download_id]["total_bytes"] = _format_bytes(
                        total_bytes
                    )

            elif d["status"] == "finished":
                download_status[download_id]["status"] = "processing"
                # Store the actual downloaded filename for renaming
                _temp_filenames[download_id] = d.get("filename")
                total_bytes = d.get("total_bytes")
                if total_bytes:
                    download_status[download_id]["total_bytes"] = _format_bytes(
                        total_bytes
                    )

        # Merge options
        ydl_opts: dict[str, Any] = self.default_opts.copy()
        ydl_opts.update(custom_opts)

        # Attach progress hook
        current_hooks = ydl_opts.get("progress_hooks", [])
        if not isinstance(current_hooks, list):
            current_hooks = [current_hooks]
        current_hooks.append(progress_hook)
        ydl_opts["progress_hooks"] = current_hooks

        # Retry configuration for rate limits (exponential backoff)
        retry_delays = [5, 10, 20, 40, 80]  # seconds
        max_retries = len(retry_delays)

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            if download_id in download_status:
                # Handle file renaming if custom filename was provided
                if custom_filename:
                    downloaded_file = _temp_filenames.pop(download_id, None)
                    if downloaded_file:
                        new_path = _rename_downloaded_file(
                            downloaded_file, custom_filename
                        )
                        if new_path:
                            download_status[download_id]["filename"] = new_path

                download_status[download_id]["status"] = "completed"
                download_status[download_id]["percent"] = "100%"
                download_status[download_id]["error"] = None
            return None  # Success

        except Exception as e:
            error_msg = _strip_ansi(str(e))
            # Retry on rate limits OR timeout errors
            is_rate_limit = "429" in error_msg or "Too Many Requests" in error_msg
            is_timeout = (
                "timed out" in error_msg.lower()
                or "timeout" in error_msg.lower()
                or "Read timed out" in error_msg
            )
            should_retry = is_rate_limit or is_timeout

            if should_retry and attempt < max_retries:
                # Retryable error, return delay
                remaining = max_retries - attempt
                retry_delay = retry_delays[attempt]
                reason = "Rate limited" if is_rate_limit else "Timed out"
                print(
                    f"{reason} on {url}, retrying in {retry_delay}s "
                    f"({remaining} retries left)"
                )
                if download_id in download_status:
                    download_status[download_id]["status"] = "retrying"
                    download_status[download_id]["error"] = (
                        f"{reason}. Retrying in {retry_delay}s... ({remaining} left)"
                    )
                return retry_delay
            else:
                # Non-retryable error or max retries exceeded
                print(f"Error downloading {url}: {e}")
                if download_id in download_status:
                    download_status[download_id]["status"] = "error"
                    download_status[download_id]["error"] = error_msg
                return None

    async def add_download(
        self,
        url: str,
        client_opts: dict[str, Any] | None = None,
        custom_filename: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Queue a new download and return its ID.

        Args:
            url: The URL to download
            client_opts: Optional yt_dlp options to override defaults
            custom_filename: Optional filename to rename the file to after download
            metadata: Optional metadata to store with the download
        """
        # Sanitize client_opts for logging
        download_id = str(uuid.uuid4())

        new_status: DownloadStatus = {
            "id": download_id,
            "url": url,
            "status": "queued",
            "percent": "0%",
            "metadata": metadata,
        }

        # Store custom filename in status for display
        if custom_filename:
            new_status["filename"] = custom_filename

        download_status[download_id] = new_status

        job: DownloadJob = {
            "id": download_id,
            "url": url,
            "opts": client_opts or {},
            "custom_filename": custom_filename,
            "metadata": metadata,
        }
        await self.queue.put(job)

        return download_id

    def get_all_downloads(self) -> list[DownloadStatus]:
        """Get all download statuses."""
        return list(download_status.values())

    def get_download(self, download_id: str) -> DownloadStatus | None:
        """Get a specific download status."""
        return download_status.get(download_id)


# Global manager instance
manager = DownloadManager(max_concurrent_downloads=2)


@asynccontextmanager
async def download_manager_lifespan(app):
    """FastAPI lifespan context manager to start download workers."""
    await manager.start_workers()
    yield
    await manager.shutdown()

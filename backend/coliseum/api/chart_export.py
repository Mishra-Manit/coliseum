"""Reusable chart export service for dashboard downloads and automation."""

from __future__ import annotations

import os
import subprocess
import tempfile
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from shutil import which
from typing import Any, Literal

from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from pydantic import BaseModel

ExportFormat = Literal["mp4"]
ExportQuality = Literal["fast", "balanced", "hq"]


class ChartExportError(Exception):
    """Base chart export exception."""


class ChartExportBusyError(ChartExportError):
    """Raised when an export is already in progress."""


class ChartExportDependencyError(ChartExportError):
    """Raised when required dependencies are missing."""


class ChartExportTimeoutError(ChartExportError):
    """Raised when rendering or encoding exceeds timeout limits."""


class ChartExportNoDataError(ChartExportError):
    """Raised when no chart data exists for export."""


@dataclass(frozen=True)
class RenderProfile:
    """Rendering settings for a named quality profile."""

    width: int
    height: int
    fps: int
    draw_seconds: float
    hold_seconds: float
    timeout_seconds: float


_PROFILES: dict[ExportQuality, RenderProfile] = {
    "fast": RenderProfile(
        width=960,
        height=540,
        fps=12,
        draw_seconds=3.5,
        hold_seconds=0.5,
        timeout_seconds=12.0,
    ),
    "balanced": RenderProfile(
        width=1280,
        height=720,
        fps=18,
        draw_seconds=4.0,
        hold_seconds=0.6,
        timeout_seconds=16.0,
    ),
    "hq": RenderProfile(
        width=1920,
        height=1080,
        fps=24,
        draw_seconds=4.5,
        hold_seconds=0.8,
        timeout_seconds=24.0,
    ),
}

_BG = "#07060a"
_GRID = "#1a1728"
_TEXT = "#8e8b98"
_AMBER = "#d97706"
_FILL = (217 / 255, 119 / 255, 6 / 255, 0.18)


class ExportResult(BaseModel):
    """Binary export payload and metadata."""

    content: bytes
    media_type: str
    filename: str
    quality_used: ExportQuality
    cache_hit: bool


class _CacheEntry(BaseModel):
    """In-memory cache entry for rendered exports."""

    content: bytes
    quality_used: ExportQuality
    expires_at: float


class ChartExportService:
    """Generate and cache chart exports for API and automation usage."""

    def __init__(self) -> None:
        self._cache_ttl_seconds = 300.0
        self._cache: dict[str, _CacheEntry] = {}
        self._cache_lock = threading.Lock()
        self._inflight_lock = threading.Lock()

    def export(
        self,
        snapshots: list[dict[str, Any]],
        export_format: ExportFormat,
        quality: ExportQuality,
    ) -> ExportResult:
        """Render an export for chart series data."""
        if export_format != "mp4":
            raise ChartExportError("Unsupported export format")

        navs = [round(float(s["total_value"]), 2) for s in snapshots if "total_value" in s]
        timestamps = [str(s["snapshot_at"]) for s in snapshots if "snapshot_at" in s]

        if not navs or not timestamps:
            raise ChartExportNoDataError("No chart data available for export")

        cache_key = self._make_cache_key(export_format, quality, navs, timestamps)
        cached = self._get_cache_entry(cache_key)
        if cached is not None:
            return ExportResult(
                content=cached.content,
                media_type="video/mp4",
                filename=self._build_filename(),
                quality_used=cached.quality_used,
                cache_hit=True,
            )

        if not self._inflight_lock.acquire(blocking=False):
            raise ChartExportBusyError("Chart export already in progress")

        try:
            result_bytes, quality_used = self._render_with_fallback(navs, quality)
            self._set_cache_entry(
                cache_key,
                _CacheEntry(
                    content=result_bytes,
                    quality_used=quality_used,
                    expires_at=time.time() + self._cache_ttl_seconds,
                ),
            )
            return ExportResult(
                content=result_bytes,
                media_type="video/mp4",
                filename=self._build_filename(),
                quality_used=quality_used,
                cache_hit=False,
            )
        finally:
            self._inflight_lock.release()

    def _smooth_nav_values(self, navs: list[float], window_size: int = 3) -> list[float]:
        """Apply moving average smoothing to NAV values to reduce spikes."""
        if len(navs) <= window_size:
            return navs

        smoothed = []
        for i in range(len(navs)):
            # Calculate window bounds
            start = max(0, i - window_size // 2)
            end = min(len(navs), i + window_size // 2 + 1)
            # Average values in window
            window_avg = sum(navs[start:end]) / (end - start)
            smoothed.append(round(window_avg, 2))
        return smoothed

    def _render_with_fallback(
        self, navs: list[float], requested_quality: ExportQuality
    ) -> tuple[bytes, ExportQuality]:
        """Render with one-step quality downgrade on timeout."""
        navs_smoothed = self._smooth_nav_values(navs)
        try:
            return self._render_mp4(navs_smoothed, requested_quality), requested_quality
        except ChartExportTimeoutError:
            downgraded = self._downgrade_quality(requested_quality)
            if downgraded is None:
                raise
            return self._render_mp4(navs_smoothed, downgraded), downgraded

    def _render_mp4(self, navs: list[float], quality: ExportQuality) -> bytes:
        """Render NAV animation and encode as MP4 using ffmpeg."""
        ffmpeg_path = which("ffmpeg")
        if ffmpeg_path is None:
            raise ChartExportDependencyError("ffmpeg is required for mp4 exports")

        profile = _PROFILES[quality]
        fd, temp_path = tempfile.mkstemp(prefix="coliseum-chart-", suffix=".mp4")
        os.close(fd)
        output_path = Path(temp_path)

        fig = Figure(
            figsize=(profile.width / 100, profile.height / 100),
            dpi=100,
            facecolor=_BG,
        )
        canvas = FigureCanvasAgg(fig)
        ax = fig.add_axes([0.06, 0.12, 0.9, 0.8], facecolor=_BG)

        for spine in ax.spines.values():
            spine.set_visible(False)

        ax.grid(axis="y", color=_GRID, linewidth=0.8, alpha=0.8)
        ax.tick_params(axis="x", bottom=False, labelbottom=False)
        ax.tick_params(axis="y", colors=_TEXT, labelsize=10)

        x_values = list(range(len(navs)))
        min_nav = min(navs)
        max_nav = max(navs)
        spread = max_nav - min_nav
        y_pad = max(spread * 0.2, 1.0)
        y_min = min_nav - y_pad
        y_max = max_nav + y_pad

        x_max = max(1, len(navs) - 1)
        ax.set_xlim(0, x_max)
        ax.set_ylim(y_min, y_max)

        line = ax.plot([], [], color=_AMBER, linewidth=2.6)[0]
        fill = None

        nav_text = ax.text(
            0.02,
            0.95,
            "Portfolio NAV\n$0.00",
            transform=ax.transAxes,
            va="top",
            ha="left",
            color=_TEXT,
            fontsize=14,
            family="monospace",
        )

        ax.text(
            0.985,
            0.04,
            "COLISEUM",
            transform=ax.transAxes,
            va="bottom",
            ha="right",
            color=_TEXT,
            fontsize=12,
            family="monospace",
            alpha=0.65,
        )

        ffmpeg_cmd = [
            ffmpeg_path,
            "-y",
            "-f",
            "rawvideo",
            "-pix_fmt",
            "rgba",
            "-s",
            f"{profile.width}x{profile.height}",
            "-r",
            str(profile.fps),
            "-i",
            "-",
            "-an",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            "-preset",
            "veryfast",
            "-crf",
            "24",
            str(output_path),
        ]

        process = subprocess.Popen(
            ffmpeg_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        start_time = time.time()
        draw_frames = max(2, int(profile.fps * profile.draw_seconds))
        hold_frames = max(1, int(profile.fps * profile.hold_seconds))
        last_frame: bytes | None = None

        try:
            for frame_index in range(draw_frames):
                elapsed = time.time() - start_time
                if elapsed > profile.timeout_seconds:
                    raise ChartExportTimeoutError("Chart export timed out")

                if len(navs) == 1:
                    point_count = 1
                else:
                    progress = frame_index / (draw_frames - 1)
                    point_count = int(round(progress * (len(navs) - 1))) + 1

                x_chunk = x_values[:point_count]
                y_chunk = navs[:point_count]

                line.set_data(x_chunk, y_chunk)
                if fill is not None:
                    fill.remove()
                fill = ax.fill_between(x_chunk, y_chunk, y2=y_min, color=_FILL)

                nav_text.set_text(f"Portfolio NAV\n${y_chunk[-1]:.2f}")

                canvas.draw()
                frame_bytes = canvas.buffer_rgba().tobytes()
                last_frame = frame_bytes
                if process.stdin is None:
                    raise ChartExportError("ffmpeg stdin is not available")
                process.stdin.write(frame_bytes)

            if last_frame is not None and process.stdin is not None:
                for _ in range(hold_frames):
                    process.stdin.write(last_frame)

            if process.stdin is not None:
                process.stdin.close()

            process.wait(timeout=max(5.0, profile.timeout_seconds / 2))
            if process.returncode != 0:
                stderr_bytes = process.stderr.read() if process.stderr else b""
                stderr = stderr_bytes.decode("utf-8", errors="ignore")
                raise ChartExportError(f"ffmpeg encode failed: {stderr[-300:]}")

            return output_path.read_bytes()
        except subprocess.TimeoutExpired as exc:
            raise ChartExportTimeoutError("Encoding timed out") from exc
        except BrokenPipeError as exc:
            stderr_bytes = process.stderr.read() if process.stderr else b""
            stderr = stderr_bytes.decode("utf-8", errors="ignore")
            raise ChartExportError(f"ffmpeg pipe failed: {stderr[-300:]}") from exc
        finally:
            if process.poll() is None:
                process.kill()
                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    pass
            fig.clear()
            if output_path.exists():
                output_path.unlink()

    def _make_cache_key(
        self,
        export_format: ExportFormat,
        quality: ExportQuality,
        navs: list[float],
        timestamps: list[str],
    ) -> str:
        """Build cache key from format, quality, and latest data signature."""
        first_ts = timestamps[0]
        last_ts = timestamps[-1]
        latest_nav = navs[-1]
        return (
            f"{export_format}:{quality}:{len(navs)}:{first_ts}:{last_ts}:{latest_nav:.2f}"
        )

    def _get_cache_entry(self, key: str) -> _CacheEntry | None:
        """Read non-expired cache entry if present."""
        now = time.time()
        with self._cache_lock:
            entry = self._cache.get(key)
            if entry is None:
                return None
            if entry.expires_at < now:
                self._cache.pop(key, None)
                return None
            return entry

    def _set_cache_entry(self, key: str, entry: _CacheEntry) -> None:
        """Store a cache entry and prune stale values."""
        now = time.time()
        with self._cache_lock:
            self._cache[key] = entry
            stale_keys = [k for k, v in self._cache.items() if v.expires_at < now]
            for stale_key in stale_keys:
                self._cache.pop(stale_key, None)

    def _build_filename(self) -> str:
        """Create a local-time human-readable filename for download."""
        stamp = datetime.now().astimezone().strftime("%b-%d-%Y-%I-%M%p").lower()
        return f"coliseum-portfolio-{stamp}.mp4"

    def _downgrade_quality(self, quality: ExportQuality) -> ExportQuality | None:
        """Return the next lower quality profile."""
        if quality == "hq":
            return "balanced"
        if quality == "balanced":
            return "fast"
        return None

"""Reusable chart export service for dashboard downloads and automation."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tempfile
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from shutil import which
from typing import Any, Literal

ExportInterval = Literal["1D", "1W", "1M", "ALL"]

_RENDER_FPS = 30
_RENDER_TIMEOUT_SECONDS = 240.0

_INTERVALS: dict[ExportInterval, tuple[timedelta | None, timedelta | None]] = {
    "1D": (timedelta(days=1), timedelta(minutes=5)),
    "1W": (timedelta(days=7), timedelta(hours=1)),
    "1M": (timedelta(days=30), timedelta(hours=6)),
    "ALL": (None, None),
}

_DURATION_PARAMS: dict[ExportInterval, tuple[float, float, float, float]] = {
    "1D": (5.5, 0.012, 6.5, 8.5),
    "1W": (7.2, 0.020, 8.5, 12.0),
    "1M": (9.5, 0.034, 11.5, 16.5),
    "ALL": (13.0, 0.070, 17.0, 31.0),
}

_ALL_TIME_BUCKETS: tuple[tuple[timedelta, timedelta], ...] = (
    (timedelta(days=14), timedelta(hours=1)),
    (timedelta(days=60), timedelta(hours=6)),
    (timedelta(days=180), timedelta(days=1)),
    (timedelta(days=365), timedelta(days=2)),
)


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
class ExportResult:
    """Binary export payload and metadata."""

    content: bytes
    media_type: str
    filename: str
    cache_hit: bool


class ChartExportService:
    """Generate and cache chart exports for API and automation usage."""

    def __init__(self) -> None:
        self._cache_ttl_seconds = 300.0
        self._cache: dict[str, tuple[bytes, float]] = {}
        self._cache_lock = threading.Lock()
        self._inflight_lock = threading.Lock()

    def export(
        self,
        cycles: list[dict[str, Any]],
        interval: ExportInterval,
    ) -> ExportResult:
        """Render an export for chart series data."""
        points = self._normalize_points(cycles, interval)
        if not points:
            raise ChartExportNoDataError("No chart data available for export")

        cache_key = self._make_cache_key(interval, points)
        cached = self._get_cache_entry(cache_key)
        if cached is not None:
            return ExportResult(
                content=cached,
                media_type="video/mp4",
                filename=self._build_filename(),
                cache_hit=True,
            )

        if not self._inflight_lock.acquire(blocking=False):
            raise ChartExportBusyError("Chart export already in progress")

        try:
            result_bytes = self._render_mp4(points, interval)
            self._set_cache_entry(
                cache_key,
                result_bytes,
                time.time() + self._cache_ttl_seconds,
            )
            return ExportResult(
                content=result_bytes,
                media_type="video/mp4",
                filename=self._build_filename(),
                cache_hit=False,
            )
        finally:
            self._inflight_lock.release()

    def _normalize_points(
        self, cycles: list[dict[str, Any]], interval: ExportInterval
    ) -> list[dict[str, Any]]:
        """Sort, filter, and bucket NAV data for rendering."""
        parsed: list[tuple[datetime, float]] = []
        for cycle in cycles:
            if "total_value" not in cycle or "cycle_at" not in cycle:
                continue
            try:
                parsed.append(
                    (
                        _parse_utc(str(cycle["cycle_at"])),
                        round(float(cycle["total_value"]), 2),
                    )
                )
            except (TypeError, ValueError):
                continue

        if not parsed:
            return []

        sorted_points = sorted(parsed, key=lambda item: item[0])
        latest_at = sorted_points[-1][0]
        lookback, configured_bucket = _INTERVALS[interval]
        if lookback is None:
            filtered = sorted_points
        else:
            cutoff = latest_at - lookback
            filtered = [(ts, nav) for ts, nav in sorted_points if ts >= cutoff]
            if not filtered:
                filtered = sorted_points[-1:]

        bucket = configured_bucket or _all_time_bucket(sorted_points[0][0], latest_at)
        bucket_seconds = int(bucket.total_seconds())
        buckets: dict[int, float] = {}
        for timestamp, nav in filtered:
            epoch_seconds = int(timestamp.timestamp())
            bucket_key = (epoch_seconds // bucket_seconds) * bucket_seconds
            buckets[bucket_key] = nav

        return [
            {
                "timestamp": datetime.fromtimestamp(key, tz=timezone.utc).isoformat(),
                "nav": nav,
            }
            for key, nav in sorted(buckets.items())
        ]

    def _render_mp4(self, points: list[dict[str, Any]], interval: ExportInterval) -> bytes:
        """Render the chart animation through Remotion."""
        frontend_dir = _frontend_dir()
        renderer_script = frontend_dir / "remotion" / "render-chart.ts"

        if which("npm") is None:
            raise ChartExportDependencyError("npm is required for Remotion chart exports")
        if not renderer_script.exists():
            raise ChartExportDependencyError("Remotion chart renderer script is missing")
        if not (frontend_dir / "node_modules" / ".bin" / "tsx").exists():
            raise ChartExportDependencyError(
                "Frontend Remotion dependencies are not installed"
            )

        with tempfile.TemporaryDirectory(prefix="coliseum-chart-") as temp_dir:
            temp_path = Path(temp_dir)
            props_path = temp_path / "props.json"
            output_path = temp_path / "chart.mp4"
            duration_in_frames = _duration_in_frames(interval, len(points), _RENDER_FPS)
            props_path.write_text(
                json.dumps(
                    {
                        "points": points,
                        "interval": interval,
                        "durationInFrames": duration_in_frames,
                    }
                ),
                encoding="utf-8",
            )

            command = [
                "npm",
                "run",
                "render:chart-video",
                "--",
                f"--props={props_path}",
                f"--output={output_path}",
            ]

            try:
                subprocess.run(
                    command,
                    cwd=frontend_dir,
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=_RENDER_TIMEOUT_SECONDS,
                )
            except subprocess.TimeoutExpired as exc:
                raise ChartExportTimeoutError("Remotion render timed out") from exc
            except subprocess.CalledProcessError as exc:
                stderr = exc.stderr.decode("utf-8", errors="ignore")
                raise ChartExportError(f"Remotion render failed: {stderr[-500:]}") from exc

            if not output_path.exists():
                raise ChartExportError("Remotion did not produce an output file")
            return output_path.read_bytes()

    def _make_cache_key(
        self,
        interval: ExportInterval,
        points: list[dict[str, Any]],
    ) -> str:
        """Build cache key from interval and full point content."""
        digest = hashlib.sha256(
            json.dumps(points, separators=(",", ":")).encode("utf-8")
        ).hexdigest()[:16]
        return f"mp4:{interval}:{digest}"

    def _get_cache_entry(self, key: str) -> bytes | None:
        """Read non-expired cache entry if present."""
        now = time.time()
        with self._cache_lock:
            entry = self._cache.get(key)
            if entry is None:
                return None
            content, expires_at = entry
            if expires_at < now:
                self._cache.pop(key, None)
                return None
            return content

    def _set_cache_entry(self, key: str, content: bytes, expires_at: float) -> None:
        """Store a cache entry and prune stale values."""
        now = time.time()
        with self._cache_lock:
            self._cache[key] = (content, expires_at)
            stale_keys = [k for k, (_, expiry) in self._cache.items() if expiry < now]
            for stale_key in stale_keys:
                self._cache.pop(stale_key, None)

    def _build_filename(self) -> str:
        """Create a local-time human-readable filename for download."""
        stamp = datetime.now().astimezone().strftime("%b-%d-%Y-%I-%M%p").lower()
        return f"coliseum-portfolio-{stamp}.mp4"


def _duration_in_frames(interval: ExportInterval, point_count: int, fps: int) -> int:
    """Pick render duration from interval breadth and visible point count."""
    base_seconds, seconds_per_point, min_seconds, max_seconds = _DURATION_PARAMS[
        interval
    ]
    seconds = min(
        max_seconds,
        max(min_seconds, base_seconds + point_count * seconds_per_point),
    )
    return int(round(seconds * fps))


def _all_time_bucket(earliest_at: datetime, latest_at: datetime) -> timedelta:
    """Choose an all-time bucket that keeps long videos readable."""
    span = latest_at - earliest_at
    for max_span, bucket in _ALL_TIME_BUCKETS:
        if span <= max_span:
            return bucket
    return timedelta(days=7)


def _frontend_dir() -> Path:
    """Resolve the frontend directory from the backend package path."""
    override = os.getenv("COLISEUM_FRONTEND_DIR")
    if override:
        return Path(override).expanduser().resolve()
    return Path(__file__).resolve().parents[3] / "frontend"


def _parse_utc(value: str) -> datetime:
    """Parse an ISO timestamp as timezone-aware UTC."""
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)

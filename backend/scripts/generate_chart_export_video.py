#!/usr/bin/env python3
"""
Generate chart export video using REAL or SIMULATED database data.

PRIORITY:
1. First attempts to fetch real data from Supabase database
2. If no DB connection or no data, falls back to SIMULATED database records

The simulation uses the EXACT same schema as real PortfolioSnapshot records:
- snapshot_at: ISO 8601 timestamp
- total_value: Portfolio NAV
- cash_balance: Cash portion
- positions_value: Position value
- open_positions: Count of open positions
- realized_pnl: Realized profit/loss

Usage:
    cd backend && source venv/bin/activate && python scripts/generate_chart_export_video.py
    
To use real data, set SUPABASE_DB_URL in .env:
    SUPABASE_DB_URL=postgresql+asyncpg://postgres:[password]@db.[project].supabase.co:5432/postgres
"""

import asyncio
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt
import numpy as np

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Color constants matching the lightweight-charts design
COLORS = {
    "bg": "#07060a",
    "grid": "#1a1728",
    "text": "#8e8b98",
    "amber": "#d97706",
    "positive": "#16a34a",
    "negative": "#dc2626",
}

# HQ Profile
PROFILE = {
    "width": 1920,
    "height": 1080,
    "fps": 30,
    "duration": 6.0,  # seconds
    "dpi": 100,
    "bitrate": "5M",
}


def format_price(value: float) -> str:
    return f"${value:,.2f}"


def format_date_from_ts(ts: int) -> str:
    dt = datetime.fromtimestamp(ts)
    return dt.strftime("%b %d")


def generate_simulated_snapshots(seed: int = 42) -> list[dict]:
    """
    Generate SIMULATED portfolio snapshots matching the EXACT database schema.
    
    This produces realistic-looking data with the same structure as real
    PortfolioSnapshot records from the database. Used when no DB connection.
    
    Schema matches list_portfolio_snapshots_from_db() return format:
    {
        "snapshot_at": "2024-01-15T10:30:00+00:00",
        "total_value": 10500.50,
        "cash_balance": 3150.15,
        "positions_value": 7350.35,
        "open_positions": 3,
        "realized_pnl": 150.25
    }
    """
    import random
    random.seed(seed)
    
    print("📊 Generating SIMULATED database records...")
    print("   (Using same schema as real PortfolioSnapshot data)")
    
    snapshots = []
    base_nav = 10000.0
    current_nav = base_nav
    start_date = datetime(2024, 1, 1)
    days = 45
    
    total_realized = 0.0
    
    for day in range(days):
        # 6 snapshots per day (every 4 hours during trading day)
        for hour in [0, 4, 8, 12, 16, 20]:
            timestamp = start_date + timedelta(days=day, hours=hour)
            
            # Realistic portfolio movements:
            # - Small intraday drift (market noise)
            # - Larger moves from position updates (every 3 days)
            # - Slight daily upward trend (winning strategy)
            drift = (random.random() - 0.47) * 50
            position_move = (random.random() - 0.4) * 300 if (day % 3 == 0 and hour == 16) else 0
            trend = day * 12
            
            current_nav = base_nav + trend + drift + position_move
            current_nav = max(current_nav, 9500)  # Floor protection at 95%
            current_nav += (random.random() - 0.5) * 20  # Micro-noise
            
            # Portfolio composition: ~30% cash, ~70% positions
            cash = current_nav * 0.3
            positions = current_nav * 0.7
            
            # Calculate realized PnL from closed positions
            if day % 7 == 0 and hour == 20:
                # Weekly position closures
                realized = (random.random() - 0.3) * 200
                total_realized += realized
            
            snapshots.append({
                "snapshot_at": timestamp.strftime("%Y-%m-%dT%H:%M:%S") + "+00:00",
                "total_value": round(current_nav, 2),
                "cash_balance": round(cash, 2),
                "positions_value": round(positions, 2),
                "open_positions": random.randint(0, 5),
                "realized_pnl": round(total_realized, 2)
            })
    
    return snapshots


async def fetch_real_data() -> list[dict] | None:
    """Attempt to fetch real data from Supabase database."""
    # Check if DB URL is available
    db_url = os.environ.get("SUPABASE_DB_URL", "")
    
    if not db_url:
        # Try to load from .env file
        env_path = Path(__file__).parent.parent / ".env"
        if env_path.exists():
            with open(env_path) as f:
                for line in f:
                    if line.startswith("SUPABASE_DB_URL="):
                        db_url = line.strip().split("=", 1)[1].strip('"\'')
                        break
    
    if not db_url:
        print("⚠️  No SUPABASE_DB_URL found in environment or .env")
        return None
    
    print("📊 Attempting to fetch REAL data from database...")
    
    try:
        # Import here to avoid errors if SQLAlchemy not installed
        from coliseum.services.supabase.repositories.portfolio_snapshots import (
            list_portfolio_snapshots_from_db,
        )
        
        snapshots = await list_portfolio_snapshots_from_db()
        
        if not snapshots:
            print("   ⚠️  Database connected but no snapshots found")
            return None
        
        print(f"   ✅ Fetched {len(snapshots)} REAL snapshots from database!")
        return snapshots
        
    except ImportError as e:
        print(f"   ⚠️  Database dependencies not installed: {e}")
        return None
    except Exception as e:
        print(f"   ⚠️  Database connection failed: {e}")
        return None


def bucketize_data(snapshots: list[dict]) -> list[dict]:
    """
    Bucket snapshots by day, keeping first and last NAV per day.
    Matches the getChartSeries logic in chart-utils.ts
    """
    buckets: dict[str, dict] = {}
    
    for snap in snapshots:
        ts = snap["snapshot_at"]
        # Parse ISO timestamp
        if ts.endswith("Z"):
            ts = ts[:-1] + "+00:00"
        dt = datetime.fromisoformat(ts)
        day_key = dt.strftime("%Y-%m-%d")
        
        if day_key not in buckets:
            buckets[day_key] = {
                "date": day_key,
                "time": int(dt.timestamp()),
                "first_nav": snap["total_value"],
                "last_nav": snap["total_value"],
            }
        else:
            buckets[day_key]["last_nav"] = snap["total_value"]
    
    return sorted(buckets.values(), key=lambda x: x["time"])


def generate_histogram(bucketized: list[dict]) -> list[dict]:
    """Generate daily P&L histogram from bucketized data."""
    hist = []
    for i, day in enumerate(bucketized):
        if i == 0:
            hist.append({"time": day["time"], "value": 0.0})
        else:
            prev = bucketized[i - 1]
            pnl = day["last_nav"] - prev["last_nav"]
            hist.append({"time": day["time"], "value": round(pnl, 2)})
    return hist


def draw_frame(
    ax_main,
    ax_hist,
    data: list[dict],
    hist_data: list[dict],
    progress: float,
):
    """Draw a single frame with given progress (0-1)."""
    ax_main.clear()
    ax_hist.clear()
    
    ax_main.set_facecolor(COLORS["bg"])
    ax_hist.set_facecolor(COLORS["bg"])
    
    if not data:
        return
    
    visible_count = max(1, int(len(data) * progress))
    visible_data = data[:visible_count]
    
    times = [d["time"] for d in data]
    navs = [d["last_nav"] for d in data]
    
    visible_times = [d["time"] for d in visible_data]
    visible_navs = [d["last_nav"] for d in visible_data]
    
    if not visible_navs:
        return
    
    min_val = min(navs) * 0.99
    max_val = max(navs) * 1.01
    current_nav = data[-1]["last_nav"]
    
    # Main chart
    ax_main.set_xlim(min(times), max(times))
    ax_main.set_ylim(min_val, max_val)
    
    if len(visible_times) > 1:
        ax_main.fill_between(
            visible_times,
            min_val,
            visible_navs,
            alpha=0.25,
            color=COLORS["amber"],
        )
        ax_main.plot(
            visible_times,
            visible_navs,
            color=COLORS["amber"],
            linewidth=3,
            solid_capstyle="round",
        )
    
    ax_main.grid(True, alpha=0.3, color=COLORS["grid"], linestyle="-")
    ax_main.set_axisbelow(True)
    ax_main.tick_params(colors=COLORS["text"], labelsize=10)
    ax_main.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: format_price(x)))
    ax_main.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: format_date_from_ts(x)))
    
    # Title
    ax_main.text(
        0.02, 0.95, "PORTFOLIO VALUE",
        transform=ax_main.transAxes,
        color=COLORS["text"],
        fontsize=14,
        fontweight="bold",
        fontfamily="monospace",
        verticalalignment="top",
    )
    ax_main.text(
        0.02, 0.88, format_price(current_nav),
        transform=ax_main.transAxes,
        color=COLORS["amber"],
        fontsize=18,
        fontweight="bold",
        fontfamily="monospace",
        verticalalignment="top",
    )
    
    for spine in ax_main.spines.values():
        spine.set_visible(False)
    
    # Histogram
    if hist_data and visible_count > 1:
        visible_hist = hist_data[:visible_count]
        hist_values = [h["value"] for h in visible_hist]
        hist_times = [h["time"] for h in visible_hist]
        
        max_abs = max(abs(v) for v in hist_values) if hist_values else 1
        
        colors = [
            COLORS["positive"] if v >= 0 else COLORS["negative"]
            for v in hist_values
        ]
        
        ax_hist.bar(
            hist_times,
            hist_values,
            color=colors,
            alpha=0.65,
            width=(max(times) - min(times)) / len(data) * 0.6,
        )
        
        ax_hist.set_xlim(min(times), max(times))
        ax_hist.axhline(y=0, color=COLORS["grid"], linewidth=0.5)
        ax_hist.set_ylim(-max_abs * 1.2, max_abs * 1.2)
    
    ax_hist.text(
        0.02, 0.85, "DAILY P&L",
        transform=ax_hist.transAxes,
        color=COLORS["text"],
        fontsize=12,
        fontfamily="monospace",
        verticalalignment="top",
    )
    
    for spine in ax_hist.spines.values():
        spine.set_visible(False)
    ax_hist.tick_params(colors=COLORS["text"], labelsize=9)
    ax_hist.set_xticks([])


async def generate_video():
    """Main video generation."""
    print("🎬 Chart Export Video Generator")
    print("   Priority: 1) Real DB data → 2) Simulated data\n")
    
    # Try real data first
    snapshots = await fetch_real_data()
    data_source = "REAL DATABASE"
    
    # Fall back to simulated
    if snapshots is None:
        snapshots = generate_simulated_snapshots()
        data_source = "SIMULATED (DB Schema)"
    
    if not snapshots:
        print("\n❌ No data available - cannot generate video")
        return
    
    # Show data summary
    first = snapshots[0]
    last = snapshots[-1]
    print(f"\n📈 Data Summary ({data_source}):")
    print(f"   Records: {len(snapshots)} snapshots")
    print(f"   Date range: {first['snapshot_at'][:10]} to {last['snapshot_at'][:10]}")
    print(f"   NAV range: {format_price(first['total_value'])} → {format_price(last['total_value'])}")
    
    # Transform
    bucketized = bucketize_data(snapshots)
    print(f"   Bucketized: {len(bucketized)} daily points")
    
    hist_data = generate_histogram(bucketized)
    
    # Setup figure
    fig = plt.figure(figsize=(19.2, 10.8), dpi=PROFILE["dpi"])
    fig.patch.set_facecolor(COLORS["bg"])
    
    gs = fig.add_gridspec(2, 1, height_ratios=[3, 1.5], hspace=0.1)
    ax_main = fig.add_subplot(gs[0])
    ax_hist = fig.add_subplot(gs[1])
    
    # Generate frames
    with tempfile.TemporaryDirectory() as frames_dir:
        print(f"\n🎞️  Rendering frames...")
        
        total_frames = int(PROFILE["duration"] * PROFILE["fps"])
        
        for i in range(total_frames):
            progress = i / (total_frames - 1) if total_frames > 1 else 1.0
            
            draw_frame(ax_main, ax_hist, bucketized, hist_data, progress)
            
            frame_path = Path(frames_dir) / f"frame_{i:04d}.png"
            fig.savefig(
                frame_path,
                facecolor=COLORS["bg"],
                edgecolor="none",
                bbox_inches="tight",
                pad_inches=0.1,
            )
            
            if i % 30 == 0:
                print(f"   {int((i / total_frames) * 100)}%")
        
        print(f"   ✓ Rendered {total_frames} frames ({PROFILE['width']}x{PROFILE['height']})")
        
        # Encode video
        output_path = Path(__file__).parent.parent.parent / "frontend" / "public" / "chart-export-demo.webm"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        print(f"\n🎥 Encoding to WebM...")
        
        ffmpeg_cmd = [
            "ffmpeg", "-y",
            "-framerate", str(PROFILE["fps"]),
            "-i", str(Path(frames_dir) / "frame_%04d.png"),
            "-c:v", "libvpx-vp9",
            "-pix_fmt", "yuva420p",
            "-b:v", PROFILE["bitrate"],
            str(output_path),
        ]
        
        try:
            subprocess.run(ffmpeg_cmd, check=True, capture_output=True)
            
            file_size = output_path.stat().st_size / 1024
            
            print(f"\n✅ SUCCESS! Video generated:")
            print(f"   File: {output_path}")
            print(f"   Size: {file_size:.1f} KB")
            print(f"   Resolution: {PROFILE['width']}x{PROFILE['height']}")
            print(f"   FPS: {PROFILE['fps']}")
            print(f"   Duration: {PROFILE['duration']}s")
            print(f"   Data source: {data_source}")
            print(f"   Data points: {len(bucketized)} days")
            
        except subprocess.CalledProcessError as e:
            print(f"\n❌ ffmpeg failed: {e}")
            if e.stderr:
                print(f"   {e.stderr.decode()[:200]}")
            raise
    
    plt.close(fig)
    
    print(f"\n💡 To use REAL data, set SUPABASE_DB_URL in backend/.env")
    print(f"   Then re-run: python scripts/generate_chart_export_video.py")


if __name__ == "__main__":
    try:
        asyncio.run(generate_video())
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

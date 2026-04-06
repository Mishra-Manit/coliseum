# GIF Download for Charts Page

## Overview

Add a server-side GIF generator that creates an animated progressive line-draw of the portfolio NAV chart, downloadable from the charts page via a small toolbar button.

## Decisions

### Generation
- Server-side via FastAPI backend using `matplotlib` + `Pillow`
- New endpoint: `GET /api/chart/gif?interval=<interval>`
- Interval param pulled from the frontend's current interval selector state (1D, 1W, 1M, ALL)
- Defaults to ALL if not specified

### Animation
- Progressive line draw, left-to-right — each frame adds the next data point, area fills behind the line as it advances
- NAV area chart only, no daily P&L histogram
- Final frame holds ~0.5 seconds before the GIF ends

### Visual Style
- Match current dark theme exactly:
  - Background: `#07060a`
  - Line color: `#d97706` (amber)
  - Area fill: amber gradient fading to transparent
  - Axis/text color: `#8e8b98`
- Minimal readable text overlays:
  - Top-left: "Portfolio NAV" label + counting NAV value that ticks up in sync with the line draw
  - Bottom-right: muted "COLISEUM" watermark
- Font: monospace (JetBrains Mono or system monospace fallback)

### Resolution and Timing
- 1200x675 pixels (16:9)
- 20 FPS, 4-5 seconds total (~80-100 frames)
- Final ~0.5 seconds (10 frames) hold the completed chart
- Color palette optimized (256 colors with dithering) to keep file size under 3-4MB

### Frontend Trigger
- Small download icon button in the chart toolbar, next to the range switcher (right side)
- Muted text color, lights up on hover
- Shows loading state during server-side generation
- Triggers browser file download on completion

## Implementation Outline

### Backend

1. Add `matplotlib` and `Pillow` to `requirements.txt`
2. Create `backend/coliseum/api/chart_gif.py`:
   - Reuse the same run-cycle data query from `get_chart_data()`
   - Apply interval filtering (same logic as `getChartSeries` in the frontend)
   - Render frames with matplotlib:
     - Set figure size to 1200x675 at appropriate DPI
     - Dark background, no default axes chrome
     - For each frame, plot the line and fill up to the current data index
     - Overlay the NAV counter text (interpolated to current value) top-left
     - Overlay "COLISEUM" watermark bottom-right
     - Render frame to PIL Image via `fig.canvas.tostring_argb()` or `savefig(BytesIO)`
   - Stitch frames into GIF using Pillow with 50ms frame duration (20 FPS)
   - Hold final frame with `duration` override on last ~10 frames
   - Optimize with `PIL.Image.quantize()` or palette reduction
3. Register endpoint on the FastAPI router:
   - `GET /api/chart/gif?interval=1D|1W|1M|ALL`
   - Return `Response(content=gif_bytes, media_type="image/gif")` with `Content-Disposition: attachment; filename="coliseum-portfolio.gif"`

### Frontend

4. Add a download button component in the chart toolbar (`lw-portfolio-chart.tsx`):
   - Small icon button (arrow-down or film icon) next to `RangeSwitcher`
   - On click: set loading state, fetch `/api/chart/gif?interval={currentInterval}` as blob
   - On response: create object URL, trigger download via temporary `<a>` element, revoke URL
   - Show spinner/disabled state while generating

## Dependencies

- `matplotlib` (new)
- `Pillow` (new, or may already be installed as a transitive dep)

## Files to Create/Modify

| File | Action |
|------|--------|
| `backend/requirements.txt` | Add matplotlib, Pillow |
| `backend/coliseum/api/chart_gif.py` | New — GIF generation logic |
| `backend/coliseum/api/server.py` | Register new endpoint |
| `frontend/components/chart/lw-portfolio-chart.tsx` | Add download button to toolbar |

## Open Questions

None — all design branches resolved.

import { useMemo } from "react";
import {
  AbsoluteFill,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import type { Interval } from "../lib/chart-utils";

type ChartPoint = {
  timestamp: string;
  nav: number;
};

export type ChartVideoProps = {
  points: ChartPoint[];
  interval: Interval;
};

const HOLD_FRACTION = 0.18;
const MIN_HOLD_FRAMES = 54;
const MAX_HOLD_FRAMES = 100;

const C = {
  bg: "#07060a",
  panel: "#0d0a12",
  border: "#2e2a40",
  grid: "#1a1728",
  text: "#8e8b98",
  foreground: "#f2f0ee",
  amber: "#d97706",
  amberSoft: "rgba(217, 119, 6, 0.24)",
  amberFade: "rgba(217, 119, 6, 0.02)",
  green: "rgba(22, 163, 74, 0.7)",
  red: "rgba(220, 38, 38, 0.7)",
} as const;

function formatMoney(value: number): string {
  return `$${value.toFixed(2)}`;
}

function formatAxisLabel(timestampMs: number, interval: Interval): string {
  const date = new Date(timestampMs);
  if (interval === "1D") {
    return date.toLocaleTimeString("en-US", {
      hour: "numeric",
      minute: "2-digit",
      hour12: false,
      timeZone: "UTC",
    });
  }
  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    timeZone: "UTC",
  });
}

function buildAxisLabels(
  points: ChartPoint[],
  interval: Interval,
): { label: string; leftPct: number }[] {
  if (points.length === 0) return [];

  const firstMs = new Date(points[0].timestamp).getTime();
  const lastMs = new Date(points[points.length - 1].timestamp).getTime();
  if (firstMs === lastMs) {
    return [{ label: formatAxisLabel(firstMs, interval), leftPct: 0 }];
  }

  const labelCount = interval === "1D" ? 5 : 6;
  const labels = Array.from({ length: labelCount }, (_, index) => {
    const progress = index / (labelCount - 1);
    const timestampMs = firstMs + progress * (lastMs - firstMs);
    return {
      label: formatAxisLabel(timestampMs, interval),
      leftPct: progress * 100,
    };
  });

  return labels.filter(
    (label, index) => index === 0 || label.label !== labels[index - 1].label,
  );
}

function buildLinePath(points: { x: number; y: number }[]): string {
  if (points.length === 0) return "";
  const [first, ...rest] = points;
  return [
    `M ${first.x} ${first.y}`,
    ...rest.map((point) => `L ${point.x} ${point.y}`),
  ].join(" ");
}

function buildAreaPath(
  points: { x: number; y: number }[],
  chartHeight: number,
): string {
  if (points.length === 0) return "";
  const last = points[points.length - 1];
  const first = points[0];
  return `${buildLinePath(points)} L ${last.x} ${chartHeight} L ${first.x} ${chartHeight} Z`;
}

function getCurrentNav(points: ChartPoint[], progress: number): number | null {
  if (points.length === 0) return null;
  if (points.length === 1) return points[0].nav;

  const position = progress * (points.length - 1);
  const baseIndex = Math.min(Math.floor(position), points.length - 2);
  const localProgress = position - baseIndex;
  const current = points[baseIndex].nav;
  const next = points[baseIndex + 1].nav;
  return current + localProgress * (next - current);
}

function makeTicks(min: number, max: number, count: number): number[] {
  if (count <= 1 || min === max) return [min];
  return Array.from({ length: count }, (_, index) => {
    const progress = index / (count - 1);
    return min + progress * (max - min);
  });
}

export function ChartVideo({ points, interval }: ChartVideoProps) {
  const frame = useCurrentFrame();
  const { durationInFrames, width, height } = useVideoConfig();
  const panelInsetX = width * 0.03125;
  const panelInsetY = height * 0.047;
  const panelWidth = width - panelInsetX * 2;
  const panelHeight = height - panelInsetY * 2;
  const chartPaddingX = width * 0.022;
  const chartWidth = panelWidth - chartPaddingX * 2;
  const headerHeight = height * 0.105;
  const pnlHeaderHeight = height * 0.047;
  const mainTopPadding = height * 0.025;
  const histTopPadding = height * 0.011;
  const bottomPadding = height * 0.025;
  const xAxisHeight = height * 0.032;
  const chartAreaHeight =
    panelHeight -
    headerHeight -
    mainTopPadding -
    pnlHeaderHeight -
    histTopPadding -
    xAxisHeight -
    bottomPadding;
  const mainChartHeight = Math.round(chartAreaHeight * 0.7);
  const histChartHeight = Math.round(chartAreaHeight * 0.3);

  const safePoints = useMemo(
    () =>
      [...points]
        .filter((point) => Number.isFinite(point.nav))
        .sort(
          (a, b) =>
            new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime(),
        ),
    [points],
  );

  const holdFrames = Math.min(
    MAX_HOLD_FRAMES,
    Math.max(MIN_HOLD_FRAMES, durationInFrames * HOLD_FRACTION),
  );
  const drawEnd = Math.max(1, durationInFrames - holdFrames);
  const progress = interpolate(frame, [0, drawEnd], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  const chartData = useMemo(() => {
    if (safePoints.length === 0) {
      return {
        linePath: "",
        areaPath: "",
        histBars: [],
        yTicks: [],
        axisLabels: [],
      };
    }

    const firstMs = new Date(safePoints[0].timestamp).getTime();
    const lastMs = new Date(safePoints[safePoints.length - 1].timestamp).getTime();
    const spanMs = Math.max(1, lastMs - firstMs);
    const navs = safePoints.map((point) => point.nav);
    const minNav = Math.min(...navs);
    const maxNav = Math.max(...navs);
    const navSpread = Math.max(0.01, maxNav - minNav);
    const yMin = minNav - Math.max(1, navSpread * 0.18);
    const yMax = maxNav + Math.max(1, navSpread * 0.18);
    const ySpan = Math.max(0.01, yMax - yMin);

    const toX = (timestamp: string) =>
      ((new Date(timestamp).getTime() - firstMs) / spanMs) * chartWidth;
    const toY = (nav: number) =>
      mainChartHeight - ((nav - yMin) / ySpan) * mainChartHeight;

    const svgPoints = safePoints.map((point) => ({
      x: toX(point.timestamp),
      y: toY(point.nav),
    }));
    const linePath = buildLinePath(svgPoints);
    const areaPath = buildAreaPath(svgPoints, mainChartHeight);

    const deltas = safePoints.map((point, index) =>
      index === 0 ? 0 : point.nav - safePoints[index - 1].nav,
    );
    const maxAbsDelta = Math.max(0.01, ...deltas.map((delta) => Math.abs(delta)));
    const histZeroY = histChartHeight / 2;
    const barWidth = Math.max(
      2,
      Math.min(18, (chartWidth / Math.max(1, safePoints.length)) * 0.7),
    );
    const histBars = safePoints.map((point, index) => {
      const x = toX(point.timestamp) - barWidth / 2;
      const delta = deltas[index];
      const barHeight = Math.abs(delta / maxAbsDelta) * (histChartHeight * 0.42);
      return {
        x,
        y: delta >= 0 ? histZeroY - barHeight : histZeroY,
        width: barWidth,
        height: Math.max(1, barHeight),
        color: delta >= 0 ? C.green : C.red,
      };
    });

    const yTicks = makeTicks(yMin, yMax, 5).map((value) => ({
      value,
      y: toY(value),
    }));

    return {
      linePath,
      areaPath,
      histBars,
      yTicks,
      axisLabels: buildAxisLabels(safePoints, interval),
    };
  }, [chartWidth, histChartHeight, interval, mainChartHeight, safePoints]);

  const currentNav = getCurrentNav(safePoints, progress);
  const first = safePoints[0];
  const pnl = currentNav !== null && first ? currentNav - first.nav : 0;
  const pnlPct = first && first.nav !== 0 ? (pnl / Math.abs(first.nav)) * 100 : 0;
  const revealWidth = chartWidth * progress;
  const clipId = "chart-reveal";
  const histClipId = "hist-reveal";

  return (
    <AbsoluteFill
      style={{
        background: C.bg,
        color: C.foreground,
        fontFamily: "JetBrains Mono, Fira Code, monospace",
      }}
    >
      <div
        style={{
          position: "absolute",
          inset: 0,
          backgroundImage:
            "linear-gradient(rgba(255,255,255,0.018) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.018) 1px, transparent 1px)",
          backgroundSize: "40px 40px",
        }}
      />
      <div
        style={{
          position: "absolute",
          inset: 0,
          background:
            "radial-gradient(circle at 20% 0%, rgba(217,119,6,0.18), transparent 32%), radial-gradient(circle at 88% 22%, rgba(180,83,9,0.13), transparent 26%)",
        }}
      />
      <div
        style={{
          position: "absolute",
          left: panelInsetX,
          top: panelInsetY,
          right: panelInsetX,
          bottom: panelInsetY,
          border: `1px solid ${C.border}`,
          background: "rgba(13, 10, 18, 0.88)",
          boxShadow: "0 0 70px rgba(217,119,6,0.11)",
        }}
      >
        <div
          style={{
            height: headerHeight,
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            padding: `0 ${chartPaddingX}px`,
            borderBottom: `1px solid ${C.border}`,
          }}
        >
          <div>
            <div
              style={{
                color: C.text,
                fontSize: 13,
                letterSpacing: 2.2,
                textTransform: "uppercase",
              }}
            >
              Portfolio Value
            </div>
            <div
              style={{
                marginTop: 7,
                color: C.amber,
                fontSize: 30,
                fontWeight: 800,
                letterSpacing: -0.8,
              }}
            >
              {currentNav !== null ? formatMoney(currentNav) : "$0.00"}
            </div>
          </div>
          <div style={{ textAlign: "right" }}>
            <div
              style={{
                color: C.text,
                fontSize: 12,
                letterSpacing: 2,
                textTransform: "uppercase",
              }}
            >
              {interval} Export
            </div>
            <div
              style={{
                marginTop: 9,
                color: pnl >= 0 ? "#34d399" : "#f87171",
                fontSize: 18,
                fontWeight: 700,
              }}
            >
              {pnl >= 0 ? "+" : ""}
              {pnl.toFixed(2)} ({pnlPct >= 0 ? "+" : ""}
              {pnlPct.toFixed(1)}%)
            </div>
          </div>
        </div>

        <div style={{ padding: `${mainTopPadding}px ${chartPaddingX}px 0` }}>
          <svg width={chartWidth} height={mainChartHeight}>
            <defs>
              <clipPath id={clipId}>
                <rect x={0} y={0} width={revealWidth} height={mainChartHeight} />
              </clipPath>
              <linearGradient id="area-fill" x1="0" x2="0" y1="0" y2="1">
                <stop offset="0%" stopColor={C.amberSoft} />
                <stop offset="100%" stopColor={C.amberFade} />
              </linearGradient>
            </defs>
            {chartData.yTicks.map((tick) => (
              <g key={tick.value}>
                <line
                  x1={0}
                  x2={chartWidth}
                  y1={tick.y}
                  y2={tick.y}
                  stroke={C.grid}
                  strokeWidth={1}
                />
                <text
                  x={chartWidth - 6}
                  y={tick.y - 7}
                  fill={C.text}
                  fontSize={12}
                  textAnchor="end"
                >
                  {formatMoney(tick.value)}
                </text>
              </g>
            ))}
            <g clipPath={`url(#${clipId})`}>
              <path d={chartData.areaPath} fill="url(#area-fill)" />
              <path
                d={chartData.linePath}
                fill="none"
                stroke={C.amber}
                strokeWidth={3}
                strokeLinejoin="round"
                strokeLinecap="round"
              />
            </g>
          </svg>
        </div>

        <div
          style={{
            height: pnlHeaderHeight,
            display: "flex",
            alignItems: "center",
            padding: `0 ${chartPaddingX}px`,
            borderTop: `1px solid ${C.border}`,
            borderBottom: `1px solid ${C.border}`,
            color: C.text,
            fontSize: 12,
            letterSpacing: 2.1,
            textTransform: "uppercase",
          }}
        >
          Period P&amp;L
        </div>
        <div style={{ padding: `${histTopPadding}px ${chartPaddingX}px 0` }}>
          <svg width={chartWidth} height={histChartHeight}>
            <defs>
              <clipPath id={histClipId}>
                <rect x={0} y={0} width={revealWidth} height={histChartHeight} />
              </clipPath>
            </defs>
            <line
              x1={0}
              x2={chartWidth}
              y1={histChartHeight / 2}
              y2={histChartHeight / 2}
              stroke={C.grid}
              strokeWidth={1}
            />
            <g clipPath={`url(#${histClipId})`}>
              {chartData.histBars.map((bar, index) => (
                <rect
                  key={`${bar.x}-${index}`}
                  x={bar.x}
                  y={bar.y}
                  width={bar.width}
                  height={bar.height}
                  fill={bar.color}
                />
              ))}
            </g>
          </svg>
        </div>
        <div
          style={{
            position: "relative",
            height: xAxisHeight,
            margin: `0 ${chartPaddingX}px`,
            borderTop: `1px solid ${C.grid}`,
          }}
        >
          {chartData.axisLabels.map((axisLabel, index) => (
            <div
              key={`${axisLabel.label}-${index}`}
              style={{
                position: "absolute",
                left: `${axisLabel.leftPct}%`,
                top: 8,
                transform:
                  index === 0
                    ? "translateX(0)"
                    : index === chartData.axisLabels.length - 1
                      ? "translateX(-100%)"
                      : "translateX(-50%)",
                color: C.text,
                fontSize: 12,
                letterSpacing: 1.2,
                whiteSpace: "nowrap",
                opacity: 0.9,
              }}
            >
              {axisLabel.label}
            </div>
          ))}
        </div>
      </div>
    </AbsoluteFill>
  );
}

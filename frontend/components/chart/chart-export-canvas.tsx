"use client";

import { useEffect, useRef, useCallback } from "react";
import type { ChartDataPoint } from "@/lib/types";
import type { Interval, LWPoint, LWHistPoint } from "@/lib/chart-utils";
import { getChartSeries } from "@/lib/chart-utils";
import type { ChartExportQuality } from "@/hooks/use-chart-export";

interface ChartExportCanvasProps {
  data: ChartDataPoint[];
  interval: Interval;
  quality: ChartExportQuality;
  isRecording: boolean;
  onComplete: () => void;
  onError: (error: string) => void;
}

// Color constants matching the lightweight-charts design
const COLORS = {
  bg: "#07060a",
  grid: "#1a1728",
  text: "#8e8b98",
  amber: "#d97706",
  positive: "#16a34a",
  negative: "#dc2626",
} as const;

interface QualityDimensions {
  width: number;
  height: number;
  padding: { top: number; right: number; bottom: number; left: number };
  fontSize: number;
  lineWidth: number;
}

const QUALITY_DIMS: Record<ChartExportQuality, QualityDimensions> = {
  fast: {
    width: 960,
    height: 540,
    padding: { top: 40, right: 80, bottom: 60, left: 60 },
    fontSize: 11,
    lineWidth: 2,
  },
  balanced: {
    width: 1280,
    height: 720,
    padding: { top: 50, right: 100, bottom: 80, left: 80 },
    fontSize: 12,
    lineWidth: 2.5,
  },
  hq: {
    width: 1920,
    height: 1080,
    padding: { top: 60, right: 120, bottom: 100, left: 100 },
    fontSize: 14,
    lineWidth: 3,
  },
};

function formatDate(timestamp: number, interval: Interval): string {
  const date = new Date(timestamp * 1000);
  if (interval === "1D") {
    return date.toLocaleTimeString("en-US", {
      hour: "numeric",
      minute: "2-digit",
      hour12: true,
    });
  }
  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
  });
}

function formatPrice(value: number): string {
  return `$${value.toFixed(2)}`;
}

export function ChartExportCanvas({
  data,
  interval,
  quality,
  isRecording,
  onComplete,
  onError,
}: ChartExportCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationRef = useRef<number | null>(null);
  const progressRef = useRef(0);

  const dims = QUALITY_DIMS[quality];

  // Get chart data using existing utility
  const { area, hist } = getChartSeries(data, interval);

  const drawGrid = useCallback(
    (ctx: CanvasRenderingContext2D, chartArea: {
      x: number;
      y: number;
      width: number;
      height: number;
    }, minValue: number, maxValue: number) => {
      ctx.strokeStyle = COLORS.grid;
      ctx.lineWidth = 1;

      // Horizontal grid lines (6 lines)
      const hSteps = 6;
      for (let i = 0; i <= hSteps; i++) {
        const y = chartArea.y + (chartArea.height * i) / hSteps;
        ctx.beginPath();
        ctx.moveTo(chartArea.x, y);
        ctx.lineTo(chartArea.x + chartArea.width, y);
        ctx.stroke();
      }

      // Vertical grid lines (8 lines)
      const vSteps = 8;
      for (let i = 0; i <= vSteps; i++) {
        const x = chartArea.x + (chartArea.width * i) / vSteps;
        ctx.beginPath();
        ctx.moveTo(x, chartArea.y);
        ctx.lineTo(x, chartArea.y + chartArea.height);
        ctx.stroke();
      }
    },
    [],
  );

  const drawLabels = useCallback(
    (ctx: CanvasRenderingContext2D, chartArea: {
      x: number;
      y: number;
      width: number;
      height: number;
    }, minValue: number, maxValue: number, points: LWPoint[]) => {
      ctx.font = `${dims.fontSize}px "JetBrains Mono", "Fira Code", monospace`;
      ctx.textAlign = "right";
      ctx.textBaseline = "middle";

      // Price labels (right side)
      const hSteps = 6;
      for (let i = 0; i <= hSteps; i++) {
        const value = minValue + ((maxValue - minValue) * (hSteps - i)) / hSteps;
        const y = chartArea.y + (chartArea.height * i) / hSteps;
        ctx.fillStyle = COLORS.text;
        ctx.fillText(formatPrice(value), chartArea.x + chartArea.width + dims.padding.right - 10, y);
      }

      // Time labels (bottom)
      ctx.textAlign = "center";
      ctx.textBaseline = "top";
      const vSteps = Math.min(points.length - 1, 6);
      for (let i = 0; i <= vSteps; i++) {
        const pointIndex = Math.floor(((points.length - 1) * i) / vSteps);
        const point = points[pointIndex];
        const x = chartArea.x + (chartArea.width * i) / vSteps;
        ctx.fillStyle = COLORS.text;
        ctx.fillText(formatDate(point.time, interval), x, chartArea.y + chartArea.height + 10);
      }
    },
    [dims.fontSize, interval],
  );

  const drawAreaChart = useCallback(
    (ctx: CanvasRenderingContext2D, chartArea: {
      x: number;
      y: number;
      width: number;
      height: number;
    }, points: LWPoint[], minValue: number, maxValue: number, progress: number) => {
      if (points.length === 0) return;

      const visiblePoints = Math.max(1, Math.floor(points.length * progress));
      const visibleData = points.slice(0, visiblePoints);

      // Create gradient for fill
      const gradient = ctx.createLinearGradient(0, chartArea.y, 0, chartArea.y + chartArea.height);
      gradient.addColorStop(0, "rgba(217, 119, 6, 0.25)");
      gradient.addColorStop(1, "rgba(217, 119, 6, 0.02)");

      // Draw filled area
      ctx.beginPath();
      ctx.moveTo(chartArea.x, chartArea.y + chartArea.height);

      for (const point of visibleData) {
        const x =
          chartArea.x +
          ((point.time - points[0].time) / (points[points.length - 1].time - points[0].time)) *
            chartArea.width;
        const y =
          chartArea.y +
          chartArea.height -
          ((point.value - minValue) / (maxValue - minValue)) * chartArea.height;
        ctx.lineTo(x, y);
      }

      if (visibleData.length > 0) {
        const lastPoint = visibleData[visibleData.length - 1];
        const lastX =
          chartArea.x +
          ((lastPoint.time - points[0].time) / (points[points.length - 1].time - points[0].time)) *
            chartArea.width;
        ctx.lineTo(lastX, chartArea.y + chartArea.height);
      }

      ctx.closePath();
      ctx.fillStyle = gradient;
      ctx.fill();

      // Draw line on top
      if (visibleData.length > 1) {
        ctx.beginPath();
        const first = visibleData[0];
        const firstX =
          chartArea.x +
          ((first.time - points[0].time) / (points[points.length - 1].time - points[0].time)) *
            chartArea.width;
        const firstY =
          chartArea.y +
          chartArea.height -
          ((first.value - minValue) / (maxValue - minValue)) * chartArea.height;
        ctx.moveTo(firstX, firstY);

        for (let i = 1; i < visibleData.length; i++) {
          const point = visibleData[i];
          const x =
            chartArea.x +
            ((point.time - points[0].time) / (points[points.length - 1].time - points[0].time)) *
              chartArea.width;
          const y =
            chartArea.y +
            chartArea.height -
            ((point.value - minValue) / (maxValue - minValue)) * chartArea.height;
          ctx.lineTo(x, y);
        }

        ctx.strokeStyle = COLORS.amber;
        ctx.lineWidth = dims.lineWidth;
        ctx.lineCap = "round";
        ctx.lineJoin = "round";
        ctx.stroke();
      }
    },
    [dims.lineWidth],
  );

  const drawHistogram = useCallback(
    (ctx: CanvasRenderingContext2D, chartArea: {
      x: number;
      y: number;
      width: number;
      height: number;
    }, histData: LWHistPoint[], progress: number) => {
      if (histData.length === 0) return;

      const visiblePoints = Math.max(1, Math.floor(histData.length * progress));
      const visibleData = histData.slice(0, visiblePoints);

      // Find max absolute value for scaling
      const maxValue = Math.max(...histData.map((p) => Math.abs(p.value)), 0.01);
      const zeroY = chartArea.y + chartArea.height / 2;

      const barWidth = (chartArea.width / histData.length) * 0.6;

      for (let i = 0; i < visibleData.length; i++) {
        const point = visibleData[i];
        const x = chartArea.x + (i / histData.length) * chartArea.width + barWidth * 0.3;
        const barHeight = (Math.abs(point.value) / maxValue) * (chartArea.height / 2);

        const y = point.value >= 0 ? zeroY - barHeight : zeroY;

        const color =
          point.value >= 0 ? "rgba(22, 163, 74, 0.65)" : "rgba(220, 38, 38, 0.65)";

        ctx.fillStyle = color;
        ctx.fillRect(x, y, barWidth, barHeight);
      }
    },
    [],
  );

  const drawTitle = useCallback(
    (ctx: CanvasRenderingContext2D, chartArea: {
      x: number;
      y: number;
      width: number;
      height: number;
    }, currentNav: number) => {
      // Title
      ctx.font = `bold ${dims.fontSize + 2}px "JetBrains Mono", "Fira Code", monospace`;
      ctx.textAlign = "left";
      ctx.textBaseline = "top";
      ctx.fillStyle = COLORS.text;
      ctx.fillText("PORTFOLIO VALUE", chartArea.x, 15);

      // Current NAV value
      ctx.font = `bold ${dims.fontSize + 4}px "JetBrains Mono", "Fira Code", monospace`;
      ctx.fillStyle = COLORS.amber;
      ctx.fillText(formatPrice(currentNav), chartArea.x, 15 + dims.fontSize + 6);

      // P&L label
      ctx.font = `${dims.fontSize}px "JetBrains Mono", "Fira Code", monospace`;
      ctx.fillStyle = COLORS.text;
      ctx.fillText("DAILY P&L", chartArea.x, chartArea.y + chartArea.height + 35);
    },
    [dims.fontSize],
  );

  const drawFrame = useCallback(
    (canvas: HTMLCanvasElement, progress: number) => {
      const ctx = canvas.getContext("2d");
      if (!ctx) return;

      // Clear and set background
      ctx.fillStyle = COLORS.bg;
      ctx.fillRect(0, 0, dims.width, dims.height);

      if (area.length === 0) return;

      // Calculate value ranges
      const values = area.map((p) => p.value);
      const minValue = Math.min(...values) * 0.99;
      const maxValue = Math.max(...values) * 1.01;
      const currentNav = area[area.length - 1]?.value ?? 0;

      // Main chart area (65% of height)
      const mainChartArea = {
        x: dims.padding.left,
        y: dims.padding.top + 50,
        width: dims.width - dims.padding.left - dims.padding.right,
        height: (dims.height - dims.padding.top - dims.padding.bottom) * 0.65 - 50,
      };

      // Histogram area (35% of height)
      const histChartArea = {
        x: dims.padding.left,
        y: mainChartArea.y + mainChartArea.height + 40,
        width: mainChartArea.width,
        height: (dims.height - dims.padding.top - dims.padding.bottom) * 0.35 - 40,
      };

      // Draw main chart
      drawGrid(ctx, mainChartArea, minValue, maxValue);
      drawLabels(ctx, mainChartArea, minValue, maxValue, area);
      drawAreaChart(ctx, mainChartArea, area, minValue, maxValue, progress);
      drawTitle(ctx, mainChartArea, currentNav);

      // Draw histogram
      if (hist.length > 0) {
        drawHistogram(ctx, histChartArea, hist, progress);
      }
    },
    [area, hist, dims, drawGrid, drawLabels, drawAreaChart, drawHistogram, drawTitle],
  );

  // Handle animation when recording starts
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    // Set canvas dimensions
    canvas.width = dims.width;
    canvas.height = dims.height;

    if (isRecording) {
      progressRef.current = 0;
      let startTime: number | null = null;

      const animate = (timestamp: number) => {
        if (!startTime) startTime = timestamp;
        const elapsed = timestamp - startTime;
        const duration = 4000; // 4s animation
        progressRef.current = Math.min(elapsed / duration, 1);

        drawFrame(canvas, progressRef.current);

        if (progressRef.current < 1) {
          animationRef.current = requestAnimationFrame(animate);
        } else {
          // Animation complete
          setTimeout(() => {
            onComplete();
          }, 100);
        }
      };

      animationRef.current = requestAnimationFrame(animate);
    } else {
      // Reset to fully drawn state when not recording
      progressRef.current = 1;
      drawFrame(canvas, 1);
    }

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [isRecording, drawFrame, onComplete, dims.width, dims.height]);

  // Initial draw
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || isRecording) return;

    canvas.width = dims.width;
    canvas.height = dims.height;
    drawFrame(canvas, 1);
  }, [drawFrame, isRecording, dims.width, dims.height]);

  // Handle data changes when not recording
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || isRecording) return;

    canvas.width = dims.width;
    canvas.height = dims.height;
    drawFrame(canvas, 1);
  }, [data, interval, drawFrame, isRecording, dims.width, dims.height]);

  return (
    <canvas
      ref={canvasRef}
      style={{
        position: "absolute",
        left: "-9999px",
        top: "-9999px",
        visibility: isRecording ? "visible" : "hidden",
        pointerEvents: "none",
      }}
      aria-hidden="true"
    />
  );
}

"use client";

import { useEffect, useRef, useState } from "react";
import type { IChartApi, ISeriesApi } from "lightweight-charts";
import type { ChartDataPoint } from "@/lib/types";
import { getChartSeries, type Interval } from "@/lib/chart-utils";
import { RangeSwitcher } from "./range-switcher";

// Colors matched to the Coliseum design system
const C = {
  bg: "#07060a",
  grid: "#1a1728",
  text: "#8e8b98",
  crosshair: "#d97706",
  crosshairLabel: "#b45309",
  positive: "#16a34a",
  negative: "#dc2626",
  amber: "#d97706",
} as const;

interface LWPortfolioChartProps {
  data: ChartDataPoint[];
  interval: Interval;
  onIntervalChange: (interval: Interval) => void;
  totalPnl: number;
}

export function LWPortfolioChart({
  data,
  interval,
  onIntervalChange,
  totalPnl,
}: LWPortfolioChartProps) {
  const mainRef = useRef<HTMLDivElement>(null);
  const histRef = useRef<HTMLDivElement>(null);
  const mainChartRef = useRef<IChartApi | null>(null);
  const histChartRef = useRef<IChartApi | null>(null);
  const baselineRef = useRef<ISeriesApi<"Baseline"> | null>(null);
  const histSeriesRef = useRef<ISeriesApi<"Histogram"> | null>(null);
  const [chartsReady, setChartsReady] = useState(false);

  // Initialize charts once on mount
  useEffect(() => {
    if (!mainRef.current || !histRef.current) return;
    let cancelled = false;

    (async () => {
      const {
        createChart,
        BaselineSeries,
        HistogramSeries,
        ColorType,
        CrosshairMode,
        LineStyle,
      } = await import("lightweight-charts");

      if (cancelled || !mainRef.current || !histRef.current) return;

      const sharedLayout = {
        layout: {
          textColor: C.text,
          background: { type: ColorType.Solid, color: C.bg },
          fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
        },
        grid: {
          vertLines: { visible: false },
          horzLines: { color: C.grid },
        },
        crosshair: {
          mode: CrosshairMode.Normal,
          vertLine: {
            color: `${C.crosshair}55`,
            width: 1 as const,
            style: LineStyle.Dashed,
            labelBackgroundColor: C.crosshairLabel,
          },
          horzLine: {
            color: `${C.crosshair}55`,
            width: 1 as const,
            style: LineStyle.Dashed,
            labelBackgroundColor: C.crosshairLabel,
          },
        },
        rightPriceScale: {
          borderVisible: false,
          scaleMargins: { top: 0.12, bottom: 0.08 },
        },
        autoSize: true,
        handleScroll: true,
        handleScale: true,
      };

      const priceFormatter = (price: number) =>
        `${price >= 0 ? "+" : "-"}$${Math.abs(price).toFixed(2)}`;

      // Main chart — time scale hidden (histogram shows it below)
      const mainChart = createChart(mainRef.current, {
        ...sharedLayout,
        timeScale: {
          visible: false,
          borderVisible: false,
          fixLeftEdge: true,
          fixRightEdge: true,
        },
        localization: { priceFormatter },
      });

      // Histogram chart — shows time axis
      const histChart = createChart(histRef.current, {
        ...sharedLayout,
        crosshair: {
          ...sharedLayout.crosshair,
          horzLine: { visible: false, labelVisible: false },
        },
        timeScale: {
          borderVisible: false,
          fixLeftEdge: true,
          fixRightEdge: true,
          timeVisible: false,
        },
        rightPriceScale: {
          borderVisible: false,
          scaleMargins: { top: 0.2, bottom: 0.05 },
        },
        localization: { priceFormatter },
      });

      // Baseline series: green above 0, red below 0
      const baselineSeries = mainChart.addSeries(BaselineSeries, {
        baseValue: { type: "price", price: 0 },
        topLineColor: C.positive,
        topFillColor1: "rgba(22, 163, 74, 0.25)",
        topFillColor2: "rgba(22, 163, 74, 0.04)",
        bottomLineColor: C.negative,
        bottomFillColor1: "rgba(220, 38, 38, 0.04)",
        bottomFillColor2: "rgba(220, 38, 38, 0.25)",
        lineWidth: 2,
        lastValueVisible: true,
        priceLineVisible: false,
        crosshairMarkerVisible: true,
        crosshairMarkerRadius: 4,
        crosshairMarkerBorderColor: C.amber,
        crosshairMarkerBackgroundColor: C.bg,
        crosshairMarkerBorderWidth: 2,
      });

      // Histogram for daily P&L bars
      const histSeries = histChart.addSeries(HistogramSeries, {
        priceScaleId: "right",
        priceLineVisible: false,
        lastValueVisible: false,
        base: 0,
      });

      mainChartRef.current = mainChart;
      histChartRef.current = histChart;
      baselineRef.current = baselineSeries;
      histSeriesRef.current = histSeries;

      // Bidirectional time scale sync
      let syncing = false;
      mainChart.timeScale().subscribeVisibleTimeRangeChange((range) => {
        if (syncing || !range) return;
        syncing = true;
        try {
          histChart.timeScale().setVisibleRange(range);
        } catch {
          // lightweight-charts throws when range contains null time values (empty chart)
        }
        syncing = false;
      });
      histChart.timeScale().subscribeVisibleTimeRangeChange((range) => {
        if (syncing || !range) return;
        syncing = true;
        try {
          mainChart.timeScale().setVisibleRange(range);
        } catch {
          // lightweight-charts throws when range contains null time values (empty chart)
        }
        syncing = false;
      });

      setChartsReady(true);
    })();

    return () => {
      cancelled = true;
      setChartsReady(false);
      mainChartRef.current?.remove();
      histChartRef.current?.remove();
      mainChartRef.current = null;
      histChartRef.current = null;
      baselineRef.current = null;
      histSeriesRef.current = null;
    };
  }, []);

  // Update data whenever chartsReady, data, or interval changes
  useEffect(() => {
    if (!chartsReady || !baselineRef.current || !histSeriesRef.current) return;

    const { area: areaData, hist: histData } = getChartSeries(data, interval);

    baselineRef.current.setData(areaData);
    histSeriesRef.current.setData(histData);

    if (areaData.length > 0) {
      mainChartRef.current?.timeScale().fitContent();
      histChartRef.current?.timeScale().fitContent();
    }
  }, [chartsReady, data, interval]);

  const isEmpty = data.length === 0;

  return (
    <div className="flex flex-col h-full min-h-0">
      {/* Chart toolbar */}
      <div className="flex items-center justify-between px-5 h-10 border-b border-border shrink-0">
        <div className="flex items-baseline gap-2.5">
          <span className="text-[9px] font-mono text-muted-foreground/70 tracking-[0.14em] uppercase">
            Cumulative P&L
          </span>
          {!isEmpty && (
            <span
              className={`text-sm font-mono font-semibold tabular-nums ${
                totalPnl >= 0 ? "text-emerald-400" : "text-red-400"
              }`}
            >
              {totalPnl >= 0 ? "+" : ""}
              {totalPnl.toFixed(2)}
            </span>
          )}
        </div>
        <RangeSwitcher value={interval} onChange={onIntervalChange} />
      </div>

      {/* Baseline chart — takes 65% of the chart area */}
      <div ref={mainRef} className="flex-[13] min-h-0 relative">
        {isEmpty && (
          <div className="absolute inset-0 flex items-center justify-center">
            <p className="text-[11px] font-mono text-muted-foreground/70 tracking-[0.14em]">
              NO TRADE DATA YET
            </p>
          </div>
        )}
      </div>

      {/* Histogram section header */}
      <div className="flex items-center px-5 h-7 border-t border-border shrink-0">
        <span className="text-[8px] font-mono text-muted-foreground/70 tracking-[0.14em] uppercase">
          Daily P&L
        </span>
      </div>

      {/* Histogram — takes 35% of the chart area */}
      <div ref={histRef} className="flex-[7] min-h-0" />
    </div>
  );
}

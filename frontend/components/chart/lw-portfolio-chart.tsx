"use client";

import { useEffect, useRef, useState } from "react";
import type { IChartApi, ISeriesApi, UTCTimestamp } from "lightweight-charts";
import { Download, Loader2 } from "lucide-react";
import type { ChartDataPoint } from "@/lib/types";
import { getChartSeries, type Interval } from "@/lib/chart-utils";
import { downloadChartExport } from "@/lib/api";
import { RangeSwitcher } from "./range-switcher";
import { FontSize } from "@/lib/typography";
import { Muted } from "@/lib/styles";

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
  currentNav: number;
}

export function LWPortfolioChart({
  data,
  interval,
  onIntervalChange,
  currentNav,
}: LWPortfolioChartProps) {
  const mainRef = useRef<HTMLDivElement>(null);
  const histRef = useRef<HTMLDivElement>(null);
  const mainChartRef = useRef<IChartApi | null>(null);
  const histChartRef = useRef<IChartApi | null>(null);
  const areaSeriesRef = useRef<ISeriesApi<"Area"> | null>(null);
  const histSeriesRef = useRef<ISeriesApi<"Histogram"> | null>(null);
  const [chartsReady, setChartsReady] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [exportError, setExportError] = useState<string | null>(null);

  useEffect(() => {
    if (!mainRef.current || !histRef.current) return;
    let cancelled = false;

    (async () => {
      const {
        createChart,
        AreaSeries,
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

      const navFormatter = (price: number) => `$${price.toFixed(2)}`;
      const pnlFormatter = (price: number) =>
        `${price >= 0 ? "+" : "-"}$${Math.abs(price).toFixed(2)}`;

      const mainChart = createChart(mainRef.current, {
        ...sharedLayout,
        timeScale: {
          visible: false,
          borderVisible: false,
          fixLeftEdge: true,
          fixRightEdge: false,
          rightOffset: 5,
        },
        localization: { priceFormatter: navFormatter },
      });

      const histChart = createChart(histRef.current, {
        ...sharedLayout,
        crosshair: {
          ...sharedLayout.crosshair,
          horzLine: { visible: false, labelVisible: false },
        },
        timeScale: {
          borderVisible: false,
          fixLeftEdge: true,
          fixRightEdge: false,
          rightOffset: 5,
          timeVisible: false,
        },
        rightPriceScale: {
          borderVisible: false,
          scaleMargins: { top: 0.2, bottom: 0.05 },
        },
        localization: { priceFormatter: pnlFormatter },
      });

      const areaSeries = mainChart.addSeries(AreaSeries, {
        lineColor: C.amber,
        topColor: "rgba(217, 119, 6, 0.25)",
        bottomColor: "rgba(217, 119, 6, 0.02)",
        lineWidth: 2,
        lastValueVisible: true,
        priceLineVisible: false,
        crosshairMarkerVisible: true,
        crosshairMarkerRadius: 4,
        crosshairMarkerBorderColor: C.amber,
        crosshairMarkerBackgroundColor: C.bg,
        crosshairMarkerBorderWidth: 2,
      });

      const histSeries = histChart.addSeries(HistogramSeries, {
        priceScaleId: "right",
        priceLineVisible: false,
        lastValueVisible: false,
        base: 0,
      });

      mainChartRef.current = mainChart;
      histChartRef.current = histChart;
      areaSeriesRef.current = areaSeries;
      histSeriesRef.current = histSeries;

      let syncing = false;
      mainChart.timeScale().subscribeVisibleTimeRangeChange((range) => {
        if (syncing || !range) return;
        syncing = true;
        try {
          histChart.timeScale().setVisibleRange(range);
        } catch {
          // lightweight-charts throws when range contains null time values
        }
        syncing = false;
      });
      histChart.timeScale().subscribeVisibleTimeRangeChange((range) => {
        if (syncing || !range) return;
        syncing = true;
        try {
          mainChart.timeScale().setVisibleRange(range);
        } catch {
          // lightweight-charts throws when range contains null time values
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
      areaSeriesRef.current = null;
      histSeriesRef.current = null;
    };
  }, []);

  useEffect(() => {
    if (!chartsReady || !areaSeriesRef.current || !histSeriesRef.current)
      return;

    const { area: areaData, hist: histData } = getChartSeries(data, interval);

    areaSeriesRef.current.setData(
      areaData.map((point) => ({
        time: point.time as UTCTimestamp,
        value: point.value,
      })),
    );
    histSeriesRef.current.setData(
      histData.map((point) => ({
        time: point.time as UTCTimestamp,
        value: point.value,
        color: point.color,
      })),
    );

    histChartRef.current?.applyOptions({
      timeScale: { timeVisible: interval === "1D" },
    });

    if (areaData.length > 0) {
      mainChartRef.current?.timeScale().fitContent();
      histChartRef.current?.timeScale().fitContent();
    }
  }, [chartsReady, data, interval]);

  const isEmpty = data.length === 0;

  const handleExport = async () => {
    if (isExporting || isEmpty) return;
    setExportError(null);
    setIsExporting(true);

    try {
      const { blob, filename } = await downloadChartExport("mp4", "balanced");
      const objectUrl = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = objectUrl;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(objectUrl);
    } catch (error) {
      setExportError(
        error instanceof Error ? error.message : "Chart export failed"
      );
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div className="flex flex-col h-full min-h-0">
      {/* Chart toolbar */}
      <div className="flex items-center justify-between px-5 h-10 border-b border-border shrink-0">
        <div className="flex items-baseline gap-2.5">
          <span
            className={`${FontSize.small} font-mono ${Muted.mutedText} tracking-[0.14em] uppercase`}
          >
            Portfolio Value
          </span>
          {!isEmpty && (
            <span
              className={`${FontSize.medium} font-mono font-semibold tabular-nums text-amber-400`}
            >
              ${currentNav.toFixed(2)}
            </span>
          )}
        </div>
        <div className="flex items-center gap-3">
          {exportError && (
            <span
              className={`${FontSize.small} font-mono text-red-400 tracking-[0.08em]`}
            >
              {exportError}
            </span>
          )}
          <button
            onClick={handleExport}
            disabled={isExporting || isEmpty}
            title={isEmpty ? "No chart data to export" : "Download MP4"}
            className={`h-7 w-7 hidden sm:inline-flex items-center justify-center border border-border rounded transition-colors ${
              isExporting || isEmpty
                ? "text-muted-foreground/50 cursor-not-allowed"
                : `${Muted.mutedText} ${Muted.mutedTextHover}`
            }`}
          >
            {isExporting ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <Download className="h-3.5 w-3.5" />
            )}
          </button>
          <RangeSwitcher value={interval} onChange={onIntervalChange} />
        </div>
      </div>

      {/* Area chart -- takes 65% of the chart area */}
      <div ref={mainRef} className="flex-[13] min-h-0 relative">
        {isEmpty && (
          <div className="absolute inset-0 flex items-center justify-center">
            <p
              className={`${FontSize.medium} font-mono ${Muted.mutedText} tracking-[0.14em]`}
            >
              NO TRADE DATA YET
            </p>
          </div>
        )}
      </div>

      {/* Histogram section header */}
      <div className="flex items-center px-5 h-7 border-t border-border shrink-0">
        <span
          className={`${FontSize.small} font-mono ${Muted.mutedText} tracking-[0.14em] uppercase`}
        >
          Daily P&L
        </span>
      </div>

      {/* Histogram -- takes 35% of the chart area */}
      <div ref={histRef} className="flex-[7] min-h-0" />
    </div>
  );
}

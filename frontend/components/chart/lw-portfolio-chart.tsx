"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import type { IChartApi, ISeriesApi, UTCTimestamp } from "lightweight-charts";
import { Download, Loader2, Image as ImageIcon, Video } from "lucide-react";
import type { ChartDataPoint } from "@/lib/types";
import { getChartSeries, type Interval } from "@/lib/chart-utils";
import { RangeSwitcher } from "./range-switcher";
import { FontSize } from "@/lib/typography";
import { Muted } from "@/lib/styles";
import { useChartExport, type ChartExportFormat, type ChartExportQuality } from "@/hooks/use-chart-export";
import { ChartExportCanvas } from "./chart-export-canvas";

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

const QUALITY_LABELS: Record<ChartExportQuality, string> = {
  fast: "Fast",
  balanced: "Balanced",
  hq: "HQ",
};

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
  const [showExportMenu, setShowExportMenu] = useState(false);
  const canvasContainerRef = useRef<HTMLDivElement>(null);

  const {
    isRecording,
    progress,
    error: exportHookError,
    quality,
    format,
    setQuality,
    setFormat,
    startRecording,
    stopRecording,
    downloadBlob,
    getProfile,
    isSupported,
  } = useChartExport("mp4", "balanced");

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

  const handleExportComplete = useCallback(() => {
    // Handled by the startRecording promise
  }, []);

  const handleExportError = useCallback((errorMsg: string) => {
    setExportError(errorMsg);
    setIsExporting(false);
  }, []);

  const handleExport = async (selectedFormat: ChartExportFormat) => {
    if (isExporting || isEmpty || isRecording) return;
    
    setFormat(selectedFormat);
    setExportError(null);
    setIsExporting(true);
    setShowExportMenu(false);

    try {
      if (selectedFormat === "png") {
        // PNG export: draw to canvas and download immediately
        const profile = getProfile();
        const canvas = document.createElement("canvas");
        canvas.width = profile.width;
        canvas.height = profile.height;

        // Render full chart to canvas using the same logic
        const exportCanvas = canvasContainerRef.current?.querySelector("canvas");
        if (exportCanvas) {
          const ctx = canvas.getContext("2d");
          if (ctx) {
            // Copy the hidden canvas content
            ctx.drawImage(exportCanvas, 0, 0);
          }
        }

        // Convert to blob and download
        const blob = await new Promise<Blob | null>((resolve) => {
          canvas.toBlob(resolve, "image/png");
        });
        
        if (blob) {
          const timestamp = new Date().toISOString().replace(/[:.]/g, "-").slice(0, -5);
          const filename = `coliseum-portfolio-${timestamp}.png`;
          downloadBlob(blob, filename);
        } else {
          throw new Error("Failed to generate PNG");
        }
        setIsExporting(false);
      } else {
        // MP4 export: animate and record
        const exportCanvas = canvasContainerRef.current?.querySelector("canvas");
        if (!exportCanvas) {
          throw new Error("Export canvas not found");
        }

        const blob = await startRecording(exportCanvas as HTMLCanvasElement);
        const timestamp = new Date().toISOString().replace(/[:.]/g, "-").slice(0, -5);
        const filename = `coliseum-portfolio-${timestamp}.webm`;
        downloadBlob(blob, filename);
        setIsExporting(false);
      }
    } catch (error) {
      setExportError(
        error instanceof Error ? error.message : "Chart export failed"
      );
      setIsExporting(false);
    }
  };

  // Handle hook errors
  useEffect(() => {
    if (exportHookError) {
      setExportError(exportHookError);
      setIsExporting(false);
    }
  }, [exportHookError]);

  // Close export menu when clicking outside
  useEffect(() => {
    if (!showExportMenu) return;

    const handleClickOutside = (e: MouseEvent) => {
      const target = e.target as HTMLElement;
      if (!target.closest(".relative")) {
        setShowExportMenu(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [showExportMenu]);

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
          <div className="relative">
            <button
              onClick={() => setShowExportMenu(!showExportMenu)}
              disabled={isExporting || isEmpty || isRecording}
              title={isEmpty ? "No chart data to export" : "Export chart"}
              className={`h-7 w-7 hidden sm:inline-flex items-center justify-center border border-border rounded transition-colors ${
                isExporting || isEmpty || isRecording
                  ? "text-muted-foreground/50 cursor-not-allowed"
                  : `${Muted.mutedText} ${Muted.mutedTextHover}`
              }`}
            >
              {isExporting || isRecording ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
              ) : (
                <Download className="h-3.5 w-3.5" />
              )}
            </button>

            {/* Export menu dropdown */}
            {showExportMenu && !isExporting && !isRecording && (
              <div className="absolute right-0 top-full mt-1 z-50 min-w-[180px] bg-card border border-border rounded shadow-lg">
                {/* Format options */}
                <div className="p-1.5 border-b border-border">
                  <p className={`${FontSize.small} font-mono ${Muted.mutedText} px-2 py-1`}>Format</p>
                  <button
                    onClick={() => handleExport("png")}
                    className={`w-full flex items-center gap-2 px-2 py-1.5 text-left rounded ${FontSize.small} font-mono ${Muted.mutedText} hover:bg-amber-500/5`}
                  >
                    <ImageIcon className="h-3.5 w-3.5" />
                    PNG Image
                  </button>
                  <button
                    onClick={() => handleExport("mp4")}
                    disabled={!isSupported}
                    className={`w-full flex items-center gap-2 px-2 py-1.5 text-left rounded ${FontSize.small} font-mono ${Muted.mutedText} hover:bg-amber-500/5 disabled:opacity-50`}
                  >
                    <Video className="h-3.5 w-3.5" />
                    MP4 Video
                    {!isSupported && <span className="ml-auto text-[10px] text-red-400">N/A</span>}
                  </button>
                </div>

                {/* Quality options */}
                <div className="p-1.5">
                  <p className={`${FontSize.small} font-mono ${Muted.mutedText} px-2 py-1`}>Quality</p>
                  <div className="flex gap-1 px-2">
                    {(["fast", "balanced", "hq"] as ChartExportQuality[]).map((q) => (
                      <button
                        key={q}
                        onClick={() => setQuality(q)}
                        className={`flex-1 px-2 py-1 rounded ${FontSize.small} font-mono transition-colors ${
                          quality === q
                            ? "bg-amber-500/20 text-amber-500"
                            : `${Muted.mutedText} hover:bg-amber-500/5`
                        }`}
                      >
                        {QUALITY_LABELS[q]}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
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

      {/* Hidden export canvas component */}
      <div ref={canvasContainerRef} className="sr-only">
        <ChartExportCanvas
          data={data}
          interval={interval}
          quality={quality}
          isRecording={isRecording}
          onComplete={handleExportComplete}
          onError={handleExportError}
        />
      </div>

      {/* Recording progress overlay */}
      {isRecording && (
        <div className="absolute inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-card border border-border rounded p-4 text-center">
            <Loader2 className="h-6 w-6 animate-spin mx-auto mb-2 text-amber-500" />
            <p className={`${FontSize.small} font-mono ${Muted.mutedText}`}>Recording...</p>
            <div className="w-32 h-1 bg-border rounded-full mt-2 overflow-hidden">
              <div
                className="h-full bg-amber-500 transition-all"
                style={{ width: `${progress}%` }}
              />
            </div>
            <p className={`${FontSize.small} font-mono text-amber-500 mt-1`}>{Math.round(progress)}%</p>
          </div>
        </div>
      )}
    </div>
  );
}

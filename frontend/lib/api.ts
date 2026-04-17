const API_BASE = process.env.NEXT_PUBLIC_API_URL || "https://coliseumapi.manitmishra.com";

// NOTE: Client-side export is now the preferred method.
// These types are kept for backward compatibility with the hook system.
export type ChartExportFormat = "mp4" | "png";
export type ChartExportQuality = "fast" | "balanced" | "hq";

// DEPRECATED: Backend chart export is now handled client-side.
// Use the useChartExport hook from @/hooks/use-chart-export instead.
// This function is kept for backward compatibility but should be avoided.
export async function downloadChartExport(
  format: ChartExportFormat = "mp4",
  quality: ChartExportQuality = "balanced",
): Promise<{ blob: Blob; filename: string }> {
  const params = new URLSearchParams({ format: format === "mp4" ? "mp4" : "png", quality });
  const res = await fetch(`${API_BASE}/api/chart/export?${params.toString()}`);

  if (!res.ok) {
    let detail = `Export failed (${res.status})`;
    try {
      const payload = (await res.json()) as { detail?: string };
      if (payload.detail) detail = payload.detail;
    } catch {
      // no-op: fallback to status message
    }
    throw new Error(detail);
  }

  const contentDisposition = res.headers.get("Content-Disposition");
  const filename =
    contentDisposition?.match(/filename="?([^";]+)"?/i)?.[1] ??
    `coliseum-portfolio.${format === "mp4" ? "webm" : "png"}`;

  return { blob: await res.blob(), filename };
}

export async function fetcher<T>(url: string): Promise<T> {
  const res = await fetch(`${API_BASE}${url}`);
  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export async function post<T>(url: string): Promise<T> {
  const res = await fetch(`${API_BASE}${url}`, { method: "POST" });
  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

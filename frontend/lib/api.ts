const API_BASE = process.env.NEXT_PUBLIC_API_URL || "https://coliseumapi.manitmishra.com";

export type ChartExportFormat = "mp4";
export type ChartExportQuality = "fast" | "balanced" | "hq";

function parseDownloadFilename(contentDisposition: string | null): string | null {
  if (!contentDisposition) return null;
  const match = contentDisposition.match(/filename="?([^";]+)"?/i);
  return match?.[1] ?? null;
}

export async function downloadChartExport(
  format: ChartExportFormat = "mp4",
  quality: ChartExportQuality = "balanced",
): Promise<{ blob: Blob; filename: string }> {
  const params = new URLSearchParams({ format, quality });
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

  const filename =
    parseDownloadFilename(res.headers.get("Content-Disposition")) ??
    `coliseum-portfolio.${format}`;

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

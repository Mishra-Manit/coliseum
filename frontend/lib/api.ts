import type { Interval } from "./chart-utils";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "https://coliseumapi.manitmishra.com";

function parseDownloadFilename(contentDisposition: string | null): string | null {
  if (!contentDisposition) return null;
  const match = contentDisposition.match(/filename="?([^";]+)"?/i);
  return match?.[1] ?? null;
}

export async function downloadChartExport(
  interval: Interval = "1M",
): Promise<{ blob: Blob; filename: string }> {
  const params = new URLSearchParams({ interval });
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
    `coliseum-portfolio.${interval.toLowerCase()}.mp4`;

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

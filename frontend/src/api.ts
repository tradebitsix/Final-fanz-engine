const API_BASE = (import.meta as any).env.VITE_API_BASE_URL || "http://localhost:8000";
const API_KEY = (import.meta as any).env.VITE_API_KEY || "";

function headers() {
  const h: Record<string,string> = { "Content-Type": "application/json" };
  if (API_KEY) h["X-API-Key"] = API_KEY;
  return h;
}

export async function health() {
  const r = await fetch(`${API_BASE}/health`);
  if (!r.ok) throw new Error(`Health failed: ${r.status}`);
  return r.json();
}

export async function convert(raw_input: string, mode: string) {
  const r = await fetch(`${API_BASE}/engine/convert`, {
    method: "POST",
    headers: headers(),
    body: JSON.stringify({ raw_input, mode }),
  });
  if (!r.ok) throw new Error(`Convert failed: ${r.status}`);
  return r.json();
}

export async function getArtifact(id: string) {
  const r = await fetch(`${API_BASE}/engine/artifacts/${encodeURIComponent(id)}`, {
    method: "GET",
    headers: headers(),
  });
  if (!r.ok) throw new Error(`Get artifact failed: ${r.status}`);
  return r.json();
}

export async function createExportToken(artifact_id: string) {
  const r = await fetch(`${API_BASE}/engine/export-token`, {
    method: "POST",
    headers: headers(),
    body: JSON.stringify({ artifact_id, ttl_seconds: 600 }),
  });
  if (!r.ok) throw new Error(`Token failed: ${r.status}`);
  return r.json();
}

export function downloadUrl(token: string) {
  return `${API_BASE}/engine/download/${encodeURIComponent(token)}`;
}

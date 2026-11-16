with open('frontend/services/api.ts', 'r', encoding='utf-8') as f:
    c = f.read().replace('\r\n', '\n')

old = """export async function discoverTimeSeries(params: {
  ra: number;
  dec: number;
  fov_deg?: number;
  release?: string;
}): Promise<any> {
  const query = new URLSearchParams();
  query.set("ra", params.ra.toString());
  query.set("dec", params.dec.toString());
  if (params.fov_deg !== undefined) query.set("fov_deg", params.fov_deg.toString());
  if (params.release) query.set("release", params.release);

  const resp = await fetch(`${getApiBaseUrl()}/temporal/discovery?${query.toString()}`);
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ detail: "Discovery query failed" }));
    throw new Error(err.detail || "Time-series discovery failed");
  }
  return resp.json();
}"""

new = """export async function discoverTimeSeries(params: {
  ra: number;
  dec: number;
  fov_deg?: number;
  release?: string;
  use_cache?: boolean;
  force_refresh?: boolean;
  signal?: AbortSignal;
}): Promise<any> {
  const query = new URLSearchParams();
  query.set("ra", params.ra.toString());
  query.set("dec", params.dec.toString());
  if (params.fov_deg !== undefined) query.set("fov_deg", params.fov_deg.toString());
  if (params.release) query.set("release", params.release);
  if (params.use_cache !== undefined) query.set("use_cache", params.use_cache.toString());
  if (params.force_refresh !== undefined) query.set("force_refresh", params.force_refresh.toString());

  const resp = await fetch(`${getApiBaseUrl()}/temporal/discovery?${query.toString()}`, {
    signal: params.signal,
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ detail: `Discovery query failed (HTTP ${resp.status})` }));
    throw new Error(err.detail || `Time-series discovery failed (HTTP ${resp.status})`);
  }
  return resp.json();
}"""

assert old in c, "Target string not found in api.ts"
c = c.replace(old, new)
with open('frontend/services/api.ts', 'w', encoding='utf-8') as f:
    f.write(c)
print("api.ts patched successfully")

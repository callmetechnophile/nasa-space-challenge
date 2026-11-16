/**
 * Resolves the API base URL based on runtime environment:
 * 1. NEXT_PUBLIC_API_BASE_URL (Azure Container Apps backend URL)
 * 2. NEXT_PUBLIC_API_URL (legacy / local explicit override)
 * 3. Server-side runtime with BACKEND_URL
 * 4. Client-side browser runtime: fallback to origin or local development
 */
export function getApiBaseUrl(): string {
  // Check NEXT_PUBLIC_API_BASE_URL first, then fallback to NEXT_PUBLIC_API_URL
  const rawUrl = process.env.NEXT_PUBLIC_API_BASE_URL || process.env.NEXT_PUBLIC_API_URL;
  if (rawUrl) {
    const cleanUrl = rawUrl.replace(/^\uFEFF/, "").trim().replace(/\/$/, "");
    return cleanUrl.endsWith("/api/v1") ? cleanUrl : `${cleanUrl}/api/v1`;
  }

  // Server-side runtime (e.g. Next.js server actions, route handlers, SSR)
  if (typeof window === "undefined") {
    if (process.env.BACKEND_URL) {
      const cleanBackend = process.env.BACKEND_URL.replace(/\/$/, "");
      return cleanBackend.endsWith("/api/v1") ? cleanBackend : `${cleanBackend}/api/v1`;
    }
    return "http://127.0.0.1:8000/api/v1";
  }

  // Client-side browser runtime in local development
  if (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1") {
    return "http://127.0.0.1:8000/api/v1";
  }

  // In production if no NEXT_PUBLIC_API_BASE_URL is set, route via current origin
  return `${window.location.origin}/api/v1`;
}

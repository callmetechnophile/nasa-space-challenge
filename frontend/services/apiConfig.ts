/**
 * Resolves the API base URL based on runtime environment:
 * 1. Explicit NEXT_PUBLIC_API_URL (if provided)
 * 2. Server-side runtime with Vercel service binding BACKEND_URL
 * 3. Client-side browser runtime: `${window.location.origin}/api/v1` (routed by Vercel rewrites to backend)
 * 4. Local development fallback: "http://127.0.0.1:8000/api/v1"
 */
export function getApiBaseUrl(): string {
  if (process.env.NEXT_PUBLIC_API_URL) {
    return process.env.NEXT_PUBLIC_API_URL.replace(/\/$/, "");
  }

  // Server-side runtime (e.g. Next.js server actions, route handlers, SSR)
  if (typeof window === "undefined") {
    if (process.env.BACKEND_URL) {
      return `${process.env.BACKEND_URL.replace(/\/$/, "")}/api/v1`;
    }
    return "http://127.0.0.1:8000/api/v1";
  }

  // Client-side browser runtime (uses current window origin, routed by Vercel rewrites)
  return `${window.location.origin}/api/v1`;
}

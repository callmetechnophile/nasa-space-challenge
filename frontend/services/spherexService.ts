/**
 * SPHEREx Archive API Service (Milestone 4).
 * Communicates with backend /api/v1/spherex endpoints to search IRSA SIA2,
 * download products, inspect MEF HDUs, and load real astronomical layers.
 */

import {
  SpherexSearchRequest,
  SpherexSearchResponse,
  SpherexDownloadRequest,
  SpherexDownloadResponse,
  SpherexMefInspection,
  SpherexLayerLoadRequest,
  SpherexLayerPayload,
  SpherexCacheStatus,
} from "../types/spherex";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api/v1";

export class SpherexService {
  /**
   * Search NASA/IPAC IRSA SIA2 archive for real SPHEREx observations.
   */
  static async searchObservations(request: SpherexSearchRequest): Promise<SpherexSearchResponse> {
    const response = await fetch(`${API_BASE_URL}/spherex/search`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const err = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(err.detail || `Search failed with status ${response.status}`);
    }

    return response.json();
  }

  /**
   * Stream download a real SPHEREx FITS product to server storage.
   */
  static async downloadProduct(request: SpherexDownloadRequest): Promise<SpherexDownloadResponse> {
    const response = await fetch(`${API_BASE_URL}/spherex/download`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const err = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(err.detail || `Download failed with status ${response.status}`);
    }

    return response.json();
  }

  /**
   * Inspect all extensions and header cards of a cached SPHEREx MEF file.
   */
  static async inspectProduct(filename: string): Promise<SpherexMefInspection> {
    const response = await fetch(`${API_BASE_URL}/spherex/inspect/${encodeURIComponent(filename)}`);

    if (!response.ok) {
      const err = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(err.detail || `Inspection failed with status ${response.status}`);
    }

    return response.json();
  }

  /**
   * Process a real SPHEREx FITS file into a 3D spherical mesh and texture layer payload.
   */
  static async loadLayer(request: SpherexLayerLoadRequest): Promise<SpherexLayerPayload> {
    const response = await fetch(`${API_BASE_URL}/spherex/load-layer`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const err = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(err.detail || `Layer load failed with status ${response.status}`);
    }

    return response.json();
  }

  /**
   * Fetch current cache inventory and storage limits.
   */
  static async getCacheStatus(): Promise<SpherexCacheStatus> {
    const response = await fetch(`${API_BASE_URL}/spherex/status`);

    if (!response.ok) {
      throw new Error(`Failed to fetch cache status: ${response.statusText}`);
    }

    return response.json();
  }
}

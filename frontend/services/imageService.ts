/**
 * Astronomical Image API Client Service (Milestone 3).
 * Interacts with the FastAPI backend for FITS ingestion, WCS mesh calculation,
 * and display-stretched textures.
 */

import {
  SampleImageInfo,
  AstronomicalImageLayerData,
  DisplayStretchType,
} from "@/types/astronomicalImage";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api/v1";

export async function fetchSampleImages(): Promise<SampleImageInfo[]> {
  const res = await fetch(`${API_BASE_URL}/images/samples`);
  if (!res.ok) {
    throw new Error(`Failed to fetch sample images: HTTP ${res.status}`);
  }
  return await res.json();
}

export async function loadSampleImageLayer(
  sampleId: string,
  stretch: DisplayStretchType = "asinh",
  brightness: number = 1.0,
  contrast: number = 1.0,
  radius: number = 98.0
): Promise<AstronomicalImageLayerData> {
  const url = new URL(`${API_BASE_URL}/images/sample/${sampleId}`);
  url.searchParams.set("stretch", stretch);
  url.searchParams.set("brightness", brightness.toString());
  url.searchParams.set("contrast", contrast.toString());
  url.searchParams.set("radius", radius.toString());

  const res = await fetch(url.toString());
  if (!res.ok) {
    const errorText = await res.text();
    throw new Error(`Failed to load sample image layer: ${errorText || res.statusText}`);
  }
  return await res.json();
}

export async function uploadFitsImageLayer(
  file: File,
  stretch: DisplayStretchType = "asinh",
  brightness: number = 1.0,
  contrast: number = 1.0,
  radius: number = 98.0
): Promise<AstronomicalImageLayerData> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("stretch", stretch);
  formData.append("brightness", brightness.toString());
  formData.append("contrast", contrast.toString());
  formData.append("radius", radius.toString());

  const res = await fetch(`${API_BASE_URL}/images/process-fits`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const errorJson = await res.json().catch(() => ({ detail: "Upload failed" }));
    throw new Error(errorJson.detail || `Upload failed with status ${res.status}`);
  }
  return await res.json();
}

export async function updateImageDisplayStretch(
  layerId: string,
  stretch: DisplayStretchType,
  brightness: number = 1.0,
  contrast: number = 1.0
): Promise<string> {
  const res = await fetch(`${API_BASE_URL}/images/re-stretch`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      layer_id: layerId,
      stretch,
      brightness,
      contrast,
    }),
  });

  if (!res.ok) {
    throw new Error(`Failed to re-stretch image layer: HTTP ${res.status}`);
  }

  const data = await res.json();
  return data.texture_data_uri;
}

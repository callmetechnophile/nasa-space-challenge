"use client";

import React, { Suspense, useState } from "react";
import { Canvas } from "@react-three/fiber";
import { StarField } from "./StarField";
import { CelestialGrid } from "./CelestialGrid";
import { CameraController, CameraTelemetry } from "./CameraController";
import { SearchMarker } from "./SearchMarker";
import { AstronomicalImageLayer } from "./AstronomicalImageLayer";
import { TargetMarkers } from "./TargetMarkers";
import { CutoutTextureOverlay } from "./CutoutTextureOverlay";
import { ActiveImageLayerState } from "@/types/astronomicalImage";

export interface CelestialSphereProps {
  showGrid?: boolean;
  showStars?: boolean;
  showLabels?: boolean;
  onTelemetryUpdate?: (telemetry: CameraTelemetry) => void;
  resetTrigger?: number;
  zoomInTrigger?: number;
  zoomOutTrigger?: number;
  targetCoords?: { ra: number; dec: number } | null;
  targetCoordsTrigger?: number;
  targetLabel?: string;
  fov?: number;
  imageLayers?: ActiveImageLayerState[];
}

/**
 * Foundational 3D Celestial Visualization Environment (Milestones 1, 2, & 3).
 * Renders an interactive WebGL celestial coordinate sphere with procedural stars,
 * RA/Dec grid, equatorial reference line, celestial poles, coordinate search marker,
 * and WCS-projected astronomical image layers.
 */
export function CelestialSphere({
  showGrid = true,
  showStars = true,
  showLabels = true,
  onTelemetryUpdate,
  resetTrigger = 0,
  zoomInTrigger = 0,
  zoomOutTrigger = 0,
  targetCoords = null,
  targetCoordsTrigger = 0,
  targetLabel = "SEARCH TARGET",
  fov = 60,
  imageLayers = [],
}: CelestialSphereProps) {
  const [webglError, setWebglError] = useState<string | null>(null);

  if (webglError) {
    return (
      <div className="w-full h-full bg-[#02040a] flex items-center justify-center p-6 text-center font-mono">
        <div className="max-w-md p-5 bg-rose-950/40 border border-rose-800/60 rounded-xl text-rose-200 space-y-2">
          <div className="text-sm font-semibold uppercase tracking-wider">
            WebGL Initialization Error
          </div>
          <p className="text-xs text-rose-300/90 leading-relaxed">
            {webglError}
          </p>
          <div className="text-[11px] text-slate-400">
            Please ensure WebGL hardware acceleration is enabled in your browser settings.
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="relative w-full h-full bg-[#02040a] overflow-hidden select-none">
      <Canvas
        camera={{ position: [0, 15, 45], fov: 60, near: 0.1, far: 1000 }}
        gl={{
          antialias: true,
          alpha: false,
          powerPreference: "high-performance",
          failIfMajorPerformanceCaveat: false,
        }}
        onCreated={({ gl }) => {
          gl.setClearColor("#02040a", 1.0);
        }}
        onError={(err: any) => {
          setWebglError(err?.message || "Failed to initialize WebGL context.");
        }}
        className="w-full h-full"
      >
        <color attach="background" args={["#02040a"]} />

        <ambientLight intensity={0.4} />

        <Suspense fallback={null}>
          {/* Milestone 3: WCS-Projected Astronomical Image Layers */}
          {imageLayers.map((layer) => (
            <AstronomicalImageLayer key={layer.layer_id} layer={layer} />
          ))}

          {/* Procedural Demonstration Star Field */}
          <StarField radius={100} count={4500} visible={showStars} />

          {/* NASA 5-Target Scientific Benchmark Markers */}
          <TargetMarkers radius={97.0} />

          {/* Dynamic Cutout Texture Overlay */}
          <CutoutTextureOverlay radius={97.2} />

          {/* Spherical Celestial Coordinate Grid */}
          <CelestialGrid
            radius={98}
            showGrid={showGrid}
            showEquator={showGrid}
            showPoles={showGrid}
            showLabels={showGrid && showLabels}
          />

          {/* Milestone 2: Coordinate Search Target Reticle */}
          {targetCoords && (
            <SearchMarker
              raDeg={targetCoords.ra}
              decDeg={targetCoords.dec}
              radius={97.0}
              visible={true}
              label={targetLabel}
            />
          )}

          {/* Camera Controller & Telemetry */}
          <CameraController
            onTelemetryUpdate={onTelemetryUpdate}
            resetTrigger={resetTrigger}
            zoomInTrigger={zoomInTrigger}
            zoomOutTrigger={zoomOutTrigger}
            targetCoords={targetCoords}
            targetCoordsTrigger={targetCoordsTrigger}
            fov={fov}
          />
        </Suspense>
      </Canvas>
    </div>
  );
}

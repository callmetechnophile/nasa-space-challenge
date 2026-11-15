"use client";

import React, { Suspense } from "react";
import { Canvas } from "@react-three/fiber";
import { OrbitControls } from "@react-three/drei";
import { useSkyStore } from "@/stores/useSkyStore";
import { CelestialGrid } from "./CelestialGrid";
import { StarField } from "./StarField";
import { Constellations } from "./Constellations";
import { GalacticPlane } from "./GalacticPlane";
import { TargetMarkers } from "./TargetMarkers";
import { CutoutTextureOverlay } from "./CutoutTextureOverlay";
import { CameraController } from "./CameraController";

export function CelestialSphereCanvas() {
  const showGrid = useSkyStore((s) => s.showGrid);
  const showConstellations = useSkyStore((s) => s.showConstellations);
  const showGalacticPlane = useSkyStore((s) => s.showGalacticPlane);
  const showEcliptic = useSkyStore((s) => s.showEcliptic);

  return (
    <div className="relative w-full h-full bg-[#030712] overflow-hidden select-none">
      <Canvas
        camera={{ position: [0, 0, 45], fov: 60, near: 0.1, far: 1000 }}
        gl={{ antialias: true, alpha: false, powerPreference: "high-performance" }}
        className="w-full h-full"
      >
        <color attach="background" args={["#030712"]} />

        <ambientLight intensity={0.4} />

        <Suspense fallback={null}>
          {/* Background Starfield */}
          <StarField radius={100} count={5000} />

          {/* Coordinate Grid & Equator */}
          <CelestialGrid radius={98} showGrid={showGrid} showEquator={true} />

          {/* Constellation Outlines */}
          <Constellations radius={97.5} visible={showConstellations} />

          {/* Milky Way Galactic & Ecliptic Planes */}
          <GalacticPlane
            radius={97.2}
            showGalactic={showGalacticPlane}
            showEcliptic={showEcliptic}
          />

          {/* Interactive Target Markers & Search Reticle */}
          <TargetMarkers radius={96.5} />

          {/* High-Resolution Cutout Texture on Celestial Sphere */}
          <CutoutTextureOverlay radius={96.0} />

          {/* Smooth Camera Fly-To Controller */}
          <CameraController />
        </Suspense>

        {/* Orbit Controls for free user exploration */}
        <OrbitControls
          enableDamping
          dampingFactor={0.05}
          rotateSpeed={0.7}
          zoomSpeed={1.0}
          panSpeed={0.8}
          minDistance={5}
          maxDistance={85}
        />
      </Canvas>
    </div>
  );
}

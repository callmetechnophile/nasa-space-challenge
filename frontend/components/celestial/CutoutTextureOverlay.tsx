"use client";

import React, { useMemo, useEffect, useState } from "react";
import * as THREE from "three";
import { useSkyStore } from "@/stores/useSkyStore";
import { radecToThreeJs } from "@/utils/coordinates";
import { getCutoutUrl } from "@/services/api";

interface CutoutTextureOverlayProps {
  radius?: number;
}

export function CutoutTextureOverlay({ radius = 96.0 }: CutoutTextureOverlayProps) {
  const showCutoutOverlay = useSkyStore((s) => s.showCutoutOverlay);
  const selectedTarget = useSkyStore((s) => s.selectedTarget);
  const raDeg = useSkyStore((s) => s.raDeg);
  const decDeg = useSkyStore((s) => s.decDeg);
  const selectedEpoch = useSkyStore((s) => s.selectedEpoch);
  const selectedChannel = useSkyStore((s) => s.selectedChannel);
  const imageStretch = useSkyStore((s) => s.imageStretch);
  const imageColormap = useSkyStore((s) => s.imageColormap);

  const [texture, setTexture] = useState<THREE.Texture | null>(null);

  const cutoutUrl = useMemo(() => {
    return getCutoutUrl({
      target: selectedTarget?.id,
      ra: selectedTarget ? undefined : raDeg,
      dec: selectedTarget ? undefined : decDeg,
      epoch: selectedEpoch?.epoch_id || "EPOCH-PASS1-20250615",
      channel: selectedChannel,
      stretch: imageStretch,
      colormap: imageColormap,
      fov_arcmin: 6.0,
    });
  }, [selectedTarget, raDeg, decDeg, selectedEpoch, selectedChannel, imageStretch, imageColormap]);

  useEffect(() => {
    if (!showCutoutOverlay) return;
    const loader = new THREE.TextureLoader();
    loader.load(
      cutoutUrl,
      (loadedTex) => {
        loadedTex.colorSpace = THREE.SRGBColorSpace;
        setTexture(loadedTex);
      },
      undefined,
      (err) => {
        console.warn("Cutout texture load error:", err);
      }
    );
  }, [cutoutUrl, showCutoutOverlay]);

  const [x, y, z] = useMemo(
    () => radecToThreeJs(raDeg, decDeg, radius),
    [raDeg, decDeg, radius]
  );

  const lookAtOrigin = useMemo(() => {
    const pos = new THREE.Vector3(x, y, z);
    return new THREE.Quaternion().setFromUnitVectors(
      new THREE.Vector3(0, 0, 1),
      pos.clone().normalize()
    );
  }, [x, y, z]);

  const borderPoints = useMemo(() => {
    return new Float32Array([
      -2.1, -2.1, 0.01,  2.1, -2.1, 0.01,
       2.1, -2.1, 0.01,  2.1,  2.1, 0.01,
       2.1,  2.1, 0.01, -2.1,  2.1, 0.01,
      -2.1,  2.1, 0.01, -2.1, -2.1, 0.01,
    ]);
  }, []);

  if (!showCutoutOverlay || !texture) return null;

  return (
    <group position={[x, y, z]} quaternion={lookAtOrigin} name="cutout-overlay">
      <mesh>
        <planeGeometry args={[4.2, 4.2]} />
        <meshBasicMaterial
          map={texture}
          transparent
          opacity={0.92}
          side={THREE.DoubleSide}
        />
      </mesh>
      {/* Subtle Cyan Border around cutout footprint */}
      <lineSegments>
        <bufferGeometry attach="geometry">
          <bufferAttribute
            attach="attributes-position"
            args={[borderPoints, 3]}
          />
        </bufferGeometry>
        <lineBasicMaterial color="#38bdf8" transparent opacity={0.7} />
      </lineSegments>
    </group>
  );
}

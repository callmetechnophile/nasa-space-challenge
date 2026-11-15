"use client";

import React, { useRef, useMemo } from "react";
import * as THREE from "three";
import { useFrame } from "@react-three/fiber";
import { Billboard, Text } from "@react-three/drei";
import { radecToVector3Array, formatRaHms, formatDecDms } from "@/utils/coordinates";

export interface SearchMarkerProps {
  raDeg: number;
  decDeg: number;
  radius?: number;
  visible?: boolean;
  label?: string;
}

/**
 * Coordinate Search Target Marker for Milestone 2.
 * Placed at the exact celestial coordinates on the sphere.
 * Displays crosshair reticle, pulsing halo, and coordinate HUD badge.
 * Strictly labeled as SEARCH TARGET (not an astronomical detection).
 */
export function SearchMarker({
  raDeg,
  decDeg,
  radius = 97.0,
  visible = true,
  label = "SEARCH TARGET",
}: SearchMarkerProps) {
  const ringRef = useRef<THREE.Mesh>(null);

  // Pulse animation
  useFrame(({ clock }) => {
    if (ringRef.current) {
      const t = clock.getElapsedTime();
      const s = 1.0 + 0.2 * Math.sin(t * 4.0);
      ringRef.current.scale.set(s, s, s);
    }
  });

  const [x, y, z] = useMemo(
    () => radecToVector3Array(raDeg, decDeg, radius),
    [raDeg, decDeg, radius]
  );

  // Quaternion to orient reticle flat against the celestial sphere surface
  const surfaceOrientation = useMemo(() => {
    const pos = new THREE.Vector3(x, y, z);
    return new THREE.Quaternion().setFromUnitVectors(
      new THREE.Vector3(0, 0, 1),
      pos.clone().normalize()
    );
  }, [x, y, z]);

  const crosshairLines = useMemo(() => {
    return new Float32Array([
      -1.6, 0, 0.02,  1.6, 0, 0.02,
      0, -1.6, 0.02,  0, 1.6, 0.02,
    ]);
  }, []);

  if (!visible) return null;

  return (
    <group name="search-target-marker" position={[x, y, z]}>
      {/* Reticle aligned tangent to sphere surface */}
      <group quaternion={surfaceOrientation}>
        {/* Pulsing Target Ring */}
        <mesh ref={ringRef}>
          <ringGeometry args={[0.9, 1.15, 32]} />
          <meshBasicMaterial
            color="#22d3ee"
            side={THREE.DoubleSide}
            transparent
            opacity={0.85}
            depthWrite={false}
          />
        </mesh>

        {/* Outer Fine Target Circle */}
        <mesh>
          <ringGeometry args={[1.7, 1.8, 32]} />
          <meshBasicMaterial
            color="#06b6d4"
            side={THREE.DoubleSide}
            transparent
            opacity={0.4}
            depthWrite={false}
          />
        </mesh>

        {/* Reticle Crosshairs */}
        <lineSegments>
          <bufferGeometry attach="geometry">
            <bufferAttribute
              attach="attributes-position"
              args={[crosshairLines, 3]}
            />
          </bufferGeometry>
          <lineBasicMaterial
            color="#22d3ee"
            transparent
            opacity={0.8}
            depthWrite={false}
          />
        </lineSegments>
      </group>

      {/* Billboard Coordinate Information Badge (Always faces camera) */}
      <Billboard position={[0, 2.8, 0]}>
        {/* Label Tag */}
        <Text
          position={[0, 0.9, 0]}
          fontSize={0.85}
          color="#38bdf8"
          anchorX="center"
          anchorY="middle"
        >
          {label}
        </Text>

        {/* RA / Dec readout */}
        <Text
          position={[0, 0, 0]}
          fontSize={0.7}
          color="#e2e8f0"
          anchorX="center"
          anchorY="middle"
        >
          {`RA: ${raDeg.toFixed(4)}° (${formatRaHms(raDeg)})`}
        </Text>
        <Text
          position={[0, -0.7, 0]}
          fontSize={0.7}
          color="#e2e8f0"
          anchorX="center"
          anchorY="middle"
        >
          {`Dec: ${decDeg.toFixed(4)}° (${formatDecDms(decDeg)})`}
        </Text>
      </Billboard>
    </group>
  );
}

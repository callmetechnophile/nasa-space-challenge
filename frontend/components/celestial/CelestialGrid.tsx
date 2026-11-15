"use client";

import React, { useMemo } from "react";
import * as THREE from "three";
import { Billboard, Text } from "@react-three/drei";
import { radecToVector3Array } from "@/utils/coordinates";

export interface CelestialGridProps {
  radius?: number;
  showGrid?: boolean;
  showEquator?: boolean;
  showPoles?: boolean;
  showLabels?: boolean;
}

/**
 * Spherical Celestial Coordinate Grid for Milestone 1.
 * Optimized with unified LineSegments for minimal GPU draw calls (1-2 draw calls).
 * 
 * Features:
 * - 24 Right Ascension meridians (every 15° = 1 hour)
 * - 10 Declination parallels (every 15° from -75° to +75°)
 * - Highlighted Celestial Equator (Dec = 0°)
 * - Celestial Poles (NCP at +Y, SCP at -Y)
 * - Billboard SDF text labels
 */
export function CelestialGrid({
  radius = 98,
  showGrid = true,
  showEquator = true,
  showPoles = true,
  showLabels = true,
}: CelestialGridProps) {
  // Combine all RA meridians and Dec parallels into a single LineSegments Float32Array
  const gridLineSegments = useMemo(() => {
    if (!showGrid) return new Float32Array();
    const segments: number[] = [];

    // 1. RA Meridians: 24 hour circles (every 15 deg = 1 hour from 0h to 23h)
    const decStep = 3; // 3-degree resolution for smooth curvature
    for (let raHour = 0; raHour < 24; raHour += 1) {
      const raDeg = raHour * 15;
      for (let dec = -87; dec < 87; dec += decStep) {
        const [x1, y1, z1] = radecToVector3Array(raDeg, dec, radius);
        const [x2, y2, z2] = radecToVector3Array(raDeg, dec + decStep, radius);
        segments.push(x1, y1, z1, x2, y2, z2);
      }
    }

    // 2. Dec Parallels: every 15 degrees (-75, -60, -45, -30, -15, +15, +30, +45, +60, +75)
    const parallels = [-75, -60, -45, -30, -15, 15, 30, 45, 60, 75];
    const raStep = 3; // 3-degree resolution around the circle
    for (const dec of parallels) {
      for (let ra = 0; ra < 360; ra += raStep) {
        const [x1, y1, z1] = radecToVector3Array(ra, dec, radius);
        const [x2, y2, z2] = radecToVector3Array(ra + raStep, dec, radius);
        segments.push(x1, y1, z1, x2, y2, z2);
      }
    }

    return new Float32Array(segments);
  }, [radius, showGrid]);

  // Highlighted Celestial Equator (Dec = 0) LineSegments
  const equatorSegments = useMemo(() => {
    if (!showEquator) return new Float32Array();
    const segments: number[] = [];
    const step = 2; // 2-degree smooth segments
    for (let ra = 0; ra < 360; ra += step) {
      const [x1, y1, z1] = radecToVector3Array(ra, 0, radius);
      const [x2, y2, z2] = radecToVector3Array(ra + step, 0, radius);
      segments.push(x1, y1, z1, x2, y2, z2);
    }
    return new Float32Array(segments);
  }, [radius, showEquator]);

  // Celestial Pole Coordinates
  const ncpPos = useMemo(() => [0, radius, 0] as [number, number, number], [radius]);
  const scpPos = useMemo(() => [0, -radius, 0] as [number, number, number], [radius]);

  // RA Hour Labels along Equator (every 2 hours: 0h, 2h, ... 22h)
  const raLabels = useMemo(() => {
    if (!showLabels) return [];
    const list: { text: string; pos: [number, number, number] }[] = [];
    for (let h = 0; h < 24; h += 2) {
      const raDeg = h * 15;
      const [x, y, z] = radecToVector3Array(raDeg, 1.8, radius * 0.985);
      list.push({ text: `${h}h`, pos: [x, y, z] });
    }
    return list;
  }, [radius, showLabels]);

  // Dec Degree Labels along Prime Meridian (RA = 0h)
  const decLabels = useMemo(() => {
    if (!showLabels) return [];
    const list: { text: string; pos: [number, number, number] }[] = [];
    const decs = [-60, -45, -30, -15, 15, 30, 45, 60];
    for (const d of decs) {
      const [x, y, z] = radecToVector3Array(1.5, d, radius * 0.985);
      list.push({ text: `${d > 0 ? "+" : ""}${d}°`, pos: [x, y, z] });
    }
    return list;
  }, [radius, showLabels]);

  if (!showGrid && !showEquator && !showPoles) return null;

  return (
    <group name="celestial-coordinate-grid">
      {/* Unified RA Meridians & Dec Parallels (Single Draw Call) */}
      {showGrid && gridLineSegments.length > 0 && (
        <lineSegments>
          <bufferGeometry attach="geometry">
            <bufferAttribute
              attach="attributes-position"
              args={[gridLineSegments, 3]}
            />
          </bufferGeometry>
          <lineBasicMaterial
            attach="material"
            color="#1e3a8a"
            transparent
            opacity={0.35}
            linewidth={1}
            depthWrite={false}
          />
        </lineSegments>
      )}

      {/* Prominent Subtle Cyan Celestial Equator (Single Draw Call) */}
      {showEquator && equatorSegments.length > 0 && (
        <lineSegments>
          <bufferGeometry attach="geometry">
            <bufferAttribute
              attach="attributes-position"
              args={[equatorSegments, 3]}
            />
          </bufferGeometry>
          <lineBasicMaterial
            attach="material"
            color="#38bdf8"
            transparent
            opacity={0.7}
            linewidth={2}
            depthWrite={false}
          />
        </lineSegments>
      )}

      {/* North & South Celestial Poles */}
      {showPoles && (
        <group name="celestial-poles">
          {/* North Celestial Pole (+Y) */}
          <group position={ncpPos}>
            <mesh>
              <sphereGeometry args={[0.55, 12, 12]} />
              <meshBasicMaterial color="#38bdf8" />
            </mesh>
            {showLabels && (
              <Billboard position={[0, 2.5, 0]}>
                <Text
                  fontSize={1.4}
                  color="#38bdf8"
                  anchorX="center"
                  anchorY="middle"
                >
                  NCP (+90°)
                </Text>
              </Billboard>
            )}
          </group>

          {/* South Celestial Pole (-Y) */}
          <group position={scpPos}>
            <mesh>
              <sphereGeometry args={[0.55, 12, 12]} />
              <meshBasicMaterial color="#38bdf8" />
            </mesh>
            {showLabels && (
              <Billboard position={[0, -2.5, 0]}>
                <Text
                  fontSize={1.4}
                  color="#38bdf8"
                  anchorX="center"
                  anchorY="middle"
                >
                  SCP (-90°)
                </Text>
              </Billboard>
            )}
          </group>
        </group>
      )}

      {/* RA Hour Circle Labels */}
      {showLabels &&
        raLabels.map((lbl, idx) => (
          <Billboard key={`ralbl-${idx}`} position={lbl.pos}>
            <Text
              fontSize={1.2}
              color="#93c5fd"
              fillOpacity={0.75}
              anchorX="center"
              anchorY="middle"
            >
              {lbl.text}
            </Text>
          </Billboard>
        ))}

      {/* Dec Degree Parallel Labels */}
      {showLabels &&
        decLabels.map((lbl, idx) => (
          <Billboard key={`declbl-${idx}`} position={lbl.pos}>
            <Text
              fontSize={1.1}
              color="#93c5fd"
              fillOpacity={0.75}
              anchorX="center"
              anchorY="middle"
            >
              {lbl.text}
            </Text>
          </Billboard>
        ))}
    </group>
  );
}

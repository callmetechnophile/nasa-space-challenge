"use client";

import React, { useMemo } from "react";
import * as THREE from "three";
import { radecToThreeJs } from "@/utils/coordinates";

interface GalacticPlaneProps {
  radius?: number;
  showGalactic?: boolean;
  showEcliptic?: boolean;
}

export function GalacticPlane({
  radius = 97.2,
  showGalactic = true,
  showEcliptic = true,
}: GalacticPlaneProps) {
  // Galactic Plane Great Circle
  const galacticPoints = useMemo(() => {
    if (!showGalactic) return new Float32Array();
    const pts: number[] = [];
    const inc = (62.87 * Math.PI) / 180;
    const node = (282.86 * Math.PI) / 180;

    for (let l = 0; l <= 360; l += 2) {
      const lRad = (l * Math.PI) / 180;
      const sinDec = Math.sin(inc) * Math.sin(lRad - (33.0 * Math.PI) / 180);
      const decRad = Math.asin(sinDec);
      const decDeg = (decRad * 180) / Math.PI;

      const yVal = Math.cos(inc) * Math.sin(lRad - (33.0 * Math.PI) / 180);
      const xVal = Math.cos(lRad - (33.0 * Math.PI) / 180);
      let raRad = Math.atan2(yVal, xVal) + node;
      if (raRad < 0) raRad += 2 * Math.PI;
      const raDeg = ((raRad * 180) / Math.PI) % 360;

      const [x, y, z] = radecToThreeJs(raDeg, decDeg, radius);
      pts.push(x, y, z);
    }
    return new Float32Array(pts);
  }, [radius, showGalactic]);

  // Ecliptic Plane (Earth's orbital plane / Zodiac, obliquity eps = 23.439 deg)
  const eclipticPoints = useMemo(() => {
    if (!showEcliptic) return new Float32Array();
    const pts: number[] = [];
    const eps = (23.43929 * Math.PI) / 180;

    for (let lon = 0; lon <= 360; lon += 2) {
      const lonRad = (lon * Math.PI) / 180;
      const decRad = Math.asin(Math.sin(eps) * Math.sin(lonRad));
      const decDeg = (decRad * 180) / Math.PI;

      const yVal = Math.cos(eps) * Math.sin(lonRad);
      const xVal = Math.cos(lonRad);
      let raRad = Math.atan2(yVal, xVal);
      if (raRad < 0) raRad += 2 * Math.PI;
      const raDeg = (raRad * 180) / Math.PI;

      const [x, y, z] = radecToThreeJs(raDeg, decDeg, radius);
      pts.push(x, y, z);
    }
    return new Float32Array(pts);
  }, [radius, showEcliptic]);

  // Galactic Center (Sgr A*: RA 17h 45m 40s = 266.417 deg, Dec -29.008 deg)
  const [gcX, gcY, gcZ] = useMemo(
    () => radecToThreeJs(266.417, -29.008, radius),
    [radius]
  );

  return (
    <group name="galactic-and-ecliptic-planes">
      {/* Galactic Plane (Violet/Magenta) */}
      {showGalactic && galacticPoints.length > 0 && (
        <group>
          <line>
            <bufferGeometry attach="geometry">
              <bufferAttribute
                attach="attributes-position"
                args={[galacticPoints, 3]}
              />
            </bufferGeometry>
            <lineBasicMaterial
              attach="material"
              color="#a855f7"
              transparent
              opacity={0.65}
              linewidth={2}
            />
          </line>

          {/* Sgr A* Galactic Center indicator */}
          <mesh position={[gcX, gcY, gcZ]}>
            <sphereGeometry args={[0.5, 12, 12]} />
            <meshBasicMaterial color="#ec4899" />
          </mesh>
        </group>
      )}

      {/* Ecliptic Plane (Amber/Gold) */}
      {showEcliptic && eclipticPoints.length > 0 && (
        <line>
          <bufferGeometry attach="geometry">
            <bufferAttribute
              attach="attributes-position"
              args={[eclipticPoints, 3]}
            />
          </bufferGeometry>
          <lineBasicMaterial
            attach="material"
            color="#f59e0b"
            transparent
            opacity={0.45}
            linewidth={1}
          />
        </line>
      )}
    </group>
  );
}

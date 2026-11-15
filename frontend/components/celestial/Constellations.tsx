"use client";

import React, { useMemo } from "react";
import * as THREE from "three";
import { radecToThreeJs } from "@/utils/coordinates";

interface ConstellationFigure {
  name: string;
  segments: [number, number, number, number][]; // [ra1, dec1, ra2, dec2]
}

const CONSTELLATIONS: ConstellationFigure[] = [
  {
    name: "Orion",
    segments: [
      // Belt
      [84.05, -1.2, 85.19, -1.94], // Mintaka to Alnilam
      [85.19, -1.94, 86.13, -1.94], // Alnilam to Alnitak
      // Body
      [88.79, 7.41, 81.28, 6.35], // Betelgeuse to Bellatrix
      [81.28, 6.35, 84.05, -1.2], // Bellatrix to Mintaka
      [88.79, 7.41, 86.13, -1.94], // Betelgeuse to Alnitak
      [84.05, -1.2, 78.63, -8.2], // Mintaka to Rigel
      [86.13, -1.94, 86.94, -9.67], // Alnitak to Saiph
      [78.63, -8.2, 86.94, -9.67], // Rigel to Saiph
    ],
  },
  {
    name: "Ursa Major (Big Dipper)",
    segments: [
      [165.93, 61.75, 165.46, 56.38], // Dubhe to Merak
      [165.46, 56.38, 178.46, 53.69], // Merak to Phecda
      [178.46, 53.69, 183.86, 57.03], // Phecda to Megrez
      [183.86, 57.03, 165.93, 61.75], // Megrez to Dubhe
      [183.86, 57.03, 193.51, 55.96], // Megrez to Alioth
      [193.51, 55.96, 200.98, 54.92], // Alioth to Mizar
      [200.98, 54.92, 206.89, 49.31], // Mizar to Alkaid
    ],
  },
  {
    name: "Cassiopeia",
    segments: [
      [2.29, 59.15, 9.83, 56.54], // Caph to Schedar
      [9.83, 56.54, 14.18, 60.72], // Schedar to Gamma Cas
      [14.18, 60.72, 21.45, 60.23], // Gamma Cas to Ruchbah
      [21.45, 60.23, 26.15, 63.67], // Ruchbah to Segin
    ],
  },
  {
    name: "Cygnus (Northern Cross)",
    segments: [
      [310.36, 45.28, 305.56, 40.26], // Deneb to Sadr
      [305.56, 40.26, 292.68, 27.96], // Sadr to Albireo
      [305.56, 40.26, 311.37, 33.97], // Sadr to Gienah
      [305.56, 40.26, 296.24, 45.13], // Sadr to Delta Cyg
    ],
  },
  {
    name: "Scorpius",
    segments: [
      [241.36, -19.8, 247.35, -26.43], // Dschubba to Antares
      [247.35, -26.43, 252.17, -34.29], // Antares to Wei
      [252.17, -34.29, 263.4, -42.99], // Wei to Sargas
      [263.4, -42.99, 263.74, -39.03], // Sargas to Shaula
    ],
  },
  {
    name: "Crux (Southern Cross)",
    segments: [
      [186.65, -63.1, 187.97, -57.11], // Acrux to Gacrux
      [191.93, -59.69, 183.95, -58.75], // Mimosa to Imai
    ],
  },
];

interface ConstellationsProps {
  radius?: number;
  visible?: boolean;
}

export function Constellations({ radius = 97.5, visible = true }: ConstellationsProps) {
  const lineArray = useMemo(() => {
    if (!visible) return new Float32Array();
    const pts: number[] = [];

    for (const c of CONSTELLATIONS) {
      for (const [ra1, dec1, ra2, dec2] of c.segments) {
        const [x1, y1, z1] = radecToThreeJs(ra1, dec1, radius);
        const [x2, y2, z2] = radecToThreeJs(ra2, dec2, radius);
        pts.push(x1, y1, z1, x2, y2, z2);
      }
    }
    return new Float32Array(pts);
  }, [radius, visible]);

  if (!visible || lineArray.length === 0) return null;

  return (
    <group name="constellations">
      <lineSegments>
        <bufferGeometry attach="geometry">
          <bufferAttribute
            attach="attributes-position"
            args={[lineArray, 3]}
          />
        </bufferGeometry>
        <lineBasicMaterial
          attach="material"
          color="#6366f1"
          transparent
          opacity={0.4}
          linewidth={1}
        />
      </lineSegments>
    </group>
  );
}

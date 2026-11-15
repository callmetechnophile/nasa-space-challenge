"use client";

import React, { useMemo } from "react";
import * as THREE from "three";

export interface StarFieldProps {
  radius?: number;
  count?: number;
  visible?: boolean;
}

/**
 * Procedural Star Field for SPHEREx Celestial Explorer (Milestone 1).
 * 
 * DATA PROVENANCE:
 * SYNTHETIC DEMONSTRATION DATA.
 * Generates 4,500 procedural stars distributed across the unit celestial sphere
 * with realistic apparent brightness (power-law distribution) and spectral color tinting
 * (subtle white, ice-blue, pale gold), rendered via a single instanced GPU Points buffer.
 */
export function StarField({
  radius = 100,
  count = 4500,
  visible = true,
}: StarFieldProps) {
  const { positions, colors } = useMemo(() => {
    const pos = new Float32Array(count * 3);
    const col = new Float32Array(count * 3);

    // Astronomical color variations for stars (O/B blue-white, A pure white, F/G pale warm white)
    const starPalette = [
      new THREE.Color("#dbeafe"), // Subtle soft blue
      new THREE.Color("#eff6ff"), // Crisp ice-white
      new THREE.Color("#ffffff"), // Pure stellar white
      new THREE.Color("#f8fafc"), // Slate white
      new THREE.Color("#fef3c7"), // Subtle warm cream
    ];

    // Deterministic linear congruential generator for reproducible star distribution
    let seed = 42891;
    const lcg = () => {
      seed = (seed * 1664525 + 1013904223) % 4294967296;
      return seed / 4294967296;
    };

    for (let i = 0; i < count; i++) {
      // Uniform spherical surface distribution using Archimedes' projection
      const u = lcg(); // RA azimuth fraction [0, 1)
      const v = lcg(); // Dec polar fraction [0, 1)

      const theta = u * 2.0 * Math.PI; // Right Ascension in radians
      const phi = Math.acos(2.0 * v - 1.0); // Polar angle from North Pole

      // Convert to Three.js Cartesian coordinates on sphere
      const x = radius * Math.sin(phi) * Math.sin(theta);
      const y = radius * Math.cos(phi);
      const z = -radius * Math.sin(phi) * Math.cos(theta);

      pos[i * 3] = x;
      pos[i * 3 + 1] = y;
      pos[i * 3 + 2] = z;

      // Color selection with brightness modulation
      const colorIndex = Math.floor(lcg() * starPalette.length);
      const baseColor = starPalette[colorIndex];

      // Realistic stellar apparent brightness (power-law distribution: more faint stars, few bright ones)
      const brightnessFactor = 0.55 + 0.45 * Math.pow(lcg(), 3.0);

      col[i * 3] = baseColor.r * brightnessFactor;
      col[i * 3 + 1] = baseColor.g * brightnessFactor;
      col[i * 3 + 2] = baseColor.b * brightnessFactor;
    }

    return { positions: pos, colors: col };
  }, [count, radius]);

  if (!visible) return null;

  return (
    <group name="demonstration-starfield">
      <points>
        <bufferGeometry attach="geometry">
          <bufferAttribute
            attach="attributes-position"
            args={[positions, 3]}
          />
          <bufferAttribute
            attach="attributes-color"
            args={[colors, 3]}
          />
        </bufferGeometry>
        <pointsMaterial
          attach="material"
          size={1.4}
          vertexColors
          transparent
          opacity={0.9}
          sizeAttenuation={false}
          blending={THREE.AdditiveBlending}
        />
      </points>
    </group>
  );
}

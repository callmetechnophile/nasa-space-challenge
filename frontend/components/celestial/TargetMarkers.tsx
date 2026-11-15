"use client";

import React, { useRef, useMemo } from "react";
import * as THREE from "three";
import { useFrame } from "@react-three/fiber";
import { useSkyStore } from "@/stores/useSkyStore";
import { radecToThreeJs } from "@/utils/coordinates";

interface TargetMarkersProps {
  radius?: number;
}

export function TargetMarkers({ radius = 96.5 }: TargetMarkersProps) {
  const validationTargets = useSkyStore((s) => s.validationTargets);
  const selectedTarget = useSkyStore((s) => s.selectedTarget);
  const selectTarget = useSkyStore((s) => s.selectTarget);
  const raDeg = useSkyStore((s) => s.raDeg);
  const decDeg = useSkyStore((s) => s.decDeg);

  // Animation ref for pulsing reticle
  const reticleRingRef = useRef<THREE.Mesh>(null);

  useFrame(({ clock }) => {
    if (reticleRingRef.current) {
      const t = clock.getElapsedTime();
      const s = 1.0 + 0.25 * Math.sin(t * 3.5);
      reticleRingRef.current.scale.set(s, s, s);
    }
  });

  // Position of active search coordinates
  const [retX, retY, retZ] = useMemo(
    () => radecToThreeJs(raDeg, decDeg, radius),
    [raDeg, decDeg, radius]
  );

  const lookAtOrigin = useMemo(() => {
    const pos = new THREE.Vector3(retX, retY, retZ);
    return new THREE.Quaternion().setFromUnitVectors(
      new THREE.Vector3(0, 0, 1),
      pos.clone().normalize()
    );
  }, [retX, retY, retZ]);

  const crosshairArray = useMemo(() => {
    return new Float32Array([
      -1.8, 0, 0, 1.8, 0, 0,
      0, -1.8, 0, 0, 1.8, 0,
    ]);
  }, []);

  return (
    <group name="target-markers">
      {/* 5 NASA Validation Targets */}
      {validationTargets.map((target) => {
        const [x, y, z] = radecToThreeJs(target.ra_deg, target.dec_deg, radius);
        const isSelected = selectedTarget?.id === target.id;

        return (
          <group
            key={target.id}
            position={[x, y, z]}
            onClick={(e) => {
              e.stopPropagation();
              selectTarget(target);
            }}
          >
            {/* Target Core Sphere */}
            <mesh>
              <sphereGeometry args={[isSelected ? 0.7 : 0.45, 16, 16]} />
              <meshBasicMaterial
                color={isSelected ? "#00f0ff" : "#38bdf8"}
                transparent
                opacity={0.9}
              />
            </mesh>

            {/* Target Outer Halo */}
            <mesh>
              <ringGeometry args={[0.7, 0.9, 24]} />
              <meshBasicMaterial
                color={isSelected ? "#00f0ff" : "#60a5fa"}
                side={THREE.DoubleSide}
                transparent
                opacity={0.6}
              />
            </mesh>
          </group>
        );
      })}

      {/* Active Search Reticle Ring */}
      <group position={[retX, retY, retZ]} quaternion={lookAtOrigin}>
        <mesh ref={reticleRingRef}>
          <ringGeometry args={[1.1, 1.35, 32]} />
          <meshBasicMaterial
            color="#22d3ee"
            side={THREE.DoubleSide}
            transparent
            opacity={0.85}
          />
        </mesh>
        {/* Reticle Crosshairs */}
        <lineSegments>
          <bufferGeometry attach="geometry">
            <bufferAttribute
              attach="attributes-position"
              args={[crosshairArray, 3]}
            />
          </bufferGeometry>
          <lineBasicMaterial color="#22d3ee" transparent opacity={0.6} />
        </lineSegments>
      </group>
    </group>
  );
}

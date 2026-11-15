"use client";

import React, { useRef, useEffect } from "react";
import * as THREE from "three";
import { useThree, useFrame } from "@react-three/fiber";
import { OrbitControls as OrbitControlsImpl } from "three-stdlib";
import { OrbitControls } from "@react-three/drei";
import { radecToVector3Array } from "@/utils/coordinates";

export interface CameraTelemetry {
  distance: number;
  polarDeg: number;
  azimuthDeg: number;
  fov: number;
}

export interface CameraControllerProps {
  onTelemetryUpdate?: (telemetry: CameraTelemetry) => void;
  resetTrigger?: number;
  zoomInTrigger?: number;
  zoomOutTrigger?: number;
  targetCoords?: { ra: number; dec: number } | null;
  targetCoordsTrigger?: number;
  fov?: number;
}

/**
 * Camera Controller for SPHEREx Celestial Explorer (Milestone 1 & 2).
 * Features:
 * - Left drag: spherical rotation (orbit)
 * - Scroll wheel: smooth zoom (dolly)
 * - Right drag: tangential pan
 * - Double-click on canvas: animated reset
 * - Touch support: 1-finger rotate, 2-finger pinch/pan
 * - Gimbal stabilization: clamps polar angle away from singularities to prevent roll
 * - Programmatic smooth great-circle flight to target astronomical coordinates (M2)
 * - Optical Field-of-View (FOV) control with projection matrix updates (M2)
 */
export function CameraController({
  onTelemetryUpdate,
  resetTrigger = 0,
  zoomInTrigger = 0,
  zoomOutTrigger = 0,
  targetCoords = null,
  targetCoordsTrigger = 0,
  fov = 60,
}: CameraControllerProps) {
  const { camera, gl } = useThree();
  const controlsRef = useRef<OrbitControlsImpl>(null);

  // Smooth animation ref
  const targetPosition = useRef<THREE.Vector3 | null>(null);
  const isAnimating = useRef(false);

  // Default initial perspective (looking from [0, 15, 45] toward [0, 0, 0])
  const defaultPosition = useRef(new THREE.Vector3(0, 15, 45));

  // Optical FOV handling (M2)
  useEffect(() => {
    if (camera instanceof THREE.PerspectiveCamera) {
      if (Math.abs(camera.fov - fov) > 0.001) {
        camera.fov = fov;
        camera.updateProjectionMatrix();
      }
    }
  }, [fov, camera]);

  // Reset Camera View smoothly
  useEffect(() => {
    if (resetTrigger > 0) {
      targetPosition.current = defaultPosition.current.clone();
      isAnimating.current = true;
      if (controlsRef.current) {
        controlsRef.current.target.set(0, 0, 0);
      }
    }
  }, [resetTrigger]);

  // Coordinate-driven Camera Flight (M2)
  useEffect(() => {
    if (targetCoordsTrigger > 0 && targetCoords) {
      const [vx, vy, vz] = radecToVector3Array(targetCoords.ra, targetCoords.dec, 1.0);
      const dir = new THREE.Vector3(vx, vy, vz);

      // Clamp near poles to prevent OrbitControls gimbal singularity
      if (Math.abs(dir.y) > 0.9995) {
        dir.y = Math.sign(dir.y) * 0.9995;
        if (Math.abs(dir.z) < 0.01 && Math.abs(dir.x) < 0.01) {
          dir.z = 0.0316;
        }
        dir.normalize();
      }

      // Current camera distance from target (0,0,0)
      const currentDist = camera.position.length();
      const targetDist = Math.min(Math.max(currentDist, 15), 45);

      // Camera positioned at -dir * targetDist looks directly through (0,0,0) toward +dir on celestial sphere
      const endCamPos = dir.clone().multiplyScalar(-targetDist);

      targetPosition.current = endCamPos;
      isAnimating.current = true;

      if (controlsRef.current) {
        controlsRef.current.target.set(0, 0, 0);
      }
    }
  }, [targetCoordsTrigger, targetCoords, camera.position]);

  // Zoom In step
  useEffect(() => {
    if (zoomInTrigger > 0 && controlsRef.current) {
      const dir = camera.position.clone().sub(controlsRef.current.target);
      const newLen = Math.max(8, dir.length() * 0.75);
      dir.setLength(newLen);
      targetPosition.current = controlsRef.current.target.clone().add(dir);
      isAnimating.current = true;
    }
  }, [zoomInTrigger, camera.position]);

  // Zoom Out step
  useEffect(() => {
    if (zoomOutTrigger > 0 && controlsRef.current) {
      const dir = camera.position.clone().sub(controlsRef.current.target);
      const newLen = Math.min(80, dir.length() * 1.35);
      dir.setLength(newLen);
      targetPosition.current = controlsRef.current.target.clone().add(dir);
      isAnimating.current = true;
    }
  }, [zoomOutTrigger, camera.position]);

  // Double-click canvas handler to reset view (only when clicking directly on canvas)
  useEffect(() => {
    const domElement = gl.domElement;
    const handleDoubleClick = (e: MouseEvent) => {
      if (e.target !== domElement) return;
      targetPosition.current = defaultPosition.current.clone();
      isAnimating.current = true;
      if (controlsRef.current) {
        controlsRef.current.target.set(0, 0, 0);
      }
    };

    domElement.addEventListener("dblclick", handleDoubleClick);
    return () => {
      domElement.removeEventListener("dblclick", handleDoubleClick);
    };
  }, [gl.domElement]);

  // Frame update loop with telemetry reporting and spherical great-circle flight
  useFrame(() => {
    if (isAnimating.current && targetPosition.current) {
      const targetDist = targetPosition.current.length();
      // Smooth interpolation
      camera.position.lerp(targetPosition.current, 0.09);
      // Maintain radial distance so camera glides on sphere instead of penetrating origin
      camera.position.setLength(targetDist);

      if (controlsRef.current) {
        controlsRef.current.update();
      }

      if (camera.position.distanceTo(targetPosition.current) < 0.15) {
        camera.position.copy(targetPosition.current);
        isAnimating.current = false;
        targetPosition.current = null;
      }
    }

    if (onTelemetryUpdate && controlsRef.current) {
      const distance = camera.position.length();
      const polar = (controlsRef.current.getPolarAngle() * 180) / Math.PI;
      const azimuth = (controlsRef.current.getAzimuthalAngle() * 180) / Math.PI;
      const persCamera = camera as THREE.PerspectiveCamera;

      if (typeof window !== "undefined") {
        (window as any).__SPHEREX_CAMERA__ = {
          position: [camera.position.x, camera.position.y, camera.position.z],
          target: [controlsRef.current.target.x, controlsRef.current.target.y, controlsRef.current.target.z],
          fov: persCamera.fov || 60,
        };
      }

      onTelemetryUpdate({
        distance: Math.round(distance * 10) / 10,
        polarDeg: Math.round(polar * 10) / 10,
        azimuthDeg: Math.round(azimuth * 10) / 10,
        fov: Math.round((persCamera.fov || 60) * 10) / 10,
      });
    }
  });

  return (
    <OrbitControls
      ref={controlsRef}
      enableDamping={true}
      dampingFactor={0.06}
      rotateSpeed={0.7}
      zoomSpeed={1.0}
      panSpeed={0.8}
      minDistance={6}
      maxDistance={82}
      minPolarAngle={0.01}
      maxPolarAngle={Math.PI - 0.01}
      enableRotate={true}
      enableZoom={true}
      enablePan={true}
      mouseButtons={{
        LEFT: THREE.MOUSE.ROTATE,
        MIDDLE: THREE.MOUSE.DOLLY,
        RIGHT: THREE.MOUSE.PAN,
      }}
      touches={{
        ONE: THREE.TOUCH.ROTATE,
        TWO: THREE.TOUCH.DOLLY_PAN,
      }}
    />
  );
}

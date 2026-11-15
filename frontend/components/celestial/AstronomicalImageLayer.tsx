"use client";

import React, { useMemo, useEffect } from "react";
import * as THREE from "three";
import { ActiveImageLayerState } from "@/types/astronomicalImage";
import { useSphericalImageGeometry } from "./ImageProjection";
import { useAstronomicalTexture } from "./ImageTextureManager";
import { radecToVector3Array } from "@/utils/coordinates";

export interface AstronomicalImageLayerProps {
  layer: ActiveImageLayerState;
  showFootprintBorder?: boolean;
}

/**
 * Astronomical Image Layer for SPHEREx 3D Sky Explorer (Milestone 3).
 * Renders an astronomical FITS product directly onto the celestial sphere
 * using scientifically correct WCS-derived curvilinear spherical geometry.
 *
 * Implements strict GPU resource management: all geometries, materials,
 * textures, and WebGL buffer attributes are explicitly disposed when unmounted.
 */
export function AstronomicalImageLayer({
  layer,
  showFootprintBorder = true,
}: AstronomicalImageLayerProps) {
  const geometry = useSphericalImageGeometry(layer.mesh);
  const { texture } = useAstronomicalTexture(layer.texture_data_uri);

  // Compute 4 corner outline points for the geometric footprint border
  const borderPoints = useMemo(() => {
    if (!layer.mesh.corners_radec || layer.mesh.corners_radec.length < 4) return null;

    const corners = layer.mesh.corners_radec;
    const r = layer.mesh.radius + 0.05; // Slightly above surface to prevent Z-fighting

    const p0 = radecToVector3Array(corners[0][0], corners[0][1], r);
    const p1 = radecToVector3Array(corners[1][0], corners[1][1], r);
    const p2 = radecToVector3Array(corners[2][0], corners[2][1], r);
    const p3 = radecToVector3Array(corners[3][0], corners[3][1], r);

    // Closed loop: 0 -> 1 -> 2 -> 3 -> 0
    return new Float32Array([
      p0[0], p0[1], p0[2],  p1[0], p1[1], p1[2],
      p1[0], p1[1], p1[2],  p2[0], p2[1], p2[2],
      p2[0], p2[1], p2[2],  p3[0], p3[1], p3[2],
      p3[0], p3[1], p3[2],  p0[0], p0[1], p0[2],
    ]);
  }, [layer.mesh.corners_radec, layer.mesh.radius]);

  // Explicitly manage footprint border BufferGeometry with deterministic disposal
  const borderGeometry = useMemo(() => {
    if (!borderPoints) return null;
    const geom = new THREE.BufferGeometry();
    geom.setAttribute("position", new THREE.BufferAttribute(borderPoints, 3));
    return geom;
  }, [borderPoints]);

  useEffect(() => {
    return () => {
      if (borderGeometry) {
        borderGeometry.dispose();
      }
    };
  }, [borderGeometry]);

  // Explicitly manage MeshBasicMaterial with deterministic disposal
  const meshMaterial = useMemo(() => {
    return new THREE.MeshBasicMaterial({
      map: texture,
      transparent: true,
      opacity: layer.opacity,
      side: THREE.DoubleSide,
      depthWrite: false,
      toneMapped: false,
    });
  }, [texture, layer.opacity]);

  useEffect(() => {
    return () => {
      meshMaterial.dispose();
    };
  }, [meshMaterial]);

  // Explicitly manage LineBasicMaterial with deterministic disposal
  const borderMaterial = useMemo(() => {
    return new THREE.LineBasicMaterial({
      color: "#06b6d4",
      transparent: true,
      opacity: Math.min(0.7, layer.opacity + 0.2),
      linewidth: 1,
      depthWrite: false,
    });
  }, [layer.opacity]);

  useEffect(() => {
    return () => {
      borderMaterial.dispose();
    };
  }, [borderMaterial]);

  if (!layer.visible) return null;

  return (
    <group name={`astronomical-layer-${layer.layer_id}`}>
      {/* 1. Main WCS-Projected Textured Spherical Mesh */}
      <mesh geometry={geometry} material={meshMaterial} />

      {/* 2. Geometric WCS Footprint Perimeter Border */}
      {showFootprintBorder && borderGeometry && (
        <lineSegments geometry={borderGeometry} material={borderMaterial} />
      )}
    </group>
  );
}

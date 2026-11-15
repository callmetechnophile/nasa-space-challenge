"use client";

import { useMemo, useEffect } from "react";
import * as THREE from "three";
import { SphericalMeshGeometry } from "@/types/astronomicalImage";

export interface ImageProjectionGeometryProps {
  mesh: SphericalMeshGeometry;
}

/**
 * Hook to construct a Three.js BufferGeometry from WCS-derived spherical coordinates.
 * Properly attaches vertices, UV coordinates, and triangle index buffers.
 * Automatically disposes underlying GPU buffers on unmount or geometry changes.
 */
export function useSphericalImageGeometry(mesh: SphericalMeshGeometry): THREE.BufferGeometry {
  const geometry = useMemo(() => {
    const geom = new THREE.BufferGeometry();

    const positionArray = new Float32Array(mesh.vertices);
    const uvArray = new Float32Array(mesh.uvs);
    const indexArray = mesh.vertex_count > 65535
      ? new Uint32Array(mesh.indices)
      : new Uint16Array(mesh.indices);

    geom.setAttribute("position", new THREE.BufferAttribute(positionArray, 3));
    geom.setAttribute("uv", new THREE.BufferAttribute(uvArray, 2));
    geom.setIndex(new THREE.BufferAttribute(indexArray, 1));

    geom.computeVertexNormals();

    return geom;
  }, [mesh.vertices, mesh.uvs, mesh.indices, mesh.vertex_count]);

  // Clean disposal
  useEffect(() => {
    return () => {
      geometry.dispose();
    };
  }, [geometry]);

  return geometry;
}

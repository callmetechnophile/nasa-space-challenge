"use client";

import React, { useEffect, useRef, useState } from "react";
import * as THREE from "three";

export type IconVariant =
  | "telescope"
  | "planet"
  | "spectral"
  | "detector"
  | "orbit"
  | "evidence"
  | "coordinate"
  | "workspace";

interface ThreeDIconProps {
  variant: IconVariant;
  size?: number; // size in px, defaults to 64
  className?: string;
  interactive?: boolean;
}

export function ThreeDIcon({
  variant,
  size = 64,
  className = "",
  interactive = true,
}: ThreeDIconProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [hasWebGL, setHasWebGL] = useState<boolean>(true);
  const [isHovered, setIsHovered] = useState<boolean>(false);

  useEffect(() => {
    // 1. WebGL Support Test
    const canvas = document.createElement("canvas");
    const gl =
      canvas.getContext("webgl2") ||
      canvas.getContext("webgl") ||
      canvas.getContext("experimental-webgl");
    if (!gl) {
      setHasWebGL(false);
      return;
    }

    const container = containerRef.current;
    if (!container) return;

    // 2. Setup Three.js Scene
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(38, 1, 0.1, 100);
    camera.position.set(0, 0, 3.8);

    const renderer = new THREE.WebGLRenderer({
      alpha: true,
      antialias: true,
      powerPreference: "low-power",
    });
    renderer.setSize(size, size);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.1;

    container.appendChild(renderer.domElement);

    // 3. Lighting System (Scientific silver, cyan, and deep space blue)
    const ambientLight = new THREE.AmbientLight(0xdbeafe, 1.2);
    scene.add(ambientLight);

    const keyLight = new THREE.DirectionalLight(0x38bdf8, 2.5);
    keyLight.position.set(2, 3, 2);
    scene.add(keyLight);

    const rimLight = new THREE.DirectionalLight(0x818cf8, 1.8);
    rimLight.position.set(-2, -1, -2);
    scene.add(rimLight);

    // 4. Mesh Construction by Variant
    const group = new THREE.Group();
    scene.add(group);

    // Standard materials
    const metallicCyan = new THREE.MeshStandardMaterial({
      color: 0x0284c7,
      metalness: 0.85,
      roughness: 0.25,
    });

    const silverMat = new THREE.MeshStandardMaterial({
      color: 0xe2e8f0,
      metalness: 0.9,
      roughness: 0.15,
    });

    const glassMat = new THREE.MeshPhysicalMaterial({
      color: 0x38bdf8,
      transparent: true,
      opacity: 0.65,
      roughness: 0.1,
      metalness: 0.1,
      transmission: 0.8,
      thickness: 0.5,
    });

    const wireMat = new THREE.LineBasicMaterial({
      color: 0x38bdf8,
      transparent: true,
      opacity: 0.45,
    });

    if (variant === "telescope") {
      // Barrel
      const barrelGeo = new THREE.CylinderGeometry(0.5, 0.4, 1.2, 24);
      const barrel = new THREE.Mesh(barrelGeo, metallicCyan);
      barrel.rotation.z = Math.PI / 4;
      group.add(barrel);

      // Aperture ring / Sunshield
      const shieldGeo = new THREE.ConeGeometry(0.75, 0.6, 24, 1, true);
      const shield = new THREE.Mesh(shieldGeo, silverMat);
      shield.rotation.z = -Math.PI / 4;
      shield.position.set(0.45, 0.45, 0);
      group.add(shield);

      // Primary mirror disk
      const mirrorGeo = new THREE.CircleGeometry(0.42, 24);
      const mirror = new THREE.Mesh(mirrorGeo, silverMat);
      mirror.position.set(-0.35, -0.35, 0.05);
      mirror.rotation.y = Math.PI / 4;
      group.add(mirror);
    } else if (variant === "planet") {
      // Main planetary sphere
      const sphereGeo = new THREE.SphereGeometry(0.8, 32, 32);
      const planetMesh = new THREE.Mesh(sphereGeo, metallicCyan);
      group.add(planetMesh);

      // Subtle atmospheric cloud ring
      const ringGeo = new THREE.TorusGeometry(1.2, 0.03, 16, 64);
      const ringMesh = new THREE.Mesh(ringGeo, silverMat);
      ringMesh.rotation.x = Math.PI / 2.5;
      ringMesh.rotation.y = Math.PI / 8;
      group.add(ringMesh);
    } else if (variant === "spectral") {
      // Triangular dispersion prism
      const shape = new THREE.Shape();
      shape.moveTo(0, 0.85);
      shape.lineTo(-0.75, -0.65);
      shape.lineTo(0.75, -0.65);
      shape.closePath();

      const extrudeSettings = { depth: 0.5, bevelEnabled: true, bevelThickness: 0.05, bevelSize: 0.05 };
      const prismGeo = new THREE.ExtrudeGeometry(shape, extrudeSettings);
      prismGeo.center();
      const prism = new THREE.Mesh(prismGeo, glassMat);
      group.add(prism);

      // Spectral beam lines
      const colors = [0x38bdf8, 0x2dd4bf, 0xfacc15, 0xf43f5e];
      colors.forEach((col, idx) => {
        const lineGeo = new THREE.BufferGeometry().setFromPoints([
          new THREE.Vector3(0.3, 0.1 - idx * 0.1, 0),
          new THREE.Vector3(1.2, 0.3 - idx * 0.25, 0.2),
        ]);
        const lineMat = new THREE.LineBasicMaterial({ color: col, linewidth: 2 });
        const line = new THREE.Line(lineGeo, lineMat);
        group.add(line);
      });
    } else if (variant === "detector") {
      // Focal plane plate with 6 sensor tiles (D1–D6)
      const baseGeo = new THREE.BoxGeometry(1.6, 1.2, 0.08);
      const base = new THREE.Mesh(baseGeo, metallicCyan);
      group.add(base);

      const tileGeo = new THREE.BoxGeometry(0.42, 0.42, 0.06);
      const positions = [
        [-0.48, 0.26, 0.05],
        [0.0, 0.26, 0.05],
        [0.48, 0.26, 0.05],
        [-0.48, -0.26, 0.05],
        [0.0, -0.26, 0.05],
        [0.48, -0.26, 0.05],
      ];
      positions.forEach((pos) => {
        const tile = new THREE.Mesh(tileGeo, silverMat);
        tile.position.set(pos[0], pos[1], pos[2]);
        group.add(tile);
      });
      group.rotation.x = 0.35;
      group.rotation.y = -0.3;
    } else if (variant === "orbit") {
      // Central sun
      const sunGeo = new THREE.SphereGeometry(0.28, 24, 24);
      const sun = new THREE.Mesh(sunGeo, silverMat);
      group.add(sun);

      // Known coplanar orbit
      const innerRingGeo = new THREE.TorusGeometry(0.75, 0.015, 12, 64);
      const innerRing = new THREE.Mesh(innerRingGeo, wireMat);
      innerRing.rotation.x = Math.PI / 2.2;
      group.add(innerRing);

      // Inclined elliptical orbit (Planet Nine hypothesis)
      const outerRingGeo = new THREE.TorusGeometry(1.3, 0.02, 12, 64);
      const outerMat = new THREE.MeshStandardMaterial({ color: 0x38bdf8, roughness: 0.3 });
      const outerRing = new THREE.Mesh(outerRingGeo, outerMat);
      outerRing.rotation.x = Math.PI / 1.5;
      outerRing.rotation.y = Math.PI / 6;
      group.add(outerRing);
    } else if (variant === "evidence") {
      // Magnifying lens ring
      const torusGeo = new THREE.TorusGeometry(0.7, 0.08, 16, 48);
      const rim = new THREE.Mesh(torusGeo, metallicCyan);
      group.add(rim);

      // Glass lens
      const lensGeo = new THREE.CylinderGeometry(0.65, 0.65, 0.05, 32);
      const lens = new THREE.Mesh(lensGeo, glassMat);
      lens.rotation.x = Math.PI / 2;
      group.add(lens);

      // Handle
      const handleGeo = new THREE.CylinderGeometry(0.06, 0.06, 0.8, 16);
      const handle = new THREE.Mesh(handleGeo, silverMat);
      handle.position.set(0.6, -0.7, 0);
      handle.rotation.z = -Math.PI / 4;
      group.add(handle);
    } else if (variant === "coordinate") {
      // Celestial sphere wireframe
      const sphereGeo = new THREE.SphereGeometry(0.9, 14, 10);
      const wireframe = new THREE.WireframeGeometry(sphereGeo);
      const line = new THREE.LineSegments(wireframe, wireMat);
      group.add(line);

      // Equatorial ring
      const eqGeo = new THREE.TorusGeometry(0.91, 0.02, 12, 48);
      const eq = new THREE.Mesh(eqGeo, silverMat);
      eq.rotation.x = Math.PI / 2;
      group.add(eq);

      // Polar axis
      const axisGeo = new THREE.CylinderGeometry(0.02, 0.02, 2.1, 12);
      const axis = new THREE.Mesh(axisGeo, metallicCyan);
      group.add(axis);
    } else if (variant === "workspace") {
      // Console base & floating data plane
      const deskGeo = new THREE.BoxGeometry(1.4, 0.1, 0.9);
      const desk = new THREE.Mesh(deskGeo, metallicCyan);
      desk.rotation.x = 0.3;
      group.add(desk);

      const screenGeo = new THREE.BoxGeometry(1.2, 0.75, 0.04);
      const screen = new THREE.Mesh(screenGeo, glassMat);
      screen.position.set(0, 0.35, -0.2);
      screen.rotation.x = 0.1;
      group.add(screen);
    }

    // 5. Animation Loop with prefers-reduced-motion check
    const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    let animId: number;
    let time = 0;

    const animate = () => {
      animId = requestAnimationFrame(animate);
      time += 0.01;

      if (!prefersReducedMotion) {
        // Slow idle drift
        group.rotation.y += 0.006;
        if (isHovered && interactive) {
          group.rotation.y += 0.02;
          group.rotation.x = Math.sin(time * 2) * 0.1;
        }
      }

      renderer.render(scene, camera);
    };

    animate();

    return () => {
      cancelAnimationFrame(animId);
      renderer.dispose();
      if (container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement);
      }
    };
  }, [variant, size, isHovered, interactive]);

  if (!hasWebGL) {
    // Graceful SVG Fallback
    return (
      <div
        className={`inline-flex items-center justify-center rounded-xl bg-cyan-950/40 border border-cyan-500/20 text-cyan-400 p-2 ${className}`}
        style={{ width: size, height: size }}
      >
        <span className="text-xs font-mono font-bold uppercase">{variant.slice(0, 3)}</span>
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      className={`inline-block select-none overflow-hidden ${className}`}
      style={{ width: size, height: size }}
      aria-hidden="true"
    />
  );
}

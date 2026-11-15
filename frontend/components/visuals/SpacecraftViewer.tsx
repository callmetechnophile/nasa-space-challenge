"use client";

import React, { useEffect, useRef, useState } from "react";
import * as THREE from "three";
import { Info, RotateCw, ZoomIn, ShieldCheck } from "lucide-react";

interface ComponentInfo {
  id: string;
  name: string;
  role: string;
  specs: string;
  description: string;
}

const COMPONENTS: Record<string, ComponentInfo> = {
  aperture: {
    id: "aperture",
    name: "Telescope Aperture & Baffle",
    role: "Photonic Collection & Stray-Light Rejection",
    specs: "20 cm clear aperture · 3.5° × 11.3° rectangular FOV",
    description:
      "A wide-field 20-centimeter primary telescope aperture designed to collect photons across a massive swath of sky with extreme stray-light attenuation from the Sun and Earth limbs.",
  },
  optics: {
    id: "optics",
    name: "Optical Assembly (TMA)",
    role: "All-Aluminum Three-Mirror Anastigmat",
    specs: "F/3 focal ratio · Achromatic across 0.75–5.0 µm",
    description:
      "A monolithic aluminum Three-Mirror Anastigmat (TMA) design that remains completely aligned and diffraction-limited through passive cryogenic contraction from 300 K down to 80 K.",
  },
  detectors: {
    id: "detectors",
    name: "Six Detector Arrays (D1–D6)",
    role: "Spectroscopic Focal Plane Assembly",
    specs: "6 × 2048×2048 Teledyne Hawaii-2RG (H2RG) HgCdTe",
    description:
      "Six independent Hawaii-2RG detector arrays, each fitted with a linear variable filter (LVF). Together, they capture 102 contiguous spectral bands without mechanical moving parts.",
  },
  shields: {
    id: "shields",
    name: "Conical V-Groove Photon Shields",
    role: "Multi-Stage Cryogenic Heat Rejection",
    specs: "3 nested aluminum cones · Outer shield rejection >99%",
    description:
      "Nested conical V-groove thermal shields deflect sunlight and solar panel heat out into cold space, enabling the entire optical assembly to cool down to <80 K passively without consumable cryogens.",
  },
  thermal: {
    id: "thermal",
    name: "Passive Thermal Radiator",
    role: "Cryogenic Detector Stage Cooling",
    specs: "Passive radiator stage cooling D5/D6 below 55 K",
    description:
      "Radiates parasitic heat directly toward the cold celestial pole, maintaining the long-wavelength HgCdTe detector arrays at ~55 K to suppress dark current thermal noise.",
  },
  scan: {
    id: "scan",
    name: "Spacecraft Scanning Geometry",
    role: "Low-Earth Polar Sun-Synchronous Orbit",
    specs: "700 km altitude · 98° inclination · 97 min orbital period",
    description:
      "The spacecraft orbits along Earth's day/night terminator, pointing at 90° from the Sun. It scans great circles across the celestial sphere, completing an all-sky map every 6 months.",
  },
};

export function SpacecraftViewer() {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [activeComponentId, setActiveComponentId] = useState<string>("optics");
  const [isRotating, setIsRotating] = useState<boolean>(true);

  const active = COMPONENTS[activeComponentId] || COMPONENTS.optics;

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    // 1. Three.js Scene Setup
    const width = container.clientWidth;
    const height = container.clientHeight;

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(40, width / height, 0.1, 100);
    camera.position.set(3.5, 2.8, 4.2);
    camera.lookAt(0, 0, 0);

    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.15;
    container.appendChild(renderer.domElement);

    // 2. Lighting System
    const ambientLight = new THREE.AmbientLight(0xdbeafe, 1.2);
    scene.add(ambientLight);

    const sunLight = new THREE.DirectionalLight(0xfff7ed, 3.2);
    sunLight.position.set(5, 6, 4);
    scene.add(sunLight);

    const earthGlow = new THREE.DirectionalLight(0x38bdf8, 1.5);
    earthGlow.position.set(-4, -2, -3);
    scene.add(earthGlow);

    // 3. Materials
    const goldFoilMat = new THREE.MeshStandardMaterial({
      color: 0xd97706,
      metalness: 0.9,
      roughness: 0.2,
    });

    const silverShieldMat = new THREE.MeshStandardMaterial({
      color: 0xf1f5f9,
      metalness: 0.92,
      roughness: 0.18,
      side: THREE.DoubleSide,
    });

    const spacecraftBusMat = new THREE.MeshStandardMaterial({
      color: 0x1e293b,
      metalness: 0.8,
      roughness: 0.35,
    });

    const apertureMat = new THREE.MeshStandardMaterial({
      color: 0x0284c7,
      metalness: 0.85,
      roughness: 0.25,
    });

    const highlightMat = new THREE.MeshStandardMaterial({
      color: 0x38bdf8,
      emissive: 0x0284c7,
      emissiveIntensity: 0.6,
      metalness: 0.9,
      roughness: 0.15,
    });

    // 4. Spacecraft Geometry Hierarchy
    const rootGroup = new THREE.Group();
    scene.add(rootGroup);

    // Spacecraft Bus (Hexagonal Service Module)
    const busGeo = new THREE.CylinderGeometry(1.0, 1.0, 0.8, 6);
    const busMesh = new THREE.Mesh(busGeo, spacecraftBusMat);
    busMesh.position.y = -0.9;
    rootGroup.add(busMesh);

    // Solar Panel Arrays (On sunny side)
    const panelGeo = new THREE.BoxGeometry(0.08, 1.2, 1.8);
    const panelMesh = new THREE.Mesh(panelGeo, goldFoilMat);
    panelMesh.position.set(-1.1, -0.8, 0);
    panelMesh.rotation.z = 0.15;
    rootGroup.add(panelMesh);

    // Nested Conical Thermal Photon Shields (3 stages)
    const shield1Geo = new THREE.ConeGeometry(1.6, 1.4, 32, 1, true);
    const shield1 = new THREE.Mesh(shield1Geo, silverShieldMat);
    shield1.position.y = 0.2;
    rootGroup.add(shield1);

    const shield2Geo = new THREE.ConeGeometry(1.3, 1.3, 32, 1, true);
    const shield2 = new THREE.Mesh(shield2Geo, silverShieldMat);
    shield2.position.y = 0.35;
    rootGroup.add(shield2);

    const shield3Geo = new THREE.ConeGeometry(1.0, 1.2, 32, 1, true);
    const shield3 = new THREE.Mesh(shield3Geo, silverShieldMat);
    shield3.position.y = 0.5;
    rootGroup.add(shield3);

    // Telescope Optical Baffle & Barrel (TMA)
    const barrelGeo = new THREE.CylinderGeometry(0.45, 0.45, 1.1, 24);
    const barrelMesh = new THREE.Mesh(
      barrelGeo,
      activeComponentId === "optics" || activeComponentId === "aperture" ? highlightMat : apertureMat
    );
    barrelMesh.position.y = 0.7;
    rootGroup.add(barrelMesh);

    // Aperture Cover / Ring
    const ringGeo = new THREE.TorusGeometry(0.48, 0.04, 16, 32);
    const ringMesh = new THREE.Mesh(
      ringGeo,
      activeComponentId === "aperture" ? highlightMat : silverShieldMat
    );
    ringMesh.rotation.x = Math.PI / 2;
    ringMesh.position.y = 1.25;
    rootGroup.add(ringMesh);

    // Focal Plane Array (Base of barrel)
    const fpaGeo = new THREE.BoxGeometry(0.55, 0.1, 0.55);
    const fpaMesh = new THREE.Mesh(
      fpaGeo,
      activeComponentId === "detectors" ? highlightMat : goldFoilMat
    );
    fpaMesh.position.y = 0.15;
    rootGroup.add(fpaMesh);

    // Cold Radiator Bracket
    const radGeo = new THREE.BoxGeometry(0.7, 0.05, 0.7);
    const radMesh = new THREE.Mesh(
      radGeo,
      activeComponentId === "thermal" ? highlightMat : silverShieldMat
    );
    radMesh.position.set(0, -0.4, 0.7);
    radMesh.rotation.x = 0.3;
    rootGroup.add(radMesh);

    // 5. Mouse Drag Interaction
    let isDragging = false;
    let prevMouseX = 0;
    let prevMouseY = 0;

    const onPointerDown = (e: MouseEvent) => {
      isDragging = true;
      prevMouseX = e.clientX;
      prevMouseY = e.clientY;
    };

    const onPointerMove = (e: MouseEvent) => {
      if (!isDragging) return;
      const deltaX = e.clientX - prevMouseX;
      const deltaY = e.clientY - prevMouseY;
      prevMouseX = e.clientX;
      prevMouseY = e.clientY;

      rootGroup.rotation.y += deltaX * 0.008;
      rootGroup.rotation.x += deltaY * 0.008;
    };

    const onPointerUp = () => {
      isDragging = false;
    };

    const domElement = renderer.domElement;
    domElement.addEventListener("mousedown", onPointerDown);
    window.addEventListener("mousemove", onPointerMove);
    window.addEventListener("mouseup", onPointerUp);

    // 6. Resize handling
    const onResize = () => {
      if (!container) return;
      const w = container.clientWidth;
      const h = container.clientHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };
    window.addEventListener("resize", onResize);

    // 7. Animation Loop
    let animId: number;
    const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    const animate = () => {
      animId = requestAnimationFrame(animate);

      if (isRotating && !isDragging && !prefersReducedMotion) {
        rootGroup.rotation.y += 0.004;
      }

      renderer.render(scene, camera);
    };

    animate();

    return () => {
      cancelAnimationFrame(animId);
      domElement.removeEventListener("mousedown", onPointerDown);
      window.removeEventListener("mousemove", onPointerMove);
      window.removeEventListener("mouseup", onPointerUp);
      window.removeEventListener("resize", onResize);
      renderer.dispose();
      if (container.contains(domElement)) {
        container.removeChild(domElement);
      }
    };
  }, [activeComponentId, isRotating]);

  return (
    <div className="w-full border border-slate-800/80 rounded-2xl bg-[#040814]/90 backdrop-blur-sm overflow-hidden shadow-2xl">
      {/* Telemetry bar */}
      <div className="px-6 py-4 border-b border-slate-800/80 flex flex-wrap items-center justify-between gap-4 bg-[#02050f]/90">
        <div className="flex items-center gap-2.5">
          <span className="w-2 h-2 rounded-full bg-cyan-400" />
          <span className="text-xs font-mono uppercase tracking-wider text-slate-200">
            SPHEREx Spacecraft 3D CAD Architecture
          </span>
        </div>
        <div className="flex items-center gap-3 text-xs font-mono">
          <span className="px-2 py-0.5 rounded bg-amber-950/60 border border-amber-500/30 text-amber-300">
            Educational Reconstruction
          </span>
          <button
            onClick={() => setIsRotating(!isRotating)}
            className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-slate-900 border border-slate-700 text-slate-300 hover:text-cyan-300 transition-colors"
          >
            <RotateCw className="w-3.5 h-3.5" />
            <span>{isRotating ? "Pause Orbit" : "Auto-Rotate"}</span>
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 min-h-[520px]">
        {/* 3D Canvas Viewport */}
        <div className="lg:col-span-7 relative flex items-center justify-center p-6 bg-[#02040a] min-h-[380px] cursor-grab active:cursor-grabbing">
          <div ref={containerRef} className="w-full h-full min-h-[360px]" />

          {/* Interactive overlay guide */}
          <div className="absolute bottom-4 left-6 text-xs font-mono text-slate-400 pointer-events-none">
            Drag cursor to rotate spacecraft in 3D space
          </div>
        </div>

        {/* Component Selector & Detailed Scientific Readout */}
        <div className="lg:col-span-5 p-6 lg:p-8 flex flex-col justify-between border-t lg:border-t-0 lg:border-l border-slate-800/80 bg-[#030611]">
          <div className="space-y-5">
            <div>
              <div className="text-xs font-mono uppercase tracking-wider text-cyan-400 mb-1">
                Selected Subsystem
              </div>
              <h3 className="text-2xl font-bold text-slate-100 tracking-tight [text-wrap:balance]">
                {active.name}
              </h3>
              <div className="text-xs font-mono text-slate-300 mt-1">{active.specs}</div>
            </div>

            <p className="text-sm text-slate-300 leading-relaxed [text-wrap:pretty]">
              {active.description}
            </p>

            <div className="pl-3.5 border-l-2 border-cyan-500/50 text-xs text-slate-300 space-y-1">
              <span className="font-semibold text-cyan-300 block">System Mission Function</span>
              <p className="text-slate-300 leading-relaxed [text-wrap:pretty]">{active.role}</p>
            </div>
          </div>

          {/* Component Selection Buttons */}
          <div className="space-y-2 pt-4 border-t border-slate-800/60 mt-6">
            <div className="text-xs font-mono uppercase text-slate-400 tracking-wider mb-2">
              Select Subsystem to Inspect:
            </div>
            <div className="grid grid-cols-2 gap-2">
              {Object.values(COMPONENTS).map((comp) => {
                const isSelected = comp.id === activeComponentId;
                return (
                  <button
                    key={comp.id}
                    onClick={() => setActiveComponentId(comp.id)}
                    className={`px-3 py-2 text-xs font-medium text-left transition-all rounded ${
                      isSelected
                        ? "bg-cyan-950/80 text-cyan-200 border-l-2 border-cyan-400"
                        : "text-slate-300 hover:text-slate-100 hover:bg-slate-800/40"
                    }`}
                  >
                    <div className="font-semibold truncate">{comp.name.split(" ")[0]} {comp.name.split(" ")[1]}</div>
                    <div className="text-xs font-mono text-slate-400 truncate">{comp.id}</div>
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

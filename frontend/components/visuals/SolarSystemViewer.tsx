"use client";

import React, { useEffect, useRef, useState } from "react";
import * as THREE from "three";
import { Eye, EyeOff, RotateCw, ZoomIn, AlertCircle } from "lucide-react";

interface TNOInfo {
  id: string;
  name: string;
  perihelionAU: number;
  aphelionAU: number;
  semiMajorAxisAU: number;
  inclinationDeg: number;
  discoveryYear: number;
  significance: string;
}

const TNOS: Record<string, TNOInfo> = {
  sedna: {
    id: "sedna",
    name: "90377 Sedna",
    perihelionAU: 76.0,
    aphelionAU: 937.0,
    semiMajorAxisAU: 506.0,
    inclinationDeg: 11.9,
    discoveryYear: 2003,
    significance: "First discovered detached Sednoid; perihelion far beyond Neptune gravitational reach (76 AU).",
  },
  vp113: {
    id: "vp113",
    name: "2012 VP113 (Biden)",
    perihelionAU: 80.5,
    aphelionAU: 446.0,
    semiMajorAxisAU: 263.0,
    inclinationDeg: 24.1,
    discoveryYear: 2014,
    significance: "Discovery prompted Trujillo & Sheppard (2014) to notice argument of perihelion clustering.",
  },
  leleaku: {
    id: "leleaku",
    name: "541132 Leleākūhonua",
    perihelionAU: 65.1,
    aphelionAU: 2100.0,
    semiMajorAxisAU: 1080.0,
    inclinationDeg: 11.7,
    discoveryYear: 2015,
    significance: "Extreme semi-major axis over 1,000 AU, reinforcing orbital clustering evidence.",
  },
  planet9: {
    id: "planet9",
    name: "Hypothesized Planet Nine",
    perihelionAU: 200.0,
    aphelionAU: 500.0,
    semiMajorAxisAU: 380.0,
    inclinationDeg: 16.0,
    discoveryYear: 2016,
    significance:
      "Dynamical hypothesis (Batygin & Brown 2016, 2021). Predicted mass ~5–10 Earth masses. UNCONFIRMED.",
  },
};

export function SolarSystemViewer() {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [showHypothesis, setShowHypothesis] = useState<boolean>(true);
  const [selectedTNOId, setSelectedTNOId] = useState<string>("planet9");
  const [isRotating, setIsRotating] = useState<boolean>(true);

  const selected = TNOS[selectedTNOId] || TNOS.planet9;

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const width = container.clientWidth;
    const height = container.clientHeight;

    // 1. Scene & Camera
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 100);
    camera.position.set(0, 5.2, 5.8);
    camera.lookAt(0, 0, 0);

    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    container.appendChild(renderer.domElement);

    // 2. Lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 1.2);
    scene.add(ambientLight);

    const rootGroup = new THREE.Group();
    scene.add(rootGroup);

    // 3. Central Sun
    const sunGeo = new THREE.SphereGeometry(0.18, 32, 32);
    const sunMat = new THREE.MeshBasicMaterial({ color: 0xfffbeb });
    const sun = new THREE.Mesh(sunGeo, sunMat);
    rootGroup.add(sun);

    // 4. Known Planet Orbits (Logarithmic radial scale for visual clarity)
    // Scale: r_visual = log10(r_AU + 1) * 0.85
    const knownPlanets = [
      { name: "Earth", rAU: 1.0, color: 0x38bdf8 },
      { name: "Jupiter", rAU: 5.2, color: 0xfbbf24 },
      { name: "Saturn", rAU: 9.5, color: 0xfde047 },
      { name: "Uranus", rAU: 19.8, color: 0x2dd4bf },
      { name: "Neptune", rAU: 30.1, color: 0x60a5fa },
    ];

    knownPlanets.forEach((p) => {
      const rVis = Math.log10(p.rAU + 1) * 1.1;
      const orbitGeo = new THREE.BufferGeometry();
      const pts: THREE.Vector3[] = [];
      const segments = 64;
      for (let i = 0; i <= segments; i++) {
        const theta = (i / segments) * Math.PI * 2;
        pts.push(new THREE.Vector3(Math.cos(theta) * rVis, 0, Math.sin(theta) * rVis));
      }
      orbitGeo.setFromPoints(pts);
      const orbitLine = new THREE.Line(
        orbitGeo,
        new THREE.LineBasicMaterial({ color: p.color, transparent: true, opacity: p.name === "Neptune" ? 0.7 : 0.25 })
      );
      rootGroup.add(orbitLine);

      // Planet dot
      const dotGeo = new THREE.SphereGeometry(p.name === "Neptune" ? 0.05 : 0.035, 16, 16);
      const dot = new THREE.Mesh(dotGeo, new THREE.MeshBasicMaterial({ color: p.color }));
      dot.position.set(rVis, 0, 0);
      rootGroup.add(dot);
    });

    // 5. Kuiper Belt Torus Ring (30–50 AU)
    const kbInner = Math.log10(30 + 1) * 1.1;
    const kbOuter = Math.log10(55 + 1) * 1.1;
    const kbGeo = new THREE.RingGeometry(kbInner, kbOuter, 48);
    const kbMat = new THREE.MeshBasicMaterial({
      color: 0x64748b,
      side: THREE.DoubleSide,
      transparent: true,
      opacity: 0.15,
    });
    const kbRing = new THREE.Mesh(kbGeo, kbMat);
    kbRing.rotation.x = Math.PI / 2;
    rootGroup.add(kbRing);

    // 6. Extreme TNO Clustered Orbits (Sedna, VP113, Leleākūhonua)
    const tnoConfigs = [
      { id: "sedna", aAU: 506, e: 0.85, inc: 11.9, omega: 311, color: 0x38bdf8 },
      { id: "vp113", aAU: 263, e: 0.69, inc: 24.1, omega: 294, color: 0x2dd4bf },
      { id: "leleaku", aAU: 1080, e: 0.94, inc: 11.7, omega: 118, color: 0xa78bfa },
    ];

    tnoConfigs.forEach((tno) => {
      const isSelected = selectedTNOId === tno.id;
      const pts: THREE.Vector3[] = [];
      const segments = 100;
      // Visual compressed scale for extreme aAU
      const aVis = Math.log10(tno.aAU) * 1.05;
      const bVis = aVis * Math.sqrt(1 - tno.e * tno.e * 0.7); // Visual eccentricity compression
      const cVis = aVis * 0.65;

      for (let i = 0; i <= segments; i++) {
        const theta = (i / segments) * Math.PI * 2;
        const x = Math.cos(theta) * aVis - cVis;
        const z = Math.sin(theta) * bVis;
        pts.push(new THREE.Vector3(x, 0, z));
      }

      const geo = new THREE.BufferGeometry().setFromPoints(pts);
      const mat = new THREE.LineBasicMaterial({
        color: tno.color,
        transparent: true,
        opacity: isSelected ? 0.95 : 0.45,
        linewidth: isSelected ? 2 : 1,
      });
      const line = new THREE.Line(geo, mat);
      line.rotation.y = (tno.omega * Math.PI) / 180;
      line.rotation.x = (tno.inc * Math.PI) / 180;
      rootGroup.add(line);
    });

    // 7. Hypothesized Planet Nine Orbit (Anti-aligned to extreme TNOs, inclined, dotted)
    if (showHypothesis) {
      const p9Pts: THREE.Vector3[] = [];
      const segments = 100;
      const aVis = Math.log10(380) * 1.05;
      const bVis = aVis * Math.sqrt(1 - 0.5 * 0.5);
      const cVis = aVis * 0.5;

      for (let i = 0; i <= segments; i++) {
        const theta = (i / segments) * Math.PI * 2;
        const x = Math.cos(theta) * aVis - cVis;
        const z = Math.sin(theta) * bVis;
        p9Pts.push(new THREE.Vector3(x, 0, z));
      }

      const p9Geo = new THREE.BufferGeometry().setFromPoints(p9Pts);
      const p9Mat = new THREE.LineDashedMaterial({
        color: 0xf43f5e,
        dashSize: 0.1,
        gapSize: 0.06,
        transparent: true,
        opacity: 0.85,
      });
      const p9Line = new THREE.Line(p9Geo, p9Mat);
      p9Line.computeLineDistances();
      p9Line.rotation.y = (130 * Math.PI) / 180; // Anti-aligned
      p9Line.rotation.x = (-16 * Math.PI) / 180; // Inclination
      rootGroup.add(p9Line);
    }

    // 8. Interaction: Pointer Drag
    let isDragging = false;
    let prevX = 0;
    let prevY = 0;

    const onPointerDown = (e: MouseEvent) => {
      isDragging = true;
      prevX = e.clientX;
      prevY = e.clientY;
    };

    const onPointerMove = (e: MouseEvent) => {
      if (!isDragging) return;
      const dx = e.clientX - prevX;
      const dy = e.clientY - prevY;
      prevX = e.clientX;
      prevY = e.clientY;

      rootGroup.rotation.y += dx * 0.007;
      rootGroup.rotation.x += dy * 0.007;
    };

    const onPointerUp = () => {
      isDragging = false;
    };

    const domElement = renderer.domElement;
    domElement.addEventListener("mousedown", onPointerDown);
    window.addEventListener("mousemove", onPointerMove);
    window.addEventListener("mouseup", onPointerUp);

    // 9. Resize Handling
    const onResize = () => {
      if (!container) return;
      const w = container.clientWidth;
      const h = container.clientHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };
    window.addEventListener("resize", onResize);

    // 10. Animation Loop
    let animId: number;
    const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    const animate = () => {
      animId = requestAnimationFrame(animate);
      if (isRotating && !isDragging && !prefersReducedMotion) {
        rootGroup.rotation.y += 0.002;
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
  }, [showHypothesis, selectedTNOId, isRotating]);

  return (
    <div className="w-full border border-slate-800/80 rounded-2xl bg-[#040814]/90 backdrop-blur-sm overflow-hidden shadow-2xl">
      {/* Telemetry bar */}
      <div className="px-6 py-4 border-b border-slate-800/80 flex flex-wrap items-center justify-between gap-4 bg-[#02050f]/90">
        <div className="flex items-center gap-2.5">
          <span className="w-2 h-2 rounded-full bg-cyan-400" />
          <span className="text-xs font-mono uppercase tracking-wider text-slate-200">
            Outer Solar System 3D Orbital Model (Logarithmic Scale)
          </span>
        </div>
        <div className="flex items-center gap-3 text-xs font-mono">
          <button
            onClick={() => setShowHypothesis(!showHypothesis)}
            className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded border transition-colors ${
              showHypothesis
                ? "bg-rose-950/60 border-rose-500/40 text-rose-300"
                : "bg-slate-900 border-slate-700 text-slate-400"
            }`}
          >
            {showHypothesis ? <Eye className="w-3.5 h-3.5" /> : <EyeOff className="w-3.5 h-3.5" />}
            <span>Planet Nine Orbit (Dashed)</span>
          </button>
          <button
            onClick={() => setIsRotating(!isRotating)}
            className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-slate-900 border border-slate-700 text-slate-300 hover:text-cyan-300 transition-colors"
          >
            <RotateCw className="w-3.5 h-3.5" />
            <span>{isRotating ? "Pause" : "Rotate"}</span>
          </button>
        </div>
      </div>

      {/* Mandatory Scientific Disclaimer Banner */}
      <div className="px-6 py-2.5 bg-amber-950/40 border-b border-amber-500/20 text-xs text-amber-200/90 flex items-center gap-2 font-mono">
        <AlertCircle className="w-4 h-4 shrink-0 text-amber-400" />
        <span>Conceptual representation of the Planet Nine hypothesis — not a confirmed orbit or discovery.</span>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 min-h-[500px]">
        {/* 3D Viewport */}
        <div className="lg:col-span-7 relative flex items-center justify-center p-6 bg-[#02040a] min-h-[380px] cursor-grab active:cursor-grabbing">
          <div ref={containerRef} className="w-full h-full min-h-[360px]" />

          {/* Scale note */}
          <div className="absolute bottom-4 left-6 text-xs font-mono text-slate-400 pointer-events-none">
            Scale: Logarithmic AU compression · Drag to rotate orbits
          </div>
        </div>

        {/* Object Inspector Drawer */}
        <div className="lg:col-span-5 p-6 lg:p-8 flex flex-col justify-between border-t lg:border-t-0 lg:border-l border-slate-800/80 bg-[#030611]">
          <div className="space-y-5">
            <div>
              <div className="text-xs font-mono uppercase tracking-wider text-cyan-400 mb-1">
                Inspected Body
              </div>
              <h3 className="text-2xl font-bold text-slate-100 tracking-tight [text-wrap:balance]">
                {selected.name}
              </h3>
              <div className="text-xs font-mono text-slate-300 mt-1">
                Discovered/Proposed: {selected.discoveryYear}
              </div>
            </div>

            <p className="text-sm text-slate-300 leading-relaxed [text-wrap:pretty]">
              {selected.significance}
            </p>

            {/* Orbital Parameters Grid - flattened */}
            <div className="grid grid-cols-2 gap-3 py-3 border-y border-slate-800 text-xs font-mono">
              <div>
                <span className="text-slate-400 block">Perihelion (q):</span>
                <span className="text-slate-100 font-semibold">{selected.perihelionAU} AU</span>
              </div>
              <div>
                <span className="text-slate-400 block">Aphelion (Q):</span>
                <span className="text-slate-100 font-semibold">{selected.aphelionAU} AU</span>
              </div>
              <div>
                <span className="text-slate-400 block">Semi-major axis (a):</span>
                <span className="text-cyan-300 font-semibold">{selected.semiMajorAxisAU} AU</span>
              </div>
              <div>
                <span className="text-slate-400 block">Inclination (i):</span>
                <span className="text-slate-100 font-semibold">{selected.inclinationDeg}°</span>
              </div>
            </div>
          </div>

          {/* Selectable Trans-Neptunian Objects */}
          <div className="space-y-2 pt-4 border-t border-slate-800/60 mt-6">
            <div className="text-xs font-mono uppercase text-slate-400 tracking-wider mb-2">
              Select Orbit to Highlight:
            </div>
            <div className="grid grid-cols-2 gap-2">
              {Object.values(TNOS).map((tno) => {
                const isSelected = tno.id === selectedTNOId;
                return (
                  <button
                    key={tno.id}
                    onClick={() => setSelectedTNOId(tno.id)}
                    className={`px-3 py-2 text-xs font-medium text-left transition-all rounded-lg border ${
                      isSelected
                        ? tno.id === "planet9"
                          ? "bg-rose-950/80 text-rose-200 border-rose-500/40 shadow-sm"
                          : "bg-cyan-950/80 text-cyan-200 border-cyan-500/40 shadow-sm"
                        : "text-slate-300 hover:text-slate-100 hover:bg-slate-800/40 border-transparent"
                    }`}
                  >
                    <div className="font-semibold truncate">{tno.name.split(" ")[0]}</div>
                    <div className="text-xs font-mono text-slate-400 truncate">a ≈ {tno.semiMajorAxisAU} AU</div>
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

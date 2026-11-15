"use client";

import React, { useEffect, useRef } from "react";

export function HeroStarfield() {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d", { alpha: true });
    if (!ctx) return;

    let animationFrameId: number;
    let width = (canvas.width = canvas.parentElement?.clientWidth || window.innerWidth);
    let height = (canvas.height = canvas.parentElement?.clientHeight || window.innerHeight);

    const onResize = () => {
      if (!canvas || !canvas.parentElement) return;
      width = canvas.width = canvas.parentElement.clientWidth;
      height = canvas.height = canvas.parentElement.clientHeight;
    };
    window.addEventListener("resize", onResize);

    // Check reduced motion
    const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    // Generate stars with depth layers
    const starCount = Math.min(160, Math.floor((width * height) / 8000));
    const stars = Array.from({ length: starCount }, () => ({
      x: Math.random() * width,
      y: Math.random() * height,
      size: Math.random() * 1.5 + 0.5,
      alpha: Math.random() * 0.7 + 0.3,
      speed: (Math.random() * 0.15 + 0.05) * (prefersReducedMotion ? 0 : 1),
      layer: Math.floor(Math.random() * 3), // 0: background, 1: mid, 2: foreground
      pulsePhase: Math.random() * Math.PI * 2,
    }));

    let mouseX = width / 2;
    let mouseY = height / 2;
    const onMouseMove = (e: MouseEvent) => {
      const rect = canvas.getBoundingClientRect();
      mouseX = e.clientX - rect.left;
      mouseY = e.clientY - rect.top;
    };
    window.addEventListener("mousemove", onMouseMove);

    let t = 0;
    const render = () => {
      t += 0.01;
      ctx.clearRect(0, 0, width, height);

      // Deep space subtle gradient
      const grad = ctx.createRadialGradient(
        width * 0.65,
        height * 0.4,
        width * 0.05,
        width * 0.65,
        height * 0.4,
        width * 0.55
      );
      grad.addColorStop(0, "rgba(14, 30, 64, 0.45)");
      grad.addColorStop(0.5, "rgba(8, 18, 42, 0.2)");
      grad.addColorStop(1, "rgba(2, 4, 10, 0)");
      ctx.fillStyle = grad;
      ctx.fillRect(0, 0, width, height);

      // Subtle celestial orbital geometry lines
      ctx.save();
      ctx.strokeStyle = "rgba(56, 189, 248, 0.06)";
      ctx.lineWidth = 1;
      ctx.setLineDash([4, 12]);
      ctx.beginPath();
      ctx.ellipse(width * 0.68, height * 0.48, width * 0.35, height * 0.28, Math.PI / 6, 0, Math.PI * 2);
      ctx.stroke();

      ctx.strokeStyle = "rgba(45, 212, 191, 0.04)";
      ctx.beginPath();
      ctx.ellipse(width * 0.68, height * 0.48, width * 0.48, height * 0.38, -Math.PI / 8, 0, Math.PI * 2);
      ctx.stroke();
      ctx.restore();

      // Render stars
      stars.forEach((star) => {
        if (!prefersReducedMotion) {
          star.y -= star.speed;
          if (star.y < 0) {
            star.y = height;
            star.x = Math.random() * width;
          }
        }

        const pulse = 0.8 + 0.2 * Math.sin(t * 1.5 + star.pulsePhase);
        const parallaxX = (mouseX - width / 2) * (star.layer * 0.012);
        const parallaxY = (mouseY - height / 2) * (star.layer * 0.012);

        ctx.fillStyle =
          star.layer === 2
            ? `rgba(186, 230, 253, ${star.alpha * pulse})`
            : star.layer === 1
            ? `rgba(125, 211, 252, ${star.alpha * pulse * 0.7})`
            : `rgba(96, 165, 250, ${star.alpha * pulse * 0.5})`;

        ctx.beginPath();
        ctx.arc(star.x + parallaxX, star.y + parallaxY, star.size, 0, Math.PI * 2);
        ctx.fill();
      });

      animationFrameId = requestAnimationFrame(render);
    };

    render();

    return () => {
      window.removeEventListener("resize", onResize);
      window.removeEventListener("mousemove", onMouseMove);
      cancelAnimationFrame(animationFrameId);
    };
  }, []);

  return (
    <div className="absolute inset-0 pointer-events-none overflow-hidden z-0" aria-hidden="true">
      <canvas ref={canvasRef} className="w-full h-full block" />
      {/* Precision reticle corner coordinate overlays */}
      <div className="absolute top-8 right-8 text-xs font-mono text-cyan-400/60 select-none hidden md:block space-y-0.5 text-right">
        <div>SYS: ICRS / SPHEREx 102-BAND</div>
        <div>FOV: 60.00° · LVF D1–D6</div>
        <div>POINTING: α 132.748° · δ -05.621°</div>
      </div>
    </div>
  );
}

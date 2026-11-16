import React from "react";

interface SkyTraceBrandMarkProps {
  size?: number;
  className?: string;
}

/**
 * SkyTrace Custom Brand Mark
 * Sculptural 3D spline and orbital 'S' celestial geometry.
 * Clean, restrained, scientific depth with subtle cyan highlights.
 */
export function SkyTraceBrandMark({
  size = 24,
  className = "",
}: SkyTraceBrandMarkProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 32 32"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={`shrink-0 ${className}`}
      aria-hidden="true"
    >
      <defs>
        {/* Subtle metallic bezel gradient */}
        <linearGradient id="st-bezel" x1="0" y1="0" x2="32" y2="32" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#1e293b" />
          <stop offset="100%" stopColor="#090d16" />
        </linearGradient>

        {/* Upper S-ribbon: specular cyan highlight to scientific deep blue */}
        <linearGradient id="st-spline-top" x1="6" y1="6" x2="26" y2="20" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#bae6fd" />
          <stop offset="35%" stopColor="#38bdf8" />
          <stop offset="80%" stopColor="#0284c7" />
          <stop offset="100%" stopColor="#1e3a8a" />
        </linearGradient>

        {/* Lower S-ribbon: deep celestial indigo curving back into electric cyan */}
        <linearGradient id="st-spline-bottom" x1="8" y1="16" x2="26" y2="27" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#0369a1" />
          <stop offset="40%" stopColor="#0284c7" />
          <stop offset="85%" stopColor="#38bdf8" />
          <stop offset="100%" stopColor="#7dd3fc" />
        </linearGradient>

        {/* Diagonal orbital ring plane */}
        <linearGradient id="st-orbit" x1="4" y1="16" x2="28" y2="16" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#38bdf8" stopOpacity="0.8" />
          <stop offset="45%" stopColor="#0ea5e9" stopOpacity="0.2" />
          <stop offset="70%" stopColor="#0284c7" stopOpacity="0.6" />
          <stop offset="100%" stopColor="#7dd3fc" stopOpacity="0.9" />
        </linearGradient>

        {/* Occlusion shadow for ribbon overlap */}
        <filter id="st-shadow" x="0" y="0" width="32" height="32" filterUnits="userSpaceOnUse">
          <feDropShadow dx="0.5" dy="1" stdDeviation="1" floodColor="#020617" floodOpacity="0.85" />
        </filter>
      </defs>

      {/* Background Badge with subtle dimensional border */}
      <rect
        x="1"
        y="1"
        width="30"
        height="30"
        rx="7"
        fill="url(#st-bezel)"
        stroke="#1e3a5f"
        strokeWidth="1"
        strokeOpacity="0.55"
      />

      {/* Subtle background orbital ring projection (tilted elliptical plane) */}
      <ellipse
        cx="16"
        cy="16"
        rx="10.5"
        ry="4.2"
        transform="rotate(-28 16 16)"
        stroke="url(#st-orbit)"
        strokeWidth="1.1"
        strokeDasharray="2 1.5"
        opacity="0.65"
      />

      {/* Lower spline loop (passes behind central focal point) */}
      <path
        d="M15.5 16.5 C 18 19.5, 23.5 20, 23.5 23 C 23.5 25.5, 19.5 26.5, 16 26.5 C 11.5 26.5, 7.8 24, 8.5 20.8 C 8.8 19.5, 10.2 18.5, 12 18"
        stroke="url(#st-spline-bottom)"
        strokeWidth="2.4"
        strokeLinecap="round"
      />

      {/* Upper sculptural S-ribbon with drop shadow for 3D overlap depth */}
      <g filter="url(#st-shadow)">
        <path
          d="M23.5 11 C 23 8, 19.8 5.5, 16 5.5 C 11.8 5.5, 8.5 7.5, 8.5 10.5 C 8.5 13.5, 13 14.5, 16.2 16.2 C 17.8 17, 19.2 18, 19.8 19.5"
          stroke="url(#st-spline-top)"
          strokeWidth="2.4"
          strokeLinecap="round"
        />
      </g>

      {/* Central Celestial Trace Node (IR / SPHEREx telemetry focal point) */}
      <circle cx="16" cy="16" r="2.2" fill="#0284c7" />
      <circle cx="16" cy="16" r="1.4" fill="#7dd3fc" />
      <circle cx="15.6" cy="15.6" r="0.6" fill="#ffffff" />
    </svg>
  );
}

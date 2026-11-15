"use client";

import React from "react";
import { ThreeDIcon } from "./ThreeDIcon";

export function TelescopeIcon({ size = 48, className = "" }: { size?: number; className?: string }) {
  return <ThreeDIcon variant="telescope" size={size} className={className} />;
}

export function PlanetIcon({ size = 48, className = "" }: { size?: number; className?: string }) {
  return <ThreeDIcon variant="planet" size={size} className={className} />;
}

export function SpectralIcon({ size = 48, className = "" }: { size?: number; className?: string }) {
  return <ThreeDIcon variant="spectral" size={size} className={className} />;
}

export function DetectorIcon({ size = 48, className = "" }: { size?: number; className?: string }) {
  return <ThreeDIcon variant="detector" size={size} className={className} />;
}

export function OrbitIcon({ size = 48, className = "" }: { size?: number; className?: string }) {
  return <ThreeDIcon variant="orbit" size={size} className={className} />;
}

export function EvidenceIcon({ size = 48, className = "" }: { size?: number; className?: string }) {
  return <ThreeDIcon variant="evidence" size={size} className={className} />;
}

export function CoordinateIcon({ size = 48, className = "" }: { size?: number; className?: string }) {
  return <ThreeDIcon variant="coordinate" size={size} className={className} />;
}

export function WorkspaceIcon({ size = 48, className = "" }: { size?: number; className?: string }) {
  return <ThreeDIcon variant="workspace" size={size} className={className} />;
}

export { ThreeDIcon } from "./ThreeDIcon";

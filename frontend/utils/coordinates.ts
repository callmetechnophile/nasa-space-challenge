/**
 * SPHEREx 3D Sky Explorer — Astronomical Coordinate Engine (Milestones 1 & 2)
 * 
 * Standards & Conventions:
 * - International Celestial Reference System (ICRS)
 * - Right Ascension (RA, alpha): [0, 360) degrees, or [0, 24) hours
 * - Declination (Dec, delta): [-90, +90] degrees
 * 
 * Three.js Cartesian Frame (Radius R):
 * - +Y axis: North Celestial Pole (Dec = +90°)
 * - -Y axis: South Celestial Pole (Dec = -90°)
 * - -Z axis: Vernal Equinox (RA = 0h / 0°, Dec = 0°)
 * - +X axis: RA = 6h / 90° (Dec = 0°)
 * - +Z axis: RA = 12h / 180° (Dec = 0°)
 * - -X axis: RA = 18h / 270° (Dec = 0°)
 * 
 * Equations:
 *   x = R * cos(dec) * sin(ra)
 *   y = R * sin(dec)
 *   z = -R * cos(dec) * cos(ra)
 */

export interface EquatorialCoordinates {
  raDeg: number;
  decDeg: number;
}

export interface CartesianVector3 {
  x: number;
  y: number;
  z: number;
}

export interface PARSEResultRA {
  degrees: number;
  hours: number;
  minutes: number;
  seconds: number;
  formatted: string;
}

export interface PARSEResultDec {
  degrees: number;
  d: number;
  m: number;
  s: number;
  sign: "+" | "-";
  formatted: string;
}

/**
 * Convert sexagesimal Right Ascension (h, m, s) to decimal degrees.
 */
export function raToDegrees(h: number, m: number, s: number): number {
  if (isNaN(h) || isNaN(m) || isNaN(s)) {
    throw new Error("RA components must be valid numbers");
  }
  if (h < 0 || h > 24) {
    throw new Error(`RA hours must be between 0 and 24, received ${h}`);
  }
  if (m < 0 || m >= 60) {
    throw new Error(`RA minutes must be between 0 and 59, received ${m}`);
  }
  if (s < 0 || s >= 60) {
    throw new Error(`RA seconds must be between 0 and 59.999, received ${s}`);
  }
  if (h === 24 && (m > 0 || s > 0)) {
    throw new Error("RA 24h must have 0m 0s (equivalent to 0h 0m 0s)");
  }

  const totalHours = h + m / 60.0 + s / 3600.0;
  const deg = (totalHours * 15.0) % 360.0;
  return Number(deg.toFixed(9));
}

/**
 * Convert sexagesimal Declination (d, m, s, sign) to decimal degrees.
 * Correctly preserves the negative sign for -00° MM' SS".
 */
export function decToDegrees(
  d: number,
  m: number,
  s: number,
  sign: "+" | "-" = "+"
): number {
  if (isNaN(d) || isNaN(m) || isNaN(s)) {
    throw new Error("Dec components must be valid numbers");
  }
  if (d < 0 || d > 90) {
    throw new Error(`Dec degrees magnitude must be between 0 and 90, received ${d}`);
  }
  if (m < 0 || m >= 60) {
    throw new Error(`Dec minutes must be between 0 and 59, received ${m}`);
  }
  if (s < 0 || s >= 60) {
    throw new Error(`Dec seconds must be between 0 and 59.999, received ${s}`);
  }
  if (d === 90 && (m > 0 || s > 0)) {
    throw new Error("Celestial pole (±90°) cannot have non-zero arcminutes or arcseconds");
  }

  const absVal = d + m / 60.0 + s / 3600.0;
  const deg = sign === "-" ? -absVal : absVal;
  return Number(deg.toFixed(9));
}

/**
 * Convert decimal degrees to sexagesimal Right Ascension.
 */
export function degreesToRA(raDeg: number): PARSEResultRA {
  if (isNaN(raDeg)) {
    throw new Error("RA degrees must be a valid number");
  }
  const normalized = ((raDeg % 360.0) + 360.0) % 360.0;
  const totalHours = normalized / 15.0;

  const hours = Math.floor(totalHours);
  const remMinutes = (totalHours - hours) * 60.0;
  const minutes = Math.floor(remMinutes);
  const seconds = Number(((remMinutes - minutes) * 60.0).toFixed(4));

  // Handle rounding edge-case
  let finalH = hours;
  let finalM = minutes;
  let finalS = seconds;
  if (finalS >= 60.0) {
    finalS = 0;
    finalM += 1;
  }
  if (finalM >= 60) {
    finalM = 0;
    finalH = (finalH + 1) % 24;
  }

  const formatted = `${finalH.toString().padStart(2, "0")}h ${finalM
    .toString()
    .padStart(2, "0")}m ${finalS.toFixed(3).padStart(6, "0")}s`;

  return {
    degrees: Number(normalized.toFixed(9)),
    hours: finalH,
    minutes: finalM,
    seconds: finalS,
    formatted,
  };
}

/**
 * Convert decimal degrees to sexagesimal Declination.
 */
export function degreesToDec(decDeg: number): PARSEResultDec {
  if (isNaN(decDeg)) {
    throw new Error("Dec degrees must be a valid number");
  }
  if (decDeg < -90.0 || decDeg > 90.0) {
    throw new Error(`Declination ${decDeg}° outside permitted range [-90°, +90°]`);
  }

  const isNeg = decDeg < 0 || Object.is(decDeg, -0);
  const sign: "+" | "-" = isNeg ? "-" : "+";
  const abs = Math.abs(decDeg);

  let d = Math.floor(abs);
  const remMinutes = (abs - d) * 60.0;
  let m = Math.floor(remMinutes);
  let s = Number(((remMinutes - m) * 60.0).toFixed(2));

  if (s >= 60.0) {
    s = 0;
    m += 1;
  }
  if (m >= 60) {
    m = 0;
    d += 1;
  }

  const formatted = `${sign}${d.toString().padStart(2, "0")}° ${m
    .toString()
    .padStart(2, "0")}' ${s.toFixed(2).padStart(5, "0")}"`;

  return {
    degrees: Number(decDeg.toFixed(9)),
    d,
    m,
    s,
    sign,
    formatted,
  };
}

/**
 * Parse RA input from either decimal degrees or sexagesimal formats.
 * Accepts:
 * - "133.795129"
 * - "08h 55m 10.831s"
 * - "08:55:10.831"
 * - "08 55 10.831"
 */
export function parseRA(
  rawInput: string,
  options: { allowNormalization?: boolean } = { allowNormalization: false }
): PARSEResultRA {
  if (!rawInput || typeof rawInput !== "string") {
    throw new Error("Right Ascension input cannot be empty");
  }

  const clean = rawInput.trim();
  if (!clean) {
    throw new Error("Right Ascension input cannot be blank");
  }

  // Reject negative RA
  if (clean.startsWith("-")) {
    throw new Error("Right Ascension cannot be negative");
  }

  // Check if sexagesimal (contains h, :, or whitespace delimiters)
  const sexaRegex = /^(\d{1,2})[h:\s]+(\d{1,2})[m:\s]+(\d{1,2}(?:\.\d+)?)[s]?$/i;
  const match = clean.match(sexaRegex);

  if (match) {
    const h = parseInt(match[1], 10);
    const m = parseInt(match[2], 10);
    const s = parseFloat(match[3]);

    const deg = raToDegrees(h, m, s);
    return degreesToRA(deg);
  }

  // Check if decimal degrees
  // Strip trailing degree symbol if present
  const numStr = clean.replace(/°/g, "").trim();
  const val = parseFloat(numStr);

  if (isNaN(val) || !/^\d+(\.\d+)?$/.test(numStr)) {
    throw new Error(`Invalid characters in Right Ascension: "${clean}"`);
  }

  if (val < 0.0 || val > 360.0) {
    if (options.allowNormalization) {
      return degreesToRA(val);
    }
    throw new Error(`Right Ascension ${val}° outside permitted range [0°, 360°]`);
  }

  return degreesToRA(val);
}

/**
 * Parse Declination input from either decimal degrees or sexagesimal formats.
 * Correctly preserves the sign for -00° MM' SS".
 * Accepts:
 * - "-7.245147"
 * - "-07° 14' 42.53\""
 * - "-07 14 42.53"
 * - "-07:14:42.53"
 * - "+30° 24' 05.1\""
 */
export function parseDec(rawInput: string): PARSEResultDec {
  if (!rawInput || typeof rawInput !== "string") {
    throw new Error("Declination input cannot be empty");
  }

  const clean = rawInput.trim();
  if (!clean) {
    throw new Error("Declination input cannot be blank");
  }

  const isExplicitNegative = clean.startsWith("-");
  const isExplicitPositive = clean.startsWith("+");
  const sign: "+" | "-" = isExplicitNegative ? "-" : "+";

  // Check if sexagesimal
  // e.g. -07° 14' 42.53", -00° 30' 00", 30 24 05.1
  const sexaRegex = /^[+-]?\s*(\d{1,2})[°d:\s]+(\d{1,2})['m:\s]+(\d{1,2}(?:\.\d+)?)["s]?$/i;
  const match = clean.match(sexaRegex);

  if (match) {
    const d = parseInt(match[1], 10);
    const m = parseInt(match[2], 10);
    const s = parseFloat(match[3]);

    const deg = decToDegrees(d, m, s, sign);
    return degreesToDec(deg);
  }

  // Check if decimal degrees
  const numStr = clean.replace(/[°+]/g, "").trim();
  const val = parseFloat(numStr);

  if (isNaN(val) || !/^-?\d+(\.\d+)?$/.test(numStr)) {
    throw new Error(`Invalid characters in Declination: "${clean}"`);
  }

  if (val < -90.0 || val > 90.0) {
    throw new Error(`Declination ${val}° outside permitted range [-90°, +90°]`);
  }

  return degreesToDec(val);
}

/**
 * Convert RA/Dec to 3D Cartesian coordinates on sphere of radius R.
 */
export function equatorialToCartesian(
  raDeg: number,
  decDeg: number,
  radius: number = 100
): CartesianVector3 {
  const alpha = (raDeg * Math.PI) / 180.0;
  const delta = (decDeg * Math.PI) / 180.0;

  const x = radius * Math.cos(delta) * Math.sin(alpha);
  const y = radius * Math.sin(delta);
  const z = -radius * Math.cos(delta) * Math.cos(alpha);

  return {
    x: Number(x.toFixed(9)),
    y: Number(y.toFixed(9)),
    z: Number(z.toFixed(9)),
  };
}

export const radecToCartesian = equatorialToCartesian;

export function radecToVector3Array(
  raDeg: number,
  decDeg: number,
  radius: number = 100
): [number, number, number] {
  const { x, y, z } = equatorialToCartesian(raDeg, decDeg, radius);
  return [x, y, z];
}

export const radecToThreeJs = radecToVector3Array;

/**
 * Convert Three.js Cartesian coordinates back to Equatorial (RA, Dec).
 */
export function cartesianToEquatorial(
  x: number,
  y: number,
  z: number
): EquatorialCoordinates {
  const r = Math.sqrt(x * x + y * y + z * z);
  if (r === 0) {
    return { raDeg: 0, decDeg: 0 };
  }

  const decRad = Math.asin(Math.max(-1.0, Math.min(1.0, y / r)));
  const decDeg = (decRad * 180.0) / Math.PI;

  let raRad = Math.atan2(x, -z);
  if (raRad < 0) {
    raRad += 2 * Math.PI;
  }
  const raDeg = (raRad * 180.0) / Math.PI;

  return {
    raDeg: Number(raDeg.toFixed(9)),
    decDeg: Number(decDeg.toFixed(9)),
  };
}

export const cartesianToRaDec = cartesianToEquatorial;

/**
 * Backward compatibility helpers for Milestone 1 string formatters
 */
export function formatRaHms(raDeg: number): string {
  return degreesToRA(raDeg).formatted;
}

export function formatDecDms(decDeg: number): string {
  return degreesToDec(decDeg).formatted;
}

export function angularSeparationDeg(
  ra1: number,
  dec1: number,
  ra2: number,
  dec2: number
): number {
  const phi1 = (dec1 * Math.PI) / 180.0;
  const phi2 = (dec2 * Math.PI) / 180.0;
  const deltaLambda = ((ra1 - ra2) * Math.PI) / 180.0;

  const sinDphi = Math.sin((phi2 - phi1) / 2.0);
  const sinDlambda = Math.sin(deltaLambda / 2.0);

  const a =
    sinDphi * sinDphi + Math.cos(phi1) * Math.cos(phi2) * sinDlambda * sinDlambda;
  const c = 2.0 * Math.atan2(Math.sqrt(a), Math.sqrt(Math.max(0, 1.0 - a)));

  return Number(((c * 180.0) / Math.PI).toFixed(9));
}

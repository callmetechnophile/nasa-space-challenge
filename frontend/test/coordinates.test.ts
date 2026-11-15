/**
 * SPHEREx 3D Sky Explorer — Milestone 2 Technical Validation
 * Astronomical Coordinate Engine Unit Tests
 */

import { describe, it } from "node:test";
import assert from "node:assert/strict";
import {
  parseRA,
  parseDec,
  raToDegrees,
  decToDegrees,
  degreesToRA,
  degreesToDec,
  equatorialToCartesian,
  cartesianToEquatorial,
  radecToCartesian,
  cartesianToRaDec,
  angularSeparationDeg,
} from "../utils/coordinates.ts";

const EPSILON = 1e-5;

function assertClose(actual: number, expected: number, msg?: string) {
  assert.ok(
    Math.abs(actual - expected) < EPSILON,
    `${msg ?? "Assertion failed"}: expected ${expected}, got ${actual} (diff: ${Math.abs(actual - expected)})`
  );
}

describe("Milestone 2: Coordinate Engine & Validation Tests", () => {
  describe("Task 1: Parsing and Mathematical Utilities", () => {
    it("raToDegrees correctly computes decimal degrees", () => {
      // 08h 55m 10.831s = (8 + 55/60 + 10.831/3600) * 15 = 133.795129167°
      const deg = raToDegrees(8, 55, 10.831);
      assertClose(deg, 133.795129, "WISE 0855 RA calculation");

      // 0h 0m 0s = 0°
      assertClose(raToDegrees(0, 0, 0), 0.0);
      // 24h 0m 0s = 0° (normalized)
      assertClose(raToDegrees(24, 0, 0), 0.0);
    });

    it("decToDegrees correctly preserves negative signs including -00°", () => {
      // -07° 14' 42.53" = -(7 + 14/60 + 42.53/3600) = -7.24514722°
      const wiseDec = decToDegrees(7, 14, 42.53, "-");
      assertClose(wiseDec, -7.245147, "WISE 0855 Dec calculation");

      // CRITICAL: Negative zero degrees: -00° 30' 00" -> -0.5°
      const negZeroDec = decToDegrees(0, 30, 0, "-");
      assertClose(negZeroDec, -0.5, "Sign preservation for -00° 30' 00\"");

      // Positive declination
      assertClose(decToDegrees(45, 0, 0, "+"), 45.0);
    });

    it("degreesToRA and degreesToDec round-trip precision", () => {
      const origRa = 133.795129;
      const parsedRa = degreesToRA(origRa);
      assert.strictEqual(parsedRa.hours, 8);
      assert.strictEqual(parsedRa.minutes, 55);
      assertClose(parsedRa.seconds, 10.831, "Seconds precision");

      const origDec = -7.24514722;
      const parsedDec = degreesToDec(origDec);
      assert.strictEqual(parsedDec.sign, "-");
      assert.strictEqual(parsedDec.d, 7);
      assert.strictEqual(parsedDec.m, 14);
      assertClose(parsedDec.s, 42.53, "Dec seconds precision");
    });
  });

  describe("Task 2: Input Format Parsing & Error Handling", () => {
    it("parseRA handles decimal degrees and sexagesimal formats", () => {
      const resDec = parseRA("133.795129");
      assertClose(resDec.degrees, 133.795129);

      const resSexa = parseRA("08h 55m 10.831s");
      assertClose(resSexa.degrees, 133.795129);

      const resColon = parseRA("08:55:10.831");
      assertClose(resColon.degrees, 133.795129);
    });

    it("parseDec handles decimal degrees, sexagesimal, and -00° 30' 00\"", () => {
      const resDec = parseDec("-7.245147");
      assertClose(resDec.degrees, -7.245147);

      const resSexa = parseDec("-07° 14' 42.53\"");
      assertClose(resSexa.degrees, -7.245147);

      const resNegZero = parseDec("-00° 30' 00\"");
      assertClose(resNegZero.degrees, -0.5, "Must parse -00° 30' 00\" as -0.5°");
      assert.strictEqual(resNegZero.sign, "-");
    });

    it("Strict input rejection for invalid coordinate values", () => {
      // Missing / empty
      assert.throws(() => parseRA(""), /cannot be/);
      assert.throws(() => parseDec("  "), /cannot be/);

      // Negative RA
      assert.throws(() => parseRA("-15.0"), /cannot be negative/);

      // RA out of range without normalization
      assert.throws(() => parseRA("365.0"), /outside permitted range/);

      // Dec out of range
      assert.throws(() => parseDec("95.0"), /outside permitted range/);
      assert.throws(() => parseDec("-90.5"), /outside permitted range/);

      // Invalid minutes & seconds
      assert.throws(() => raToDegrees(10, 65, 0), /minutes must be between 0 and 59/);
      assert.throws(() => decToDegrees(10, 20, 75), /seconds must be between 0 and 59/);

      // Pole boundary checks
      assert.throws(() => decToDegrees(90, 15, 0), /Celestial pole/);

      // Invalid characters
      assert.throws(() => parseRA("12h 30m ABCs"), /Invalid characters/);
      assert.throws(() => parseDec("Dec: 45 deg"), /Invalid characters/);
    });
  });

  describe("Task 3: Eight Required Celestial Test Cases", () => {
    // 1. RA 0°, Dec 0°
    it("Case 1: RA 0°, Dec 0°", () => {
      const v = equatorialToCartesian(0, 0, 1.0);
      assertClose(v.x, 0.0);
      assertClose(v.y, 0.0);
      assertClose(v.z, -1.0);
      const eq = cartesianToEquatorial(v.x, v.y, v.z);
      assertClose(eq.raDeg, 0.0);
      assertClose(eq.decDeg, 0.0);
    });

    // 2. RA 90°, Dec 0°
    it("Case 2: RA 90°, Dec 0°", () => {
      const v = equatorialToCartesian(90, 0, 1.0);
      assertClose(v.x, 1.0);
      assertClose(v.y, 0.0);
      assertClose(v.z, 0.0);
      const eq = cartesianToEquatorial(v.x, v.y, v.z);
      assertClose(eq.raDeg, 90.0);
      assertClose(eq.decDeg, 0.0);
    });

    // 3. RA 180°, Dec 0°
    it("Case 3: RA 180°, Dec 0°", () => {
      const v = equatorialToCartesian(180, 0, 1.0);
      assertClose(v.x, 0.0);
      assertClose(v.y, 0.0);
      assertClose(v.z, 1.0);
      const eq = cartesianToEquatorial(v.x, v.y, v.z);
      assertClose(eq.raDeg, 180.0);
      assertClose(eq.decDeg, 0.0);
    });

    // 4. RA 270°, Dec 0°
    it("Case 4: RA 270°, Dec 0°", () => {
      const v = equatorialToCartesian(270, 0, 1.0);
      assertClose(v.x, -1.0);
      assertClose(v.y, 0.0);
      assertClose(v.z, 0.0);
      const eq = cartesianToEquatorial(v.x, v.y, v.z);
      assertClose(eq.raDeg, 270.0);
      assertClose(eq.decDeg, 0.0);
    });

    // 5. RA 0°, Dec +90° (NCP)
    it("Case 5: RA 0°, Dec +90°", () => {
      const v = equatorialToCartesian(0, 90, 1.0);
      assertClose(v.x, 0.0);
      assertClose(v.y, 1.0);
      assertClose(v.z, 0.0);
      const eq = cartesianToEquatorial(v.x, v.y, v.z);
      assertClose(eq.decDeg, 90.0);
    });

    // 6. RA 0°, Dec -90° (SCP)
    it("Case 6: RA 0°, Dec -90°", () => {
      const v = equatorialToCartesian(0, -90, 1.0);
      assertClose(v.x, 0.0);
      assertClose(v.y, -1.0);
      assertClose(v.z, 0.0);
      const eq = cartesianToEquatorial(v.x, v.y, v.z);
      assertClose(eq.decDeg, -90.0);
    });

    // 7. RA 359.999°, Dec 0°
    it("Case 7: RA 359.999°, Dec 0°", () => {
      const v = equatorialToCartesian(359.999, 0, 1.0);
      const len = Math.hypot(v.x, v.y, v.z);
      assertClose(len, 1.0);
      const eq = cartesianToEquatorial(v.x, v.y, v.z);
      assertClose(eq.raDeg, 359.999);
      assertClose(eq.decDeg, 0.0);
    });

    // 8. WISE 0855 Target Validation Case
    it("Case 8: WISE 0855 Navigation Preset", () => {
      const parsedRa = parseRA("08h 55m 10.831s");
      const parsedDec = parseDec("-07° 14' 42.53\"");

      assertClose(parsedRa.degrees, 133.795129, "WISE 0855 expected RA");
      assertClose(parsedDec.degrees, -7.245147, "WISE 0855 expected Dec");

      const v = equatorialToCartesian(parsedRa.degrees, parsedDec.degrees, 1.0);
      const len = Math.hypot(v.x, v.y, v.z);
      assertClose(len, 1.0, "Direction vector must be unit length");

      const recovered = cartesianToEquatorial(v.x, v.y, v.z);
      assertClose(recovered.raDeg, 133.795129);
      assertClose(recovered.decDeg, -7.245147);
    });
  });
});

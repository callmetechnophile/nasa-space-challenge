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
  formatRaHms,
  formatDecDms,
  angularSeparationDeg,
} from "../utils/coordinates.ts";

describe("SPHEREx M2 Scientific Validation: Edge Cases & Mathematical Precision", () => {
  it("Edge Case 1: RA = 0°, Dec = 0° (Vernal Equinox)", () => {
    const raRes = parseRA("0.000000");
    const decRes = parseDec("0.000000");
    assert.equal(raRes.degrees, 0);
    assert.equal(decRes.degrees, 0);

    const { x, y, z } = equatorialToCartesian(0, 0, 100);
    // In our convention: RA 0, Dec 0 is along -Z
    assert.ok(Math.abs(x) < 1e-9);
    assert.ok(Math.abs(y) < 1e-9);
    assert.ok(Math.abs(z - (-100)) < 1e-9);

    const { raDeg, decDeg } = cartesianToEquatorial(x, y, z);
    assert.ok(Math.abs(raDeg - 0) < 1e-6);
    assert.ok(Math.abs(decDeg - 0) < 1e-6);
  });

  it("Edge Case 2: RA = 90°, Dec = 0°", () => {
    const raRes = parseRA("90.000000");
    assert.equal(raRes.degrees, 90);
    assert.equal(raRes.hours, 6);
    assert.equal(raRes.minutes, 0);
    assert.equal(raRes.seconds, 0);

    const { x, y, z } = equatorialToCartesian(90, 0, 100);
    // RA 90 is along +X
    assert.ok(Math.abs(x - 100) < 1e-9);
    assert.ok(Math.abs(y) < 1e-9);
    assert.ok(Math.abs(z) < 1e-9);

    const { raDeg, decDeg } = cartesianToEquatorial(x, y, z);
    assert.ok(Math.abs(raDeg - 90) < 1e-6);
    assert.ok(Math.abs(decDeg - 0) < 1e-6);
  });

  it("Edge Case 3: RA = 180°, Dec = 0°", () => {
    const raRes = parseRA("180.000000");
    assert.equal(raRes.degrees, 180);
    assert.equal(raRes.hours, 12);

    const { x, y, z } = equatorialToCartesian(180, 0, 100);
    // RA 180 is along +Z
    assert.ok(Math.abs(x) < 1e-9);
    assert.ok(Math.abs(y) < 1e-9);
    assert.ok(Math.abs(z - 100) < 1e-9);

    const { raDeg, decDeg } = cartesianToEquatorial(x, y, z);
    assert.ok(Math.abs(raDeg - 180) < 1e-6);
    assert.ok(Math.abs(decDeg - 0) < 1e-6);
  });

  it("Edge Case 4: RA = 270°, Dec = 0°", () => {
    const raRes = parseRA("270.000000");
    assert.equal(raRes.degrees, 270);
    assert.equal(raRes.hours, 18);

    const { x, y, z } = equatorialToCartesian(270, 0, 100);
    // RA 270 is along -X
    assert.ok(Math.abs(x - (-100)) < 1e-9);
    assert.ok(Math.abs(y) < 1e-9);
    assert.ok(Math.abs(z) < 1e-9);

    const { raDeg, decDeg } = cartesianToEquatorial(x, y, z);
    assert.ok(Math.abs(raDeg - 270) < 1e-6);
    assert.ok(Math.abs(decDeg - 0) < 1e-6);
  });

  it("Edge Case 5: RA = 0°, Dec = +90° (North Celestial Pole)", () => {
    const decRes = parseDec("+90.000000");
    assert.equal(decRes.degrees, 90);

    const { x, y, z } = equatorialToCartesian(0, 90, 100);
    // North pole is along +Y
    assert.ok(Math.abs(x) < 1e-9);
    assert.ok(Math.abs(y - 100) < 1e-9);
    assert.ok(Math.abs(z) < 1e-9);

    const { decDeg } = cartesianToEquatorial(x, y, z);
    assert.ok(Math.abs(decDeg - 90) < 1e-6);
  });

  it("Edge Case 6: RA = 0°, Dec = -90° (South Celestial Pole)", () => {
    const decRes = parseDec("-90.000000");
    assert.equal(decRes.degrees, -90);

    const { x, y, z } = equatorialToCartesian(0, -90, 100);
    // South pole is along -Y
    assert.ok(Math.abs(x) < 1e-9);
    assert.ok(Math.abs(y - (-100)) < 1e-9);
    assert.ok(Math.abs(z) < 1e-9);

    const { decDeg } = cartesianToEquatorial(x, y, z);
    assert.ok(Math.abs(decDeg - (-90)) < 1e-6);
  });

  it("Edge Case 7: RA = 359.999°, Dec = 0°", () => {
    const raRes = parseRA("359.999");
    assert.ok(Math.abs(raRes.degrees - 359.999) < 1e-6);
    assert.equal(raRes.hours, 23);
    assert.equal(raRes.minutes, 59);
    assert.ok(Math.abs(raRes.seconds - 59.76) < 0.01);
  });

  it("Edge Case 8: Negative zero declination (-00° 30' 00\")", () => {
    const res = parseDec("-00° 30' 00\"");
    assert.equal(res.sign, "-");
    assert.equal(res.degrees, -0.5);
    assert.equal(res.d, 0);
    assert.equal(res.m, 30);
    assert.equal(res.s, 0);
  });

  it("Invalid Input Rejection Policy", () => {
    // Negative RA
    assert.throws(() => parseRA("-10"), /cannot be negative/);
    assert.throws(() => parseRA("-0.01"), /cannot be negative/);

    // RA out of range
    assert.throws(() => parseRA("360.001"), /outside permitted range/);
    assert.throws(() => parseRA("400.5"), /outside permitted range/);

    // Dec out of range
    assert.throws(() => parseDec("90.0001"), /outside permitted range/);
    assert.throws(() => parseDec("-91.0"), /outside permitted range/);

    // Pole minute/second overflow
    assert.throws(() => parseDec("+90° 01' 00\""), /cannot have non-zero/);
    assert.throws(() => parseDec("-90° 00' 01\""), /cannot have non-zero/);

    // Invalid minutes/seconds
    assert.throws(() => parseRA("12h 65m 00s"), /minutes must be between 0 and 59/);
    assert.throws(() => parseRA("12h 10m 75s"), /seconds must be between 0 and 59/);
    assert.throws(() => parseDec("+45° 60' 00\""), /minutes must be between 0 and 59/);
    assert.throws(() => parseDec("+45° 10' 65\""), /seconds must be between 0 and 59/);

    // Non-numeric malformed strings
    assert.throws(() => parseRA("alpha_centauri"), /Invalid characters/);
    assert.throws(() => parseDec("north_pole"), /Invalid characters/);
  });

  it("Round-Trip Precision across 200 random celestial coordinates", () => {
    for (let i = 0; i < 200; i++) {
      const origRa = Math.random() * 359.999;
      const origDec = (Math.random() - 0.5) * 179.999;

      const raObj = degreesToRA(origRa);
      const decObj = degreesToDec(origDec);

      const restoredRa = raToDegrees(raObj.hours, raObj.minutes, raObj.seconds);
      const restoredDec = decToDegrees(decObj.d, decObj.m, decObj.s, decObj.sign);

      const sep = angularSeparationDeg(origRa, origDec, restoredRa, restoredDec);
      // Angular error must be less than 0.01 arcseconds (0.01 / 3600 = 2.77e-6 deg)
      assert.ok(
        sep < 0.000005,
        `Separation ${sep}° exceeds threshold for RA ${origRa}, Dec ${origDec}`
      );
    }
  });

  it("WISE 0855 Target Precision Verification", () => {
    // 08h 55m 10.831s
    const wiseRa = raToDegrees(8, 55, 10.831);
    // 8 + 55/60 + 10.831/3600 = 8.9196752777... hours * 15 = 133.7951291666... deg
    assert.ok(Math.abs(wiseRa - 133.79512917) < 1e-7);

    // -07° 14' 42.53"
    const wiseDec = decToDegrees(7, 14, 42.53, "-");
    // -(7 + 14/60 + 42.53/3600) = -7.245147222... deg
    assert.ok(Math.abs(wiseDec - (-7.24514722)) < 1e-7);

    // Verify error is strictly within 0.001 arcseconds
    const arcsecErrorRa = Math.abs(wiseRa - 133.795129) * 3600;
    const arcsecErrorDec = Math.abs(wiseDec - (-7.245147)) * 3600;
    assert.ok(arcsecErrorRa < 0.001, `RA error ${arcsecErrorRa}" must be < 0.001"`);
    assert.ok(arcsecErrorDec < 0.001, `Dec error ${arcsecErrorDec}" must be < 0.001"`);
  });
});

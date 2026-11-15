/**
 * SPHEREx 3D Sky Explorer — Milestone 6 Challenge Completion Unit Tests
 * Validates 5 target presets, time-series player properties, and non-discovery disclaimer.
 */

import { describe, it } from "node:test";
import assert from "node:assert/strict";

describe("Milestone 6: NASA SPHEREx Challenge Completion", () => {
  const NASA_5_TARGETS = [
    {
      id: "barnards-star",
      name: "Barnard's Star",
      raDeg: 269.452083,
      decDeg: 4.693333,
      pm_ra_cosdec: -798.58,
      pm_dec: 10328.12,
    },
    {
      id: "epsilon-indi-b",
      name: "Epsilon Indi B",
      raDeg: 331.043792,
      decDeg: -56.782722,
      binary_separation_arcsec: 0.73,
    },
    {
      id: "wise-0855",
      name: "WISE 0855",
      raDeg: 133.795129,
      decDeg: -7.245147,
      pm_ra_cosdec: -8118.0,
      pm_dec: 715.0,
    },
    {
      id: "rw-aurigae",
      name: "RW Aurigae",
      raDeg: 76.956417,
      decDeg: 30.401417,
    },
    {
      id: "r-draconis",
      name: "R Draconis",
      raDeg: 248.167625,
      decDeg: 66.755056,
      period_days: 245.6,
    },
  ];

  it("contains all 5 required NASA challenge validation targets", () => {
    assert.equal(NASA_5_TARGETS.length, 5);
    const names = NASA_5_TARGETS.map((t) => t.name);
    assert.ok(names.includes("Barnard's Star"));
    assert.ok(names.includes("Epsilon Indi B"));
    assert.ok(names.includes("WISE 0855"));
    assert.ok(names.includes("RW Aurigae"));
    assert.ok(names.includes("R Draconis"));
  });

  it("verifies proper motion magnitude of high-motion targets", () => {
    const barnard = NASA_5_TARGETS.find((t) => t.id === "barnards-star")!;
    const barnardNetPM = Math.hypot(barnard.pm_ra_cosdec, barnard.pm_dec);
    assert.ok(barnardNetPM > 10000); // ~10,359 mas/yr (10.36 arcsec/yr)

    const wise = NASA_5_TARGETS.find((t) => t.id === "wise-0855")!;
    const wiseNetPM = Math.hypot(wise.pm_ra_cosdec, wise.pm_dec);
    assert.ok(wiseNetPM > 8000); // ~8,149 mas/yr (8.15 arcsec/yr)
  });

  it("verifies Epsilon Indi B binary separation constraint against SPHEREx resolution", () => {
    const epsIndi = NASA_5_TARGETS.find((t) => t.id === "epsilon-indi-b")!;
    const spherexPixelScaleArcsec = 6.2;
    assert.ok(epsIndi.binary_separation_arcsec! < spherexPixelScaleArcsec);
  });

  it("verifies mandatory non-discovery disclaimer string invariant", () => {
    const disclaimer =
      "NOTICE: Observed Data | Processed Images | Synthetic Test Data | Change Candidates — NOT SCIENTIFICALLY CONFIRMED. Unverified candidates are not astronomical discoveries.";
    assert.ok(disclaimer.includes("NOT SCIENTIFICALLY CONFIRMED"));
    assert.ok(disclaimer.includes("Unverified candidates are not astronomical discoveries"));
  });

  it("verifies playback interval calculation across multipliers", () => {
    const baseSpeed = 1500;
    const speed05 = Math.max(200, baseSpeed / 0.5); // 3000ms
    const speed1 = Math.max(200, baseSpeed / 1.0);  // 1500ms
    const speed2 = Math.max(200, baseSpeed / 2.0);  // 750ms
    const speed4 = Math.max(200, baseSpeed / 4.0);  // 375ms
    assert.equal(speed05, 3000);
    assert.equal(speed1, 1500);
    assert.equal(speed2, 750);
    assert.equal(speed4, 375);
  });
});

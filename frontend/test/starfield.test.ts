/**
 * SPHEREx 3D Sky Explorer — Milestone 1 Technical Validation
 * Task 2: Star Field Distribution and Geometry Validation Tests
 */

import { describe, it } from "node:test";
import assert from "node:assert/strict";

describe("Task 2: Procedural Star Field Technical Validation", () => {
  // Replicate the generator logic from StarField.tsx
  function generateStars(count = 4500, radius = 100) {
    const pos = new Float32Array(count * 3);
    const col = new Float32Array(count * 3);

    let seed = 42891;
    const lcg = () => {
      seed = (seed * 1664525 + 1013904223) % 4294967296;
      return seed / 4294967296;
    };

    for (let i = 0; i < count; i++) {
      const u = lcg(); // RA azimuth fraction [0, 1)
      const v = lcg(); // Dec polar fraction [0, 1)

      const theta = u * 2.0 * Math.PI;
      const phi = Math.acos(2.0 * v - 1.0);

      const x = radius * Math.sin(phi) * Math.sin(theta);
      const y = radius * Math.cos(phi);
      const z = -radius * Math.sin(phi) * Math.cos(theta);

      pos[i * 3] = x;
      pos[i * 3 + 1] = y;
      pos[i * 3 + 2] = z;

      const brightnessFactor = 0.55 + 0.45 * Math.pow(lcg(), 3.0);
      col[i * 3] = brightnessFactor;
      col[i * 3 + 1] = brightnessFactor;
      col[i * 3 + 2] = brightnessFactor;
    }
    return { pos, col };
  }

  it("All stars lie precisely on the spherical boundary of radius R", () => {
    const R = 100;
    const { pos } = generateStars(4500, R);

    for (let i = 0; i < 4500; i++) {
      const x = pos[i * 3];
      const y = pos[i * 3 + 1];
      const z = pos[i * 3 + 2];
      const r = Math.hypot(x, y, z);
      assert.ok(
        Math.abs(r - R) < 1e-4,
        `Star ${i} distance ${r} deviated from radius ${R}`
      );
    }
  });

  it("Uniform spherical distribution (Archimedes Equal-Area Test)", () => {
    const { pos } = generateStars(4500, 100);
    // Divide sphere into 10 equal-area latitude bands:
    // For unit sphere, area of slice between y1 and y2 is 2*pi*(y2 - y1).
    // With 10 equal slices along Y from -100 to +100 (each Delta Y = 20),
    // each slice has exactly equal surface area.
    const numBins = 10;
    const binCounts = new Array(numBins).fill(0);

    for (let i = 0; i < 4500; i++) {
      const y = pos[i * 3 + 1]; // y in [-100, 100]
      const normalizedY = Math.min(0.9999, Math.max(0, (y + 100) / 200));
      const bin = Math.floor(normalizedY * numBins);
      binCounts[bin]++;
    }

    const expectedPerBin = 4500 / numBins; // 450 stars per bin
    for (let b = 0; b < numBins; b++) {
      // With N=450, 3*sigma = 3 * sqrt(450 * 0.9) ~ 60 stars
      // Check count is within ~20% of expectation, proving no polar clustering or equatorial bunching
      const diff = Math.abs(binCounts[b] - expectedPerBin);
      assert.ok(
        diff < 75,
        `Bin ${b} count ${binCounts[b]} deviated too much from uniform expectation ${expectedPerBin}`
      );
    }
  });

  it("Distribution is deterministic and stable across calls", () => {
    const run1 = generateStars(4500, 100);
    const run2 = generateStars(4500, 100);

    for (let i = 0; i < run1.pos.length; i++) {
      assert.strictEqual(
        run1.pos[i],
        run2.pos[i],
        `Position index ${i} must match identically`
      );
    }
  });

  it("Colors and brightness factors are strictly normalized in [0, 1]", () => {
    const { col } = generateStars(4500, 100);
    for (let i = 0; i < col.length; i++) {
      assert.ok(col[i] >= 0.0 && col[i] <= 1.0, `Color component ${col[i]} out of [0, 1]`);
    }
  });
});

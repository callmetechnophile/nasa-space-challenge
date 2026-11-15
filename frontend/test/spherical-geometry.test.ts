import { describe, it } from "node:test";
import assert from "node:assert/strict";
import * as THREE from "three";
import {
  equatorialToCartesian,
  cartesianToEquatorial,
  radecToVector3Array,
  angularSeparationDeg,
} from "../utils/coordinates.ts";

describe("SPHEREx M3 Geometry Tests: Spherical Projection & Three.js BufferGeometry", () => {
  it("T08.1: Vertex Radius Uniformity on R=98.0 Celestial Sphere", () => {
    const testPoints = [
      { ra: 0.0, dec: 0.0 },
      { ra: 90.0, dec: 0.0 },
      { ra: 180.0, dec: 0.0 },
      { ra: 270.0, dec: 0.0 },
      { ra: 45.0, dec: 45.0 },
      { ra: 133.795129, dec: -7.245147 },
      { ra: 359.99, dec: 0.0 },
      { ra: 0.0, dec: 90.0 },
      { ra: 0.0, dec: -90.0 },
    ];

    const targetRadius = 98.0;
    for (const pt of testPoints) {
      const vec = radecToVector3Array(pt.ra, pt.dec, targetRadius);
      const computedR = Math.sqrt(vec[0] * vec[0] + vec[1] * vec[1] + vec[2] * vec[2]);
      assert.ok(
        Math.abs(computedR - targetRadius) < 1e-5,
        `Radius at RA=${pt.ra}, Dec=${pt.dec} is ${computedR}, expected ${targetRadius}`
      );
    }
  });

  it("T08.2: Axis Orientation & Cardinal Point Consistency", () => {
    const R = 98.0;

    // NCP (Dec = +90°) -> +Y
    const ncp = equatorialToCartesian(0, 90, R);
    assert.ok(Math.abs(ncp.x) < 1e-6);
    assert.ok(Math.abs(ncp.y - R) < 1e-6);
    assert.ok(Math.abs(ncp.z) < 1e-6);

    // SCP (Dec = -90°) -> -Y
    const scp = equatorialToCartesian(0, -90, R);
    assert.ok(Math.abs(scp.x) < 1e-6);
    assert.ok(Math.abs(scp.y - (-R)) < 1e-6);
    assert.ok(Math.abs(scp.z) < 1e-6);

    // Vernal Equinox (RA = 0°, Dec = 0°) -> -Z
    const equinox = equatorialToCartesian(0, 0, R);
    assert.ok(Math.abs(equinox.x) < 1e-6);
    assert.ok(Math.abs(equinox.y) < 1e-6);
    assert.ok(Math.abs(equinox.z - (-R)) < 1e-6);

    // RA = 90° (6h), Dec = 0° -> +X
    const ra90 = equatorialToCartesian(90, 0, R);
    assert.ok(Math.abs(ra90.x - R) < 1e-6);
    assert.ok(Math.abs(ra90.y) < 1e-6);
    assert.ok(Math.abs(ra90.z) < 1e-6);

    // RA = 270° (18h), Dec = 0° -> -X
    const ra270 = equatorialToCartesian(270, 0, R);
    assert.ok(Math.abs(ra270.x - (-R)) < 1e-6);
    assert.ok(Math.abs(ra270.y) < 1e-6);
    assert.ok(Math.abs(ra270.z) < 1e-6);
  });

  it("T09: UV Coordinates and BufferGeometry Construction", () => {
    // Construct a synthetic 8x8 quad mesh
    const nx = 8;
    const ny = 8;
    const numVerts = (nx + 1) * (ny + 1);

    const positions = new Float32Array(numVerts * 3);
    const uvs = new Float32Array(numVerts * 2);
    const indices: number[] = [];

    let vIdx = 0;
    for (let j = 0; j <= ny; j++) {
      const v = j / ny;
      const dec = -10.0 + (j / ny) * 2.0; // [-10, -8]
      for (let i = 0; i <= nx; i++) {
        const u = i / nx;
        const ra = 130.0 + (i / nx) * 2.0; // [130, 132]

        const p = equatorialToCartesian(ra, dec, 98.0);
        positions[vIdx * 3] = p.x;
        positions[vIdx * 3 + 1] = p.y;
        positions[vIdx * 3 + 2] = p.z;

        uvs[vIdx * 2] = u;
        uvs[vIdx * 2 + 1] = v;
        vIdx++;
      }
    }

    const stride = nx + 1;
    for (let j = 0; j < ny; j++) {
      for (let i = 0; i < nx; i++) {
        const v00 = j * stride + i;
        const v10 = j * stride + (i + 1);
        const v01 = (j + 1) * stride + i;
        const v11 = (j + 1) * stride + (i + 1);
        indices.push(v00, v10, v11);
        indices.push(v00, v11, v01);
      }
    }

    // Build Three.js BufferGeometry
    const geom = new THREE.BufferGeometry();
    geom.setAttribute("position", new THREE.BufferAttribute(positions, 3));
    geom.setAttribute("uv", new THREE.BufferAttribute(uvs, 2));
    geom.setIndex(new THREE.BufferAttribute(new Uint16Array(indices), 1));
    geom.computeVertexNormals();

    assert.equal(geom.attributes.position.count, 81);
    assert.equal(geom.attributes.uv.count, 81);
    assert.equal(indices.length, 64 * 2 * 3); // 128 triangles = 384 indices

    // Validate UV range [0, 1]
    for (let k = 0; k < uvs.length; k += 2) {
      assert.ok(uvs[k] >= 0.0 && uvs[k] <= 1.0, `U coordinate ${uvs[k]} out of [0, 1] range`);
      assert.ok(uvs[k + 1] >= 0.0 && uvs[k + 1] <= 1.0, `V coordinate ${uvs[k + 1]} out of [0, 1] range`);
    }

    // Clean disposal test
    geom.dispose();
  });

  it("T14: RA Wraparound Mesh Topology", () => {
    // Test RA wraparound from 359.8° to 0.2° across the meridian
    const raStart = 359.8;
    const raEnd = 0.2;
    const dec = 5.0;

    const pStart = equatorialToCartesian(raStart, dec, 98.0);
    const pEnd = equatorialToCartesian(raEnd, dec, 98.0);

    // Compute Euclidean distance between vertices across 0.4° span
    const dx = pEnd.x - pStart.x;
    const dy = pEnd.y - pStart.y;
    const dz = pEnd.z - pStart.z;
    const dist = Math.sqrt(dx * dx + dy * dy + dz * dz);

    // Expected chord length: 2 * R * cos(dec) * sin(dRA / 2) where dRA = 0.4 deg
    const decRad = (dec * Math.PI) / 180.0;
    const thetaRad = (0.4 * Math.PI) / 180.0;
    const expectedChord = 2.0 * (98.0 * Math.cos(decRad)) * Math.sin(thetaRad / 2.0);

    assert.ok(
      Math.abs(dist - expectedChord) < 1e-4,
      `Chord length across meridian is ${dist}, expected ${expectedChord}. Mesh must not stretch across entire diameter.`
    );
  });
});

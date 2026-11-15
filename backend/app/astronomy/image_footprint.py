"""Image Footprint & Spherical Mesh Generator for SPHEREx 3D Sky Explorer.
Computes WCS-derived curvilinear footprints, adaptive spherical meshes,
and Three.js BufferGeometry vertex/index/UV payloads.
"""

from __future__ import annotations

import math
from typing import List, Tuple, Dict, Any, Optional
import numpy as np
from pydantic import BaseModel, Field

from astropy.wcs import WCS
from app.astronomy.wcs_processor import pixel_to_world, get_pixel_scales_arcsec


class SphericalMeshGeometry(BaseModel):
    """Payload representing a 3D Three.js BufferGeometry on the celestial sphere."""
    radius: float = Field(..., description="Sphere radius in Three.js units")
    grid_density_x: int = Field(..., description="Number of subdivisions along X axis")
    grid_density_y: int = Field(..., description="Number of subdivisions along Y axis")
    vertex_count: int = Field(..., description="Total number of vertices")
    index_count: int = Field(..., description="Total number of triangle indices")
    vertices: List[float] = Field(..., description="Flattened 3D position array [x0, y0, z0, x1, y1, z1, ...]")
    uvs: List[float] = Field(..., description="Flattened UV coordinate array [u0, v0, u1, v1, ...]")
    indices: List[int] = Field(..., description="Triangle vertex index list")
    corners_radec: List[Tuple[float, float]] = Field(..., description="4 corners in (RA, Dec) degrees")
    center_radec: Tuple[float, float] = Field(..., description="Center in (RA, Dec) degrees")
    angular_diameter_deg: float = Field(..., description="Approximate field diameter in degrees")


def radec_to_cartesian(
    ra_deg: float | np.ndarray,
    dec_deg: float | np.ndarray,
    radius: float = 98.0
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Convert RA/Dec degrees to 3D Cartesian coordinates on celestial sphere.
    Strictly follows the SPHEREx M1/M2 ICRS convention:
      +Y: North Celestial Pole (Dec = +90°)
      -Y: South Celestial Pole (Dec = -90°)
      -Z: Vernal Equinox (RA = 0°, Dec = 0°)
      +X: RA = 90° (6h), Dec = 0°
    """
    alpha = np.radians(ra_deg)
    delta = np.radians(dec_deg)

    x = radius * np.cos(delta) * np.sin(alpha)
    y = radius * np.sin(delta)
    z = -radius * np.cos(delta) * np.cos(alpha)

    return x, y, z


def generate_spherical_mesh(
    wcs: WCS,
    width: int,
    height: int,
    radius: float = 98.0,
    min_grid: int = 8,
    max_grid: int = 32
) -> SphericalMeshGeometry:
    """Generate adaptive spherical mesh geometry for an astronomical image.
    Tessellates the image footprint in pixel space, maps each vertex through WCS
    into RA/Dec, and projects onto the celestial sphere.
    """
    # 1. Determine adaptive grid density based on angular extent
    mean_scale_arcsec, _, _ = get_pixel_scales_arcsec(wcs)
    diag_pixels = math.sqrt(width * width + height * height)
    angular_extent_deg = (diag_pixels * mean_scale_arcsec) / 3600.0

    # Scale density: larger or heavily distorted fields get denser grids
    if angular_extent_deg < 0.5:
        density = min_grid  # 8x8 is ample for small FOV (< 30 arcmin)
    elif angular_extent_deg < 5.0:
        density = 16
    elif angular_extent_deg < 20.0:
        density = 24
    else:
        density = max_grid  # 32x32 for wide-field or all-sky tiles

    nx = density
    ny = max(int(density * (height / width)), min_grid)

    # 2. Pixel grid
    x_pix = np.linspace(0.0, float(width - 1), nx + 1)
    y_pix = np.linspace(0.0, float(height - 1), ny + 1)
    grid_x, grid_y = np.meshgrid(x_pix, y_pix)

    # 3. WCS transformation: Pixel -> World (RA, Dec)
    ra_deg, dec_deg = pixel_to_world(wcs, grid_x, grid_y, origin=0)

    # 4. Spherical Cartesian projection: (RA, Dec) -> (x, y, z)
    x_3d, y_3d, z_3d = radec_to_cartesian(ra_deg, dec_deg, radius=radius)

    # 5. Build vertex & UV buffers
    # UV mapping: u in [0, 1] from left to right; v in [0, 1] from bottom to top
    # Since numpy grid_y has row 0 at y_pix[0]=0 (bottom of FITS image),
    # u = x_pix / (width - 1), v = y_pix / (height - 1)
    u_norm = np.linspace(0.0, 1.0, nx + 1)
    v_norm = np.linspace(0.0, 1.0, ny + 1)
    grid_u, grid_v = np.meshgrid(u_norm, v_norm)

    # Flatten arrays
    flat_x = x_3d.flatten()
    flat_y = y_3d.flatten()
    flat_z = z_3d.flatten()
    flat_u = grid_u.flatten()
    flat_v = grid_v.flatten()

    num_vertices = len(flat_x)

    vertices: List[float] = []
    uvs: List[float] = []

    for k in range(num_vertices):
        vertices.extend([
            round(float(flat_x[k]), 5),
            round(float(flat_y[k]), 5),
            round(float(flat_z[k]), 5),
        ])
        uvs.extend([
            round(float(flat_u[k]), 5),
            round(float(flat_v[k]), 5),
        ])

    # 6. Build triangle indices (quads split into two triangles)
    indices: List[int] = []
    stride = nx + 1

    for j in range(ny):
        for i in range(nx):
            v00 = j * stride + i
            v10 = j * stride + (i + 1)
            v01 = (j + 1) * stride + i
            v11 = (j + 1) * stride + (i + 1)

            # Triangle 1
            indices.extend([v00, v10, v11])
            # Triangle 2
            indices.extend([v00, v11, v01])

    # 7. Footprint corners & center
    c_x = (width - 1) / 2.0
    c_y = (height - 1) / 2.0
    center_ra, center_dec = pixel_to_world(wcs, c_x, c_y, origin=0)

    corner_pixels = np.array([
        [0.0, 0.0],
        [float(width - 1), 0.0],
        [float(width - 1), float(height - 1)],
        [0.0, float(height - 1)]
    ])
    c_ra, c_dec = pixel_to_world(wcs, corner_pixels[:, 0], corner_pixels[:, 1], origin=0)
    corners = [(round(float(c_ra[i]), 6), round(float(c_dec[i]), 6)) for i in range(4)]

    return SphericalMeshGeometry(
        radius=radius,
        grid_density_x=nx,
        grid_density_y=ny,
        vertex_count=num_vertices,
        index_count=len(indices),
        vertices=vertices,
        uvs=uvs,
        indices=indices,
        corners_radec=corners,
        center_radec=(round(float(center_ra), 6), round(float(center_dec), 6)),
        angular_diameter_deg=round(angular_extent_deg, 5),
    )

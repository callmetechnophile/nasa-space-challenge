"""SPHEREx Spectral Compatibility Evaluator (Milestone 5).
Evaluates Linear Variable Filter (LVF) transmission wavelength equivalence
between multi-epoch observations using the FITS WAVE-TAB extension (WCS-WAVE).
"""

from __future__ import annotations

import numpy as np
from typing import Tuple, Dict, Any, Optional
from scipy.interpolate import RegularGridInterpolator
from astropy.io import fits
from astropy.wcs import WCS


class LVFWavelengthModel:
    """Evaluates effective wavelength λ_eff(x, y) and bandpass width Δλ(x, y)
    from SPHEREx WCS-WAVE binary table extension.
    """

    def __init__(self, x_grid: np.ndarray, y_grid: np.ndarray, values: np.ndarray):
        """
        x_grid: 1D array of X pixel indices (1-based, e.g. [1, 256, ..., 2040])
        y_grid: 1D array of Y pixel indices (1-based, e.g. [1, 256, ..., 2040])
        values: 3D array of shape (len(y_grid), len(x_grid), 2)
                values[:, :, 0] = central wavelength in microns
                values[:, :, 1] = FWHM bandwidth in microns
        """
        self.x_grid = np.asarray(x_grid, dtype=np.float64)
        self.y_grid = np.asarray(y_grid, dtype=np.float64)
        vals = np.asarray(values, dtype=np.float64)

        if vals.ndim == 3 and vals.shape[0] == 2:
            # Shape is (2, ny, nx)
            val_lambda = vals[0]
            val_delta = vals[1]
        elif vals.ndim == 3 and vals.shape[-1] == 2:
            # Shape is (ny, nx, 2)
            val_lambda = vals[:, :, 0]
            val_delta = vals[:, :, 1]
        else:
            raise ValueError(f"Unexpected shape for WCS-WAVE values array: {vals.shape}")

        self._interp_lambda = RegularGridInterpolator(
            (self.y_grid, self.x_grid),
            val_lambda,
            bounds_error=False,
            fill_value=None,  # extrapolates if needed within detector bounds
        )
        self._interp_delta = RegularGridInterpolator(
            (self.y_grid, self.x_grid),
            val_delta,
            bounds_error=False,
            fill_value=None,
        )

    @classmethod
    def from_fits_hdu(cls, wave_hdu: fits.BinTableHDU) -> "LVFWavelengthModel":
        """Instantiate from a SPHEREx WCS-WAVE BinTableHDU."""
        col_x = wave_hdu.data["X"][0]
        col_y = wave_hdu.data["Y"][0]
        col_vals = wave_hdu.data["VALUES"][0]
        return cls(col_x, col_y, col_vals)

    @classmethod
    def from_fits_file(cls, filepath: str) -> Optional["LVFWavelengthModel"]:
        """Instantiate by loading WCS-WAVE from a FITS file."""
        with fits.open(filepath) as hdul:
            if "WCS-WAVE" in hdul:
                return cls.from_fits_hdu(hdul["WCS-WAVE"])
            # Fallback check for detector approximation
            detector = hdul[1].header.get("DETECTOR", 1) if len(hdul) > 1 else 1
            return cls.synthetic_default(detector=detector)

    @classmethod
    def synthetic_default(cls, detector: int = 1) -> "LVFWavelengthModel":
        """Provide calibrated default linear variable filter model for detector 1-6
        in case WCS-WAVE table is missing.
        """
        band_ranges = {
            1: (0.75, 1.12),
            2: (1.12, 1.67),
            3: (1.67, 2.42),
            4: (2.42, 3.82),
            5: (3.82, 4.42),
            6: (4.42, 5.00),
        }
        lmin, lmax = band_ranges.get(int(detector), (0.75, 1.12))
        x_grid = np.linspace(1, 2040, 9)
        y_grid = np.linspace(1, 2040, 9)
        values = np.zeros((9, 9, 2), dtype=np.float64)

        for i, y in enumerate(y_grid):
            # Y=1 is lmax, Y=2040 is lmin on detector 1
            frac = (2040.0 - y) / 2039.0
            lam = lmin + frac * (lmax - lmin)
            dlam = lam / 40.0  # R ~ 40
            for j in range(9):
                values[i, j, 0] = lam
                values[i, j, 1] = dlam

        return cls(x_grid, y_grid, values)

    def evaluate(self, x: np.ndarray, y: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Evaluate (λ, Δλ) in microns for 1-based pixel coordinates (x, y)."""
        pts = np.column_stack([np.asarray(y).ravel(), np.asarray(x).ravel()])
        lam = self._interp_lambda(pts).reshape(np.shape(x))
        dlam = self._interp_delta(pts).reshape(np.shape(x))
        return lam, dlam


def evaluate_spectral_compatibility(
    wave_model1: LVFWavelengthModel,
    wave_model2: LVFWavelengthModel,
    x1: np.ndarray,
    y1: np.ndarray,
    x2: np.ndarray,
    y2: np.ndarray,
    tolerance: float = 0.02,
) -> Dict[str, Any]:
    """Evaluate spectral compatibility between two observations at mapped pixel coordinates.

    Parameters:
    -----------
    wave_model1, wave_model2 : LVFWavelengthModel
    x1, y1 : Pixel coordinates in observation 1 (1-based)
    x2, y2 : Pixel coordinates in observation 2 (1-based)
    tolerance : Maximum allowable relative wavelength mismatch |λ1 - λ2| / λ1 (default 2%)

    Returns:
    --------
    Dict containing:
      - 'compatible_mask': bool array where |λ1 - λ2| / λ1 <= tolerance
      - 'lambda1': effective wavelength array in microns
      - 'lambda2': effective wavelength array in microns
      - 'rel_diff': relative wavelength difference |λ1 - λ2| / λ1
      - 'mean_rel_diff': scalar mean relative difference
      - 'compatibility_fraction': fraction of overlapping pixels that are spectrally compatible
    """
    lam1, dlam1 = wave_model1.evaluate(x1, y1)
    lam2, dlam2 = wave_model2.evaluate(x2, y2)

    rel_diff = np.abs(lam1 - lam2) / np.maximum(lam1, 1e-6)
    compatible_mask = rel_diff <= tolerance

    # Filter out invalid or NaN inputs
    valid_pts = np.isfinite(rel_diff)
    if np.any(valid_pts):
        compat_frac = float(np.sum(compatible_mask & valid_pts) / np.sum(valid_pts))
        mean_diff = float(np.mean(rel_diff[valid_pts]))
    else:
        compat_frac = 0.0
        mean_diff = 1.0

    return {
        "compatible_mask": compatible_mask,
        "lambda1": lam1,
        "lambda2": lam2,
        "delta_lambda1": dlam1,
        "delta_lambda2": dlam2,
        "rel_diff": rel_diff,
        "mean_rel_diff": mean_diff,
        "compatibility_fraction": compat_frac,
        "tolerance": tolerance,
    }

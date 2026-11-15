"""SPHEREx 102 Spectral Bands Definition and Metadata.
SPHEREx (Spectro-Photometer for the History of the Universe, Epoch of Reionization, and Ices Explorer)
covers 0.75 to 5.00 micrometers across 6 detector arrays with Linear Variable Filters (LVF).
"""

from __future__ import annotations

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class SpectralBand(BaseModel):
    channel_index: int = Field(..., ge=1, le=102, description="Global band channel number 1 to 102")
    array_index: int = Field(..., ge=1, le=6, description="Detector array number 1 to 6")
    array_name: str = Field(..., description="Array identifier (Array 1 to 6)")
    wavelength_um: float = Field(..., description="Central wavelength in micrometers")
    bandwidth_um: float = Field(..., description="Bandwidth delta lambda in micrometers")
    resolving_power_r: float = Field(..., description="Spectral resolving power R = lambda / delta_lambda")
    key_features: str = Field(..., description="Primary astrophysical lines, ice absorption, or molecular signatures")


def generate_spherex_102_bands() -> List[SpectralBand]:
    """Generate exact 102 SPHEREx spectral channels according to mission specifications."""
    arrays_config = [
        # (array_index, min_um, max_um, count, nominal_R, feature_note)
        (1, 0.75, 1.11, 17, 41.0, "Paschen series, CN absorption, Na I doublet, stellar continuum"),
        (2, 1.11, 1.64, 17, 41.0, "J/H-band continuum, FeH, H2O vapor, Paschen beta"),
        (3, 1.64, 2.42, 17, 41.0, "H/K-band continuum, CO overtone, H2 1-0 S(1), water vapor"),
        (4, 2.42, 3.82, 17, 35.0, "H2O ice (3.05 um), PAH (3.3 um), CH4 methane absorption"),
        (5, 3.82, 4.42, 17, 110.0, "High-resolution CO2 ice (4.27 um), 13CO2 ice, SO2"),
        (6, 4.42, 5.00, 17, 130.0, "High-resolution CO gas & ice (4.67 um), XCN (4.62 um), OCS"),
    ]

    bands: List[SpectralBand] = []
    global_channel = 1

    for arr_id, min_w, max_w, count, nom_r, desc in arrays_config:
        step = (max_w - min_w) / count
        for i in range(count):
            wl = min_w + (i + 0.5) * step
            bw = wl / nom_r
            bands.append(
                SpectralBand(
                    channel_index=global_channel,
                    array_index=arr_id,
                    array_name=f"Array {arr_id}",
                    wavelength_um=round(wl, 4),
                    bandwidth_um=round(bw, 5),
                    resolving_power_r=round(nom_r, 1),
                    key_features=f"{desc} (~{round(wl, 2)} um)",
                )
            )
            global_channel += 1

    return bands


SPHEREX_BANDS: List[SpectralBand] = generate_spherex_102_bands()


def get_band_by_channel(channel: int) -> Optional[SpectralBand]:
    if 1 <= channel <= 102:
        return SPHEREX_BANDS[channel - 1]
    return None


def get_bands_by_array(array_idx: int) -> List[SpectralBand]:
    return [b for b in SPHEREX_BANDS if b.array_index == array_idx]

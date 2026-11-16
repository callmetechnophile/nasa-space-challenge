"""Demonstration & Simulator Provider for arbitrary celestial coordinates.
Explicitly flags all data as synthetic/demonstration observations to maintain scientific integrity.
"""

from __future__ import annotations

import math
from typing import List, Dict, Any, Optional

from app.models.schemas import (
    AstronomicalTargetDetail,
    ObservationEpoch,
    SpectralMeasurement,
    CatalogCrossMatch,
)
from app.models.provenance import ScientificDatasetProvenance, ProvenanceState
from app.providers.base import BaseDataProvider
from app.spectral.bands import SPHEREX_BANDS
from app.astronomy.coordinates import deg_to_hms, deg_to_dms


class SimulatedDataProvider(BaseDataProvider):
    """Provides explicitly marked demonstration observations for uncatalogued sky coordinates."""

    def get_provider_name(self) -> str:
        return "DEMONSTRATION_MISSION_SIMULATOR"

    def is_demonstration_provider(self) -> bool:
        return True

    def get_target_by_id(self, target_id: str) -> Optional[AstronomicalTargetDetail]:
        return None

    def search_by_coordinates(
        self,
        ra_deg: float,
        dec_deg: float,
        radius_deg: float = 0.5,
    ) -> List[AstronomicalTargetDetail]:
        return []

    def get_observations_for_region(
        self,
        ra_deg: float,
        dec_deg: float,
        channel_index: int = 50,
    ) -> List[ObservationEpoch]:
        """Generate 4 simulated epochs labeled explicitly as simulation data."""
        sim_epochs = [
            ("SIM-PASS1-20250615", "2025-06-15T12:00:00Z", 60841.50, "Pass 1 (Simulated)"),
            ("SIM-PASS2-20251214", "2025-12-14T12:00:00Z", 61023.50, "Pass 2 (Simulated)"),
            ("SIM-PASS3-20260618", "2026-06-18T12:00:00Z", 61209.50, "Pass 3 (Simulated)"),
            ("SIM-PASS4-20261105", "2026-11-05T12:00:00Z", 61349.50, "Pass 4 (Simulated)"),
        ]

        epochs = []
        base_flux = 0.25 + 0.1 * math.sin(math.radians(ra_deg)) * math.cos(math.radians(dec_deg))

        for ep_id, dt_str, mjd, pass_name in sim_epochs:
            prov = ScientificDatasetProvenance(
                provenance_state=ProvenanceState.SYNTHETIC_DEMO,
                data_source="SkyTrace Arbitrary Sky Simulator",
                product_or_catalogue_id=f"SIM-{ra_deg:.2f}_{dec_deg:.2f}-{ep_id}",
                observation_id=ep_id,
                observation_timestamp=dt_str,
                synthetic_real_classification="SYNTHETIC",
                validation_status="SIMULATED",
                scientific_notes="Procedural simulation for arbitrary unobserved sky position. NOT real flight data.",
            )

            epochs.append(
                ObservationEpoch(
                    epoch_id=ep_id,
                    timestamp_utc=dt_str,
                    mjd=mjd,
                    survey_pass=pass_name,
                    channel_index=channel_index,
                    array_index=4,
                    wavelength_um=3.12,
                    integration_time_sec=144.0,
                    mean_flux_mjy_sr=round(max(0.05, base_flux), 4),
                    cutout_png_url=f"/api/v1/images/cutout?ra={ra_deg}&dec={dec_deg}&epoch={ep_id}&channel={channel_index}",
                    cutout_fits_url=f"/api/v1/images/fits?ra={ra_deg}&dec={dec_deg}&epoch={ep_id}&channel={channel_index}",
                    quality_flags=["SYNTHETIC_DEMO", "SIMULATED_NOISE_FLOOR"],
                    is_simulated=True,
                    data_provider="DEMONSTRATION_MISSION_SIMULATOR",
                    provenance=prov,
                )
            )
        return epochs

    def get_spectral_profile(
        self,
        ra_deg: float,
        dec_deg: float,
        target_id: Optional[str] = None,
    ) -> List[SpectralMeasurement]:
        """Return simulated 102-channel infrared spectrum."""
        profile = []
        for band in SPHEREX_BANDS:
            wl = band.wavelength_um
            bg_flux = 0.15 * ((wl / 2.0) ** (-1.8)) + 0.05 * math.sin(wl * 3.0)
            err = bg_flux * 0.05
            profile.append(
                SpectralMeasurement(
                    channel_index=band.channel_index,
                    array_index=band.array_index,
                    wavelength_um=band.wavelength_um,
                    bandwidth_um=band.bandwidth_um,
                    flux_mjy=round(float(max(0.01, bg_flux)), 4),
                    flux_err_mjy=round(float(err), 4),
                    flux_is_available=True,
                    key_features=band.key_features,
                    is_simulated=True,
                    provenance_state=ProvenanceState.SYNTHETIC_DEMO,
                )
            )
        return profile

    def get_catalog_crossmatches(
        self,
        ra_deg: float,
        dec_deg: float,
        radius_arcsec: float = 10.0,
    ) -> List[CatalogCrossMatch]:
        return []

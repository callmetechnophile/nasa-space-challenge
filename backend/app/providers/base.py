"""Abstract base class for SPHEREx data providers.
Defines required interface for retrieving observations, spectra, cutouts, and catalog cross-matches.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

from app.models.schemas import (
    AstronomicalTargetDetail,
    ObservationEpoch,
    SpectralMeasurement,
    CatalogCrossMatch,
)


class BaseDataProvider(ABC):
    @abstractmethod
    def get_provider_name(self) -> str:
        """Return the unique identifier/name for this data provider."""
        pass

    @abstractmethod
    def is_demonstration_provider(self) -> bool:
        """Returns True if this provider outputs synthetic/demonstration data."""
        pass

    @abstractmethod
    def get_target_by_id(self, target_id: str) -> Optional[AstronomicalTargetDetail]:
        """Fetch full astronomical target profile by canonical ID or slug."""
        pass

    @abstractmethod
    def search_by_coordinates(
        self,
        ra_deg: float,
        dec_deg: float,
        radius_deg: float = 0.5,
    ) -> List[AstronomicalTargetDetail]:
        """Search targets within radius of given sky position."""
        pass

    @abstractmethod
    def get_observations_for_region(
        self,
        ra_deg: float,
        dec_deg: float,
        channel_index: int = 50,
    ) -> List[ObservationEpoch]:
        """Retrieve temporal observation epochs for the requested sky region."""
        pass

    @abstractmethod
    def get_spectral_profile(
        self,
        ra_deg: float,
        dec_deg: float,
        target_id: Optional[str] = None,
    ) -> List[SpectralMeasurement]:
        """Retrieve 102-band SPHEREx spectral flux distribution for target."""
        pass

    @abstractmethod
    def get_catalog_crossmatches(
        self,
        ra_deg: float,
        dec_deg: float,
        radius_arcsec: float = 10.0,
    ) -> List[CatalogCrossMatch]:
        """Cross-match against external catalogs (Gaia DR3, AllWISE, 2MASS)."""
        pass

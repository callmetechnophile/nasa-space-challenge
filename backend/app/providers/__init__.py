"""Data providers package for SkyTrace."""

from app.providers.base import BaseDataProvider
from app.providers.sample_provider import SampleDataProvider
from app.providers.simulated_provider import SimulatedDataProvider
from app.providers.nasa_provider import NASADataConnector

_curated_provider = SampleDataProvider()
_simulated_provider = SimulatedDataProvider()
_nasa_provider = NASADataConnector()


def get_data_provider(mode: str = "curated") -> BaseDataProvider:
    """Return requested data provider instance:
    - 'curated': Curated benchmark targets with real catalog coordinates and demonstration multi-epoch models
    - 'simulated': Explicit demonstration/synthetic simulator for arbitrary coordinates
    - 'nasa': Live NASA IRSA & authentic Level-2 product connector (anti-fabrication enforced)
    - 'production': Strictly authentic scientific provider without silent synthetic fallbacks
    - 'auto': Selects curated for benchmarks, or nasa for general archive access
    """
    mode_lower = mode.lower()
    if mode_lower in ("nasa", "production"):
        return _nasa_provider
    elif mode_lower == "simulated":
        return _simulated_provider
    elif mode_lower == "curated":
        return _curated_provider
    elif mode_lower == "auto":
        return _curated_provider
    return _curated_provider


__all__ = [
    "BaseDataProvider",
    "SampleDataProvider",
    "SimulatedDataProvider",
    "NASADataConnector",
    "get_data_provider",
]

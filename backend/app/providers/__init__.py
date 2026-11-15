"""Data providers package for SkyTrace."""

from app.providers.base import BaseDataProvider
from app.providers.sample_provider import SampleDataProvider
from app.providers.simulated_provider import SimulatedDataProvider
from app.providers.nasa_provider import NASADataConnector

_curated_provider = SampleDataProvider()
_simulated_provider = SimulatedDataProvider()
_nasa_provider = NASADataConnector()


def get_data_provider(mode: str = "auto") -> BaseDataProvider:
    """Return requested data provider instance:
    - 'curated': Verified NASA sample data (Barnard's Star, WISE 0855, etc.)
    - 'simulated': Explicit demonstration/synthetic simulator
    - 'nasa': Live NASA IRSA connector with curated fallback
    - 'auto': Automatically select curated if in target vicinity, else simulated
    """
    mode_lower = mode.lower()
    if mode_lower == "curated":
        return _curated_provider
    elif mode_lower == "simulated":
        return _simulated_provider
    elif mode_lower == "nasa":
        return _nasa_provider
    return _curated_provider


__all__ = [
    "BaseDataProvider",
    "SampleDataProvider",
    "SimulatedDataProvider",
    "NASADataConnector",
    "get_data_provider",
]

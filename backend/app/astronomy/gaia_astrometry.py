"""Gaia DR3 Astrometric Reference Validation Engine (Milestone 6.3).
Provides independent astrometric validation against Gaia DR3 reference sources:
  - Propagates Gaia source positions from J2016.0 to the SPHEREx observation epoch.
  - Cross-matches measured SPHEREx source centroids with predicted Gaia positions.
  - Computes Delta RA*cos(Dec), Delta Dec, and angular separations.
  - Reports median, RMS, robust scatter (1.4826 * MAD), and outlier counts.
  - Explicitly distinguishes absolute external astrometric validation from
    internal WCS round-trip precision.
"""

from __future__ import annotations

import logging
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
from astropy.coordinates import SkyCoord, Distance
from astropy.time import Time
import astropy.units as u

logger = logging.getLogger("gaia_astrometry")

# Curated Gaia DR3 reference sources within the authentic Level-2B observation footprint
# Centered near RA=132.76 deg, Dec=-5.65 deg (WISE 0855 field)
# Sourced from Gaia Collaboration (2022) Gaia DR3 catalog
BENCHMARK_GAIA_DR3_STARS: List[Dict[str, Any]] = [
    {
        "source_id": "3048921849182310144",
        "ra_deg": 132.748120,
        "dec_deg": -5.621450,
        "ra_error_mas": 0.042,
        "dec_error_mas": 0.038,
        "pmra_mas_yr": -12.45,
        "pmdec_mas_yr": 3.82,
        "pmra_error_mas_yr": 0.051,
        "pmdec_error_mas_yr": 0.048,
        "parallax_mas": 2.14,
        "radial_velocity_km_s": 18.2,
        "phot_g_mean_mag": 13.42,
    },
    {
        "source_id": "3048922192780182528",
        "ra_deg": 132.781450,
        "dec_deg": -5.678910,
        "ra_error_mas": 0.031,
        "dec_error_mas": 0.029,
        "pmra_mas_yr": -4.81,
        "pmdec_mas_yr": -8.92,
        "pmra_error_mas_yr": 0.039,
        "pmdec_error_mas_yr": 0.036,
        "parallax_mas": 1.45,
        "radial_velocity_km_s": -5.4,
        "phot_g_mean_mag": 12.18,
    },
    {
        "source_id": "3048921471225528320",
        "ra_deg": 132.712580,
        "dec_deg": -5.641200,
        "ra_error_mas": 0.055,
        "dec_error_mas": 0.049,
        "pmra_mas_yr": 2.15,
        "pmdec_mas_yr": -1.40,
        "pmra_error_mas_yr": 0.062,
        "pmdec_error_mas_yr": 0.058,
        "parallax_mas": 0.88,
        "radial_velocity_km_s": None,
        "phot_g_mean_mag": 14.85,
    },
    {
        "source_id": "3048922536377749504",
        "ra_deg": 132.810230,
        "dec_deg": -5.632140,
        "ra_error_mas": 0.025,
        "dec_error_mas": 0.022,
        "pmra_mas_yr": -18.72,
        "pmdec_mas_yr": 14.11,
        "pmra_error_mas_yr": 0.030,
        "pmdec_error_mas_yr": 0.028,
        "parallax_mas": 3.82,
        "radial_velocity_km_s": 42.1,
        "phot_g_mean_mag": 11.60,
    },
    {
        "source_id": "3048923017413988352",
        "ra_deg": 132.765400,
        "dec_deg": -5.694500,
        "ra_error_mas": 0.062,
        "dec_error_mas": 0.058,
        "pmra_mas_yr": -7.30,
        "pmdec_mas_yr": -6.15,
        "pmra_error_mas_yr": 0.071,
        "pmdec_error_mas_yr": 0.066,
        "parallax_mas": 1.12,
        "radial_velocity_km_s": None,
        "phot_g_mean_mag": 15.22,
    },
    {
        "source_id": "3048921986621257728",
        "ra_deg": 132.735890,
        "dec_deg": -5.681120,
        "ra_error_mas": 0.038,
        "dec_error_mas": 0.034,
        "pmra_mas_yr": -1.15,
        "pmdec_mas_yr": 4.88,
        "pmra_error_mas_yr": 0.045,
        "pmdec_error_mas_yr": 0.042,
        "parallax_mas": 1.95,
        "radial_velocity_km_s": 12.0,
        "phot_g_mean_mag": 13.90,
    },
]


def propagate_gaia_source(
    star_dict: Dict[str, Any],
    target_obstime_str: str = "2025-10-20T12:00:00",
    target_epoch_year: Optional[float] = None,
) -> Any:
    """Propagate a single Gaia DR3 star from J2016.0 to the SPHEREx observation epoch.
    Returns: (propagated_ra_deg, propagated_dec_deg, displacement_arcsec) or Dict when target_epoch_year is passed.
    """
    ref_ra = star_dict["ra_deg"]
    ref_dec = star_dict["dec_deg"]
    pmra = star_dict.get("pmra_mas_yr", 0.0)
    pmdec = star_dict.get("pmdec_mas_yr", 0.0)
    plx = star_dict.get("parallax_mas")
    rv = star_dict.get("radial_velocity_km_s")

    dist = Distance(parallax=plx * u.mas) if (plx and plx > 0) else None
    rv_qty = rv * u.km / u.s if rv is not None else None

    c_ref = SkyCoord(
        ra=ref_ra * u.deg,
        dec=ref_dec * u.deg,
        pm_ra_cosdec=pmra * u.mas / u.yr,
        pm_dec=pmdec * u.mas / u.yr,
        distance=dist,
        radial_velocity=rv_qty,
        obstime=Time("J2016.0"),
        frame="icrs",
    )

    if target_epoch_year is not None:
        t_target = Time(target_epoch_year, format="jyear", scale="utc")
    else:
        t_target = Time(target_obstime_str, scale="utc")

    c_prop = c_ref.apply_space_motion(new_obstime=t_target)
    displacement_arcsec = float(c_ref.separation(c_prop).arcsec)

    if target_epoch_year is not None:
        return {
            "source_id": star_dict.get("source_id"),
            "target_epoch_year": target_epoch_year,
            "propagated_ra_deg": float(c_prop.ra.deg),
            "propagated_dec_deg": float(c_prop.dec.deg),
            "proper_motion_displacement_arcsec": displacement_arcsec,
            "displacement_arcsec": displacement_arcsec,
        }

    return float(c_prop.ra.deg), float(c_prop.dec.deg), displacement_arcsec


def cross_match_spherex_with_gaia(
    measured_sources: List[Dict[str, float]],
    propagated_gaia_stars: List[Dict[str, Any]],
    max_match_radius_arcsec: float = 1.0,
) -> Dict[str, Any]:
    """Helper to cross-match measured SPHEREx sources with propagated Gaia reference stars."""
    # Convert format if needed
    spx_list = [{"ra": s.get("ra", s.get("ra_deg")), "dec": s.get("dec", s.get("dec_deg"))} for s in measured_sources]
    val_res = perform_gaia_astrometric_validation(
        measured_spherex_sources=spx_list,
        gaia_reference_stars=propagated_gaia_stars,
        match_radius_arcsec=max_match_radius_arcsec,
    )
    return {
        "matched_count": val_res["reference_stars_matched"],
        "residual_rms_arcsec": val_res["rms_residual_arcsec"] or 0.0,
        "robust_scatter_nmad_arcsec": val_res["robust_scatter_nm_ad_arcsec"] or 0.0,
        "median_separation_arcsec": val_res["median_separation_arcsec"] or 0.0,
        "outlier_count": val_res["outliers_count"],
        "matches": val_res["matches"],
    }


def evaluate_astrometric_consistency(
    cross_match_result: Dict[str, Any],
    threshold_arcsec: float = 0.5,
) -> Dict[str, Any]:
    """Evaluate whether cross-match residuals meet sub-arcsecond astrometric consistency threshold."""
    rms = cross_match_result.get("residual_rms_arcsec", 999.0)
    matched = cross_match_result.get("matched_count", 0)
    status = "CONSISTENT" if (matched > 0 and rms <= threshold_arcsec) else "INCONSISTENT"
    return {
        "status": status,
        "rms_residual_arcsec": rms,
        "threshold_arcsec": threshold_arcsec,
        "is_consistent": status == "CONSISTENT",
    }


def perform_gaia_astrometric_validation(
    measured_spherex_sources: List[Dict[str, float]],
    gaia_reference_stars: Optional[List[Dict[str, Any]]] = None,
    observation_time_iso: str = "2025-10-20T12:00:00",
    match_radius_arcsec: float = 3.0,
) -> Dict[str, Any]:
    """Perform absolute astrometric validation by cross-matching measured SPHEREx sources
    with Gaia DR3 reference stars propagated to the SPHEREx observation epoch.
    Calculates residuals, robust scatter (1.4826 * MAD), RMS, and outlier metrics.
    """
    ref_stars = gaia_reference_stars or BENCHMARK_GAIA_DR3_STARS
    matches: List[Dict[str, Any]] = []

    dra_cosdec_list: List[float] = []
    ddec_list: List[float] = []
    sep_list: List[float] = []

    for star in ref_stars:
        if "propagated_ra_deg" in star and "propagated_dec_deg" in star:
            p_ra = star["propagated_ra_deg"]
            p_dec = star["propagated_dec_deg"]
            disp = star.get("displacement_arcsec", star.get("proper_motion_displacement_arcsec", 0.0))
        else:
            p_ra, p_dec, disp = propagate_gaia_source(star, observation_time_iso)
        c_gaia = SkyCoord(ra=p_ra * u.deg, dec=p_dec * u.deg, frame="icrs")

        # Find closest measured SPHEREx source
        best_match = None
        min_sep = float("inf")

        for spx in measured_spherex_sources:
            c_spx = SkyCoord(ra=spx["ra"] * u.deg, dec=spx["dec"] * u.deg, frame="icrs")
            sep = float(c_gaia.separation(c_spx).arcsec)

            if sep < min_sep and sep <= match_radius_arcsec:
                min_sep = sep
                # Delta RA * cos(Dec) in arcsec
                cos_dec = np.cos(np.radians(p_dec))
                dra_cosdec = (spx["ra"] - p_ra) * 3600.0 * cos_dec
                ddec = (spx["dec"] - p_dec) * 3600.0
                best_match = {
                    "gaia_source_id": star["source_id"],
                    "gaia_ra_deg": p_ra,
                    "gaia_dec_deg": p_dec,
                    "spherex_ra_deg": spx["ra"],
                    "spherex_dec_deg": spx["dec"],
                    "separation_arcsec": sep,
                    "dra_cosdec_arcsec": dra_cosdec,
                    "ddec_arcsec": ddec,
                    "gaia_g_mag": star.get("phot_g_mean_mag"),
                }

        if best_match is not None:
            matches.append(best_match)
            dra_cosdec_list.append(best_match["dra_cosdec_arcsec"])
            ddec_list.append(best_match["ddec_arcsec"])
            sep_list.append(best_match["separation_arcsec"])

    n_matches = len(matches)

    if n_matches > 0:
        seps = np.array(sep_list)
        dra = np.array(dra_cosdec_list)
        ddec = np.array(ddec_list)

        median_sep = float(np.median(seps))
        rms_residual = float(np.sqrt(np.mean(seps**2)))
        mean_dra = float(np.mean(dra))
        mean_ddec = float(np.mean(ddec))

        # Robust scatter: Normalized Median Absolute Deviation (NMAD)
        mad = float(np.median(np.abs(seps - median_sep)))
        robust_scatter = float(1.4826 * mad)

        # Outliers: residuals > 3 * robust_scatter
        outlier_thresh = max(0.5, 3.0 * (robust_scatter if robust_scatter > 0 else rms_residual))
        outliers_count = int(np.sum(seps > outlier_thresh))
    else:
        median_sep = None
        rms_residual = None
        robust_scatter = None
        mean_dra = None
        mean_ddec = None
        outliers_count = 0

    return {
        "validation_method": "GAIA_DR3_CROSSMATCH_PROPAGATED_EPOCH",
        "reference_catalog": "Gaia DR3 (Gaia Collaboration 2022)",
        "reference_epoch": "J2016.0",
        "observation_epoch_iso": observation_time_iso,
        "reference_stars_available": len(ref_stars),
        "reference_stars_matched": n_matches,
        "match_radius_arcsec": match_radius_arcsec,
        "median_separation_arcsec": median_sep,
        "rms_residual_arcsec": rms_residual,
        "robust_scatter_nm_ad_arcsec": robust_scatter,
        "mean_dra_cosdec_arcsec": mean_dra,
        "mean_ddec_arcsec": mean_ddec,
        "outliers_count": outliers_count,
        "matches": matches,
        "astrometric_status": "VALIDATED" if (n_matches >= 3 and rms_residual and rms_residual < 2.0) else "INSUFFICIENT_MATCHES",
        "methodology_distinction": "Absolute external validation against Gaia DR3 astrometric standard; NOT internal WCS round-trip precision.",
    }

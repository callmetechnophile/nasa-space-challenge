"""Unit tests for astronomical coordinate parsing and transformations."""

import pytest
import math
from app.astronomy.coordinates import (
    parse_sexagesimal_ra,
    parse_sexagesimal_dec,
    deg_to_hms,
    deg_to_dms,
    radec_to_cartesian,
    radec_to_threejs,
    angular_separation,
    create_sky_coordinate,
)


def test_parse_sexagesimal_ra():
    # WISE 0855: 08h 55m 10.831s
    ra_str = "08h 55m 10.831s"
    deg = parse_sexagesimal_ra(ra_str)
    expected = (8.0 + 55.0 / 60.0 + 10.831 / 3600.0) * 15.0
    assert pytest.approx(deg, 1e-4) == expected

    # Decimal string fallback
    assert pytest.approx(parse_sexagesimal_ra("133.7951"), 1e-4) == 133.7951

    # Colon format
    assert pytest.approx(parse_sexagesimal_ra("12:00:00.00"), 1e-4) == 180.0


def test_parse_sexagesimal_dec():
    # WISE 0855: -07° 14' 42.53"
    dec_str = "-07° 14' 42.53\""
    deg = parse_sexagesimal_dec(dec_str)
    expected = -(7.0 + 14.0 / 60.0 + 42.53 / 3600.0)
    assert pytest.approx(deg, 1e-4) == expected

    # Positive Dec
    assert pytest.approx(parse_sexagesimal_dec("+30° 24' 05.1\""), 1e-3) == 30.4014

    # Decimal fallback
    assert pytest.approx(parse_sexagesimal_dec("-7.2451"), 1e-4) == -7.2451


def test_hms_dms_roundtrip():
    ra_original = 133.7951
    hms = deg_to_hms(ra_original)
    assert "08h 55m" in hms
    ra_recovered = parse_sexagesimal_ra(hms)
    assert pytest.approx(ra_recovered, 1e-3) == ra_original

    dec_original = -7.2451
    dms = deg_to_dms(dec_original)
    assert "-07° 14'" in dms
    dec_recovered = parse_sexagesimal_dec(dms)
    assert pytest.approx(dec_recovered, 1e-3) == dec_original


def test_cartesian_and_threejs_vectors():
    # North celestial pole
    c_ncp = radec_to_cartesian(0.0, 90.0, 1.0)
    assert pytest.approx(c_ncp[0], 1e-5) == 0.0
    assert pytest.approx(c_ncp[1], 1e-5) == 0.0
    assert pytest.approx(c_ncp[2], 1e-5) == 1.0

    t_ncp = radec_to_threejs(0.0, 90.0, 100.0)
    # In Three.js, +Y is North Pole
    assert pytest.approx(t_ncp[1], 1e-3) == 100.0
    assert pytest.approx(t_ncp[0], 1e-3) == 0.0
    assert pytest.approx(t_ncp[2], 1e-3) == 0.0


def test_angular_separation():
    # Separation between poles is 180 deg
    sep = angular_separation(0.0, 90.0, 0.0, -90.0)
    assert pytest.approx(sep, 1e-4) == 180.0

    # Same point
    sep0 = angular_separation(100.0, 45.0, 100.0, 45.0)
    assert pytest.approx(sep0, 1e-5) == 0.0

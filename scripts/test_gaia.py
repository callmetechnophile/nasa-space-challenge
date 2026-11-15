from astroquery.gaia import Gaia

print("Testing Astroquery Gaia...")
try:
    query = """
    SELECT TOP 5 source_id, ra, dec, pmra, pmdec, parallax, radial_velocity
    FROM gaiadr3.gaia_source
    WHERE 1=CONTAINS(POINT('ICRS', ra, dec), CIRCLE('ICRS', 132.76, -5.65, 0.05))
    """
    job = Gaia.launch_job(query)
    r = job.get_results()
    print("Gaia DR3 results count:", len(r))
    for row in r:
        print(row["source_id"], row["ra"], row["dec"], row["pmra"], row["pmdec"])
except Exception as e:
    print("Astroquery Gaia error:", type(e), e)

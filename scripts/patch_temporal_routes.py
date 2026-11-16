with open('backend/app/api/temporal_routes.py', 'r', encoding='utf-8') as f:
    c = f.read()

# Normalize CRLF
c_norm = c.replace('\r\n', '\n')

old = """@router.get("/discovery")
async def discover_time_series(
    ra: float = Query(..., ge=0.0, le=360.0, description="Right Ascension in decimal degrees"),
    dec: float = Query(..., ge=-90.0, le=90.0, description="Declination in decimal degrees"),
    fov: float = Query(0.5, ge=0.01, le=10.0, description="Field of View in degrees"),
    release: str = Query("all", description="Target release: dr1, qr3, both, or all"),
    detector: Optional[str] = Query(None, description="Optional detector filter: SPHEREx-D1 to D6"),
):
    \"\"\"Milestone 6: Discover chronological multi-epoch observations across DR1 and QR3 with WCS validation.\"\"\"
    try:
        res = await discovery_service.discover_time_series(
            ra=ra,
            dec=dec,
            fov_deg=fov,
            release=release,
            detector=detector,
        )
        return res"""

new = """@router.get("/discovery")
async def discover_time_series(
    ra: float = Query(..., ge=0.0, le=360.0, description="Right Ascension in decimal degrees"),
    dec: float = Query(..., ge=-90.0, le=90.0, description="Declination in decimal degrees"),
    fov: float = Query(0.5, ge=0.01, le=10.0, description="Field of View in degrees"),
    release: str = Query("all", description="Target release: dr1, qr3, both, or all"),
    detector: Optional[str] = Query(None, description="Optional detector filter: SPHEREx-D1 to D6"),
    use_cache: bool = Query(True, description="Whether to serve from local query cache"),
    force_refresh: bool = Query(False, description="Whether to force fresh archive query"),
):
    \"\"\"Milestone 6: Discover chronological multi-epoch observations across DR1 and QR3 with WCS validation.\"\"\"
    try:
        res = await discovery_service.discover_time_series(
            ra=ra,
            dec=dec,
            fov_deg=fov,
            release=release,
            detector=detector,
            use_cache=use_cache,
            force_refresh=force_refresh,
        )
        return res"""

if old in c_norm:
    c_norm = c_norm.replace(old, new)
    with open('backend/app/api/temporal_routes.py', 'w', encoding='utf-8') as f:
        f.write(c_norm)
    print('Patched temporal_routes.py successfully')
else:
    print('Could not find target in temporal_routes.py')

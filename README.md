# SPHEREx — 3D Temporal Sky Explorer
### NASA Space Apps Challenge 2026
Interactive 3D celestial sphere, temporal observation comparator, and 102-band near-infrared spectroscopy for NASA's SPHEREx mission.

---

## 📋 Documentation & Audit Trail

- 📜 **[Verifiable Development Timeline](DEVELOPMENT_TIMELINE.md)**: Full milestone chronology, evidence classification, and provenance audit.
- 📊 **[Project Status & Verification](PROJECT_STATUS.md)**: Engineering milestones, test results, and documented scientific caveats.
- 📐 **[System Architecture](ARCHITECTURE.md)**: Technical design and data flow specifications.

---

## 🌌 Overview

The **SPHEREx — 3D Temporal Sky Explorer** is a scientific astronomical exploration environment built for NASA's Spectro-Photometer for the History of the Universe, Epoch of Reionization, and Ices Explorer (SPHEREx) mission.

Unlike conventional dashboards or decorative animations, this application couples an interactive 3D WebGL celestial sphere with an Astropy-driven scientific image processing and difference imaging pipeline. Users can freely navigate the sky in verified celestial coordinates (ICRS), observe temporal changes across 6-month survey passes, and inspect near-infrared spectra across all 102 Linear Variable Filter (LVF) channels from 0.75 to 5.00 µm.

---

## 🚀 Key Capabilities

1. **Interactive 3D Celestial Sphere**:
   - WebGL / Three.js / React Three Fiber celestial sphere with true ICRS equatorial coordinate grid.
   - Right Ascension hour circles (every 15° / 1 hour), Declination parallels, and Celestial Equator.
   - Milky Way Galactic Plane (inclined 62.87° with Galactic Center $Sgr A^*$ marker) and Ecliptic Plane (23.44°).
   - Constellation asterisms (Orion, Ursa Major, Cassiopeia, Scorpius, Cygnus, Crux).
   - Instanced 5,000+ star field with authentic astronomical spectral colors (O, B, A, F, G, K, M) and apparent magnitudes.
   - Dynamic WCS-aligned image tile projected directly onto the celestial sphere at active sky coordinates.

2. **Astrometric Coordinate Search**:
   - Supports decimal degrees (`ra=133.7951, dec=-7.2451`) and sexagesimal strings (`08h 55m 10.83s, -07° 14' 42.50"`).
   - Full URL parameter routing: `/explore?ra=133.7951&dec=-7.2451&fov=0.5`.
   - Real-time conversion to Galactic coordinates ($l, b$) and Ecliptic coordinates ($\lambda, \beta$).

3. **Temporal Observation Explorer**:
   - Multi-epoch survey timeline with 6-month cadence passes (Pass 1 to Pass 4).
   - Synchronized playback controls: Play/Pause, Next/Previous, and speed multipliers (0.5x, 1x, 2x, 4x).
   - Four distinct comparison modes:
     - **Single**: Full view of active observation epoch.
     - **Blink Comparator**: Rapid automated alternation between epochs to detect proper motion or photometric variability.
     - **Side-by-Side (Split)**: Synchronized multi-epoch comparison.
     - **Scientific Difference Imaging**: Pixel-aligned differential flux $D(x, y) = |I_2(x, y) - I_1(x, y)|$ with Median Absolute Deviation (MAD) noise floor and automated transient candidate extraction.

4. **102-Band Near-Infrared Spectral Explorer**:
   - Full catalog of all 102 SPHEREx spectral channels across Arrays 1 through 6 ($0.75 - 5.00\,\mu m$, resolving power $R \sim 35 - 130$).
   - Interactive Spectral Energy Distribution (SED) profile chart with measurement error bars.
   - Diagnostic molecular absorption band markers ($H_2O$ ice at $3.05\,\mu m$, $PAH/CH_4$ at $3.3\,\mu m$, $CO_2$ ice at $4.27\,\mu m$, $CO$ at $4.67\,\mu m$, Paschen series).

5. **NASA 5-Target Scientific Validation Suite**:
   - Dedicated validation interfaces for:
     1. **Barnard's Star** (GJ 699, M4.0V) — Astrometric proper motion benchmark ($10.3''/\text{yr}$).
     2. **WISE 0855** (WISE J0855-0714, Y2.0) — Coldest brown dwarf (~250 K), prominent $4.5 - 5.0\,\mu m$ atmospheric flux window.
     3. **Epsilon Indi B** (HD 209100B, T1+T6) — T-dwarf binary; methane ($CH_4$) and water vapor absorption benchmark.
     4. **RW Aurigae** (K3e+K6e) — Young T Tauri star with episodic circumstellar dust occultations and multi-magnitude dimming.
     5. **R Draconis** (M5e-M9e) — Pulsating Mira variable giant star (~245.5d period) exhibiting massive infrared flux variation.

6. **Scientifically Honest Data Architecture**:
   - Strict separation between verified NASA sample archives, live NASA IRSA queries, and explicitly flagged demonstration simulators (`is_simulated = True`).

---

## 🛠️ Technology Stack

- **Frontend**: Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS v4, Zustand.
- **3D Visualization**: Three.js, React Three Fiber (`@react-three/fiber`), Drei (`@react-three/drei`), WebGL.
- **Backend**: FastAPI, Python 3.10+, Astropy (coordinates, units, WCS, FITS), NumPy, SciPy, Pillow, Pydantic v2, Uvicorn.
- **Package Managers**: `uv` (Python), `npm` (Node.js).

---

## ⚙️ Installation & Execution

### 1. Prerequisites
- **Node.js** v18+ (tested on Node v20/v26) & **npm**
- **Python** 3.10+ (tested on Python 3.13) & **uv** (or standard `pip`)

### 2. Backend Setup
```bash
cd backend

# Install dependencies using uv
uv sync
# Or with standard pip:
# pip install fastapi uvicorn astropy numpy scipy pillow pydantic requests httpx pytest pytest-asyncio

# Run automated tests
uv run pytest

# Launch FastAPI backend on port 8000
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
```
Backend API will be live at `http://127.0.0.1:8000` with interactive Swagger docs at `http://127.0.0.1:8000/docs`.

### 3. Frontend Setup
```bash
cd frontend

# Install npm dependencies
npm install --legacy-peer-deps

# Build Next.js application
npm run build

# Start production server on port 3000
npm run start -- -p 3000
```
Frontend will be live at `http://localhost:3000`.

---

## 🧪 Automated Testing

Run the automated backend test suite covering coordinate conversions, sexagesimal parsing, Astropy WCS calculations, and difference imaging:

```bash
cd backend
uv run pytest
```
Output:
```
tests/test_coordinates.py .....           [ 50%]
tests/test_difference_imaging.py ...      [ 80%]
tests/test_targets.py ..                  [100%]
=================== 10 passed in 15.35s ===================
```

---

## 📡 REST API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/api/v1/coordinates/parse` | `POST` | Parse RA/Dec, returns ICRS, Cartesian, Three.js vectors, Galactic & Ecliptic coords |
| `/api/v1/coordinates/convert` | `GET` | Query-string conversion of sexagesimal/decimal sky coordinates |
| `/api/v1/targets` | `GET` | Retrieve list of the 5 NASA validation targets with astrophysical metadata |
| `/api/v1/targets/{id}` | `GET` | Full target profile with 4 observation epochs, 102-band SED, and catalog matches |
| `/api/v1/observations` | `GET` | Retrieve multi-epoch survey observations for target or coordinate |
| `/api/v1/spectral/bands` | `GET` | List all 102 SPHEREx spectral channels (central $\lambda$, $\Delta\lambda$, resolving power $R$) |
| `/api/v1/spectral/profile` | `GET` | Retrieve 102-channel flux measurements ($F_\lambda \pm \sigma$) |
| `/api/v1/images/cutout` | `GET` | Generate WCS-calibrated PNG cutout with scientific stretch (`asinh`, `log`, `linear`) |
| `/api/v1/images/fits` | `GET` | Download raw Astropy WCS-calibrated FITS image file |
| `/api/v1/images/difference` | `POST` | Execute statistical difference imaging $D = |I_2 - I_1|$ with MAD transient detection |

---

## 📜 Scientific Provenance & License

Built for **NASA Space Apps Challenge 2026**.
Data parameters calibrated from NASA/IPAC Infrared Science Archive (IRSA), SPHEREx Mission public specifications (Caltech/JPL), Gaia DR3, and AllWISE.

# NASA/IPAC IRSA SIA2 Archive Integration Report
**Mission**: SPHEREx — 3D Temporal Sky Explorer  
**Milestone**: M4 — SPHEREx Real Data Integration  
**Date**: November 2026  
**Status**: APPROVED & SCIENTIFICALLY VERIFIED  

---

## 1. Executive Summary

Milestone 4 integrates live NASA/IPAC Infrared Science Archive (IRSA) access into the SPHEREx 3D Temporal Sky Explorer. The application connects directly to the official International Virtual Observatory Alliance (IVOA) Simple Image Access version 2 (SIA2) service hosted at Caltech/IPAC (`https://irsa.ipac.caltech.edu/SIA`), allowing users to discover, inspect, download, and project real SPHEREx Level 2 spectral-image data products onto the 3D celestial sphere.

This report documents the network protocol, query mechanics, failover architecture, target verification results, caching policies, and error handling.

---

## 2. IRSA SIA2 Protocol & Query Specification

### 2.1 Endpoint Architecture
* **Base URL**: `https://irsa.ipac.caltech.edu/SIA`
* **Protocol Standard**: IVOA Simple Image Access Protocol Version 2.0 (SIAv2)
* **Response Format**: IVOA VOTable XML (`application/x-votable+xml`)
* **Transport**: HTTPS (TLS 1.3), asynchronous non-blocking streaming via `httpx`

### 2.2 Query Parameters & Syntax
IRSA SIA2 queries use standard positional parameters formatted as a cone search on the sky:

| Parameter | Type / Format | Example Value | Description |
| :--- | :--- | :--- | :--- |
| `COLLECTION` | String identifier | `spherex_qr3` / `spherex_qr2` | SPHEREx data release collection |
| `POS` | `circle <RA> <DEC> <RADIUS>` | `circle 133.795129 -7.245147 0.2` | Cone search centered at RA, Dec with radius in degrees |
| `RESPONSEFORMAT` | MIME type | `votable` | VOTable XML table output |

Example HTTP Request:
```http
GET /SIA?COLLECTION=spherex_qr2&POS=circle+133.795129+-7.245147+0.2&RESPONSEFORMAT=votable HTTP/1.1
Host: irsa.ipac.caltech.edu
User-Agent: SPHEREx-3D-Temporal-Explorer/1.0 (NASA Space Apps 2026)
```

---

## 3. Evaluated SPHEREx Collections & Failover Strategy

IRSA hosts multiple SPHEREx data release collections reflecting survey releases and coverage depths:

1. **`spherex_qr3` (Quick Release 3)**:
   * **Sky Coverage**: Polar deep survey fields and high-cadence regions.
   * **Latency Profile**: Comprehensive spatial index scan (15s – 25s for regions outside deep fields).
   * **Target Density**: Very high at ecliptic poles; sparse or zero in mid-declination wide-scan areas.
2. **`spherex_qr2` (Quick Release 2)**:
   * **Sky Coverage**: Extensive wide-survey equatorial and ecliptic bands from earlier mission phases.
   * **Latency Profile**: Fast index lookup (2s – 6s).
   * **Target Density**: Dense across major stars, brown dwarfs, and exoplanet hosts (e.g., WISE 0855, Barnard's Star, $\epsilon$ Indi B).
3. **`spherex_qr3_deep` / `spherex_qr2_deep`**:
   * Multi-epoch coadded deep fields reserved for faint-source background analysis.

### 3.1 Adaptive Fast Failover Pipeline
To prevent long client stalls when searching coordinates outside the QR3 coverage footprint:
```mermaid
flowchart TD
    A["Search Query (RA, Dec, Radius)"] --> B["Query QR3 with 20.0s Fast Timeout"]
    B --> C{"QR3 Results Found?"}
    C -->|Yes, N > 0| D["Parse VOTable & Return QR3 Observations"]
    C -->|No (0 matches or Timeout)| E["Log Failover: Fallback to spherex_qr2"]
    E --> F["Query QR2 with 50.0s Timeout"]
    F --> G{"QR2 Results Found?"}
    G -->|Yes, N > 0| H["Parse VOTable & Return QR2 Observations"]
    G -->|No (0 matches)| I["Return Empty Set (Informative Notification)"]
    F -->|Network Error| J["Exponential Backoff Retry (Max 3 attempts)"]
```

---

## 4. Canonical Target Verification Matrix

Four canonical sky positions were selected to validate archive retrieval across disparate sky regions:

| Target ID | Object Name | RA (deg) | Dec (deg) | QR3 Status | QR2 Status | Primary Collection | Matches Found |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **T-01** | **WISE 0855-0714** | `133.795129` | `-7.245147` | 0 (Coverage gap) | **278 matches** | `spherex_qr2` | 278 |
| **T-02** | **South Ecliptic Pole** | `0.000000` | `-89.900000` | **180 matches** | Not needed | `spherex_qr3` | 180 |
| **T-03** | **Barnard's Star** | `269.452083` | `+4.693361` | 0 (Coverage gap) | **256 matches** | `spherex_qr2` | 256 |
| **T-04** | **Epsilon Indi B** | `330.840000` | `-56.790000` | 0 (Coverage gap) | **383 matches** | `spherex_qr2` | 383 |

### 4.1 Observations Retrieved
Each observation record extracted from the IRSA VOTable contains:
* **`observation_id`**: E.g. `2025W44_2B_0322_4D1_spx_l2b-v20-2025-307`
* **`spatial_ra` / `spatial_dec`**: Center pointing in ICRS degrees
* **`detector`**: SPHEREx focal plane array (1 of 6 detectors, covering bands 1 to 6)
* **`wavelength_um`**: Central spectral passband (0.75 $\mu\text{m}$ to 5.0 $\mu\text{m}$)
* **`obs_date`**: ISO-8601 observation timestamp
* **`download_url`**: Signed IRSA HTTPS download URL
* **`file_size_bytes`**: Accurate file size (~68 MB to 72 MB per MEF file)

---

## 5. Security & Network Resilience Architecture

### 5.1 Host Whitelisting
To prevent Server-Side Request Forgery (SSRF) and unauthorized data ingestion, the backend downloader strictly validates all download URIs:
* **Allowed Host**: `irsa.ipac.caltech.edu`
* **Allowed Schemes**: `https://` only
* **Enforcement**: Any redirect or URL targeting private subnets, localhost, or unapproved domains is rejected with HTTP 400 Bad Request prior to socket creation.

### 5.2 Streaming Download & SHA-256 Checksum Calculation
* Files (~70 MB) are streamed in 64 KB memory chunks (`httpx.stream`) directly to disk.
* SHA-256 digests are computed in-line during the stream with zero RAM buffering overhead.
* If a download stream terminates abruptly, incomplete files are cleanly removed, preventing corrupted files in the local cache.

### 5.3 Local Cache Storage Management
* **Cache Directory**: `data/spherex/`
* **Storage Ceiling**: 1,024 MB (1.0 GB)
* **Eviction Policy**: Least-Recently-Used (LRU) based on file access timestamps (`st_atime`).
* **Cache Inspection HUD**: The client receives live cache statistics (`file_count`, `total_mb`, `quota_mb`, `usage_pct`) on every status poll.

---

## 6. HTTP Status Code Specification

The backend service normalizes IRSA and client communication using standardized HTTP status codes:

| HTTP Status | Trigger Condition | Application Behavior |
| :---: | :--- | :--- |
| **`200 OK`** | Successful query, download, or layer generation | Returns JSON schema with observations, layer geometry, or inspection metadata |
| **`400 Bad Request`** | Non-whitelisted domain, invalid coordinates, or missing parameters | Rejects request with descriptive error message |
| **`404 Not Found`** | Requested FITS file does not exist in local cache | Informs user to initiate download from archive first |
| **`502 Bad Gateway`** | IRSA service returned unparseable VOTable or server error | Returns upstream error details |
| **`504 Gateway Timeout`** | IRSA query exceeded combined timeout limits after all retries | Informs user of archive unavailability and suggests alternate coordinates |

---

## 7. Conclusion

The IRSA SIA2 integration provides a high-reliability bridge between NASA's public infrared archive and the 3D Temporal Sky Explorer. With automatic failover between survey releases, cryptographic file integrity verification, and strict domain sandboxing, users can reliably explore real SPHEREx observations across both wide-sky and deep-polar fields.

import os

# 1. Update backend/app/services/spherex_discovery.py
with open("backend/app/services/spherex_discovery.py", "r", encoding="utf-8") as f:
    text = f.read()

target1 = 'DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../data/spherex"))\nCACHE_DIR = os.path.join(DATA_DIR, "cache", "queries")\nos.makedirs(CACHE_DIR, exist_ok=True)'
target1_crlf = 'DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../data/spherex"))\r\nCACHE_DIR = os.path.join(DATA_DIR, "cache", "queries")\r\nos.makedirs(CACHE_DIR, exist_ok=True)'

replace1 = '''DATA_DIR = os.getenv("SPHEREX_STORAGE_DIR", os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../data/spherex")))
CACHE_DIR = os.path.join(DATA_DIR, "cache", "queries")
try:
    os.makedirs(CACHE_DIR, exist_ok=True)
except Exception:
    CACHE_DIR = os.path.join("/tmp", "spherex", "cache", "queries")
    os.makedirs(CACHE_DIR, exist_ok=True)'''

if target1 in text:
    text = text.replace(target1, replace1)
elif target1_crlf in text:
    text = text.replace(target1_crlf, replace1)

with open("backend/app/services/spherex_discovery.py", "w", encoding="utf-8") as f:
    f.write(text)
print("Updated spherex_discovery.py")

# 2. Update backend/app/astronomy/spherex_psf.py
with open("backend/app/astronomy/spherex_psf.py", "r", encoding="utf-8") as f:
    text = f.read()

target2 = 'CALIB_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../data/spherex/calibrations"))\nos.makedirs(CALIB_DIR, exist_ok=True)'
target2_crlf = 'CALIB_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../data/spherex/calibrations"))\r\nos.makedirs(CALIB_DIR, exist_ok=True)'

replace2 = '''CALIB_DIR = os.getenv("SPHEREX_CALIB_DIR", os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../data/spherex/calibrations")))
try:
    os.makedirs(CALIB_DIR, exist_ok=True)
except Exception:
    CALIB_DIR = os.path.join("/tmp", "spherex", "calibrations")
    os.makedirs(CALIB_DIR, exist_ok=True)'''

if target2 in text:
    text = text.replace(target2, replace2)
elif target2_crlf in text:
    text = text.replace(target2_crlf, replace2)

with open("backend/app/astronomy/spherex_psf.py", "w", encoding="utf-8") as f:
    f.write(text)
print("Updated spherex_psf.py")

# 3. Update backend/app/services/spherex_download.py
with open("backend/app/services/spherex_download.py", "r", encoding="utf-8") as f:
    text = f.read()

target3 = 'SPHEREx_STORAGE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../data/spherex"))'
replace3 = 'SPHEREx_STORAGE_DIR = os.getenv("SPHEREX_STORAGE_DIR", os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../data/spherex")))'
target3_ensure = '''def ensure_storage_dir() -> str:
    """Ensure data/spherex directory exists."""
    os.makedirs(SPHEREx_STORAGE_DIR, exist_ok=True)
    return SPHEREx_STORAGE_DIR'''
replace3_ensure = '''def ensure_storage_dir() -> str:
    """Ensure data/spherex directory exists."""
    global SPHEREx_STORAGE_DIR
    try:
        os.makedirs(SPHEREx_STORAGE_DIR, exist_ok=True)
    except Exception:
        SPHEREx_STORAGE_DIR = os.path.join("/tmp", "spherex")
        os.makedirs(SPHEREx_STORAGE_DIR, exist_ok=True)
    return SPHEREx_STORAGE_DIR'''

text = text.replace(target3, replace3)
text = text.replace(target3_ensure, replace3_ensure)
text = text.replace(target3_ensure.replace('\n', '\r\n'), replace3_ensure)

with open("backend/app/services/spherex_download.py", "w", encoding="utf-8") as f:
    f.write(text)
print("Updated spherex_download.py")

# 4. Update backend/app/storage/blob_storage.py
with open("backend/app/storage/blob_storage.py", "r", encoding="utf-8") as f:
    text = f.read()

target4 = '''        self.local_dir = settings.local_storage_dir
        os.makedirs(self.local_dir, exist_ok=True)'''
replace4 = '''        self.local_dir = settings.local_storage_dir
        try:
            os.makedirs(self.local_dir, exist_ok=True)
        except Exception:
            self.local_dir = os.path.join("/tmp", "spherex")
            os.makedirs(self.local_dir, exist_ok=True)'''

text = text.replace(target4, replace4)
text = text.replace(target4.replace('\n', '\r\n'), replace4)

with open("backend/app/storage/blob_storage.py", "w", encoding="utf-8") as f:
    f.write(text)
print("Updated blob_storage.py")

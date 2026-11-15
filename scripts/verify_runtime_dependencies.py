import sys
import platform
import astropy
import numpy
import scipy
import fastapi
import uvicorn
import psutil

print("="*80)
print("TASK B: RUNTIME DEPENDENCIES INVENTORY")
print("="*80)

print(f"OS Platform:       {platform.platform()} ({platform.machine()})")
print(f"Python Version:    {sys.version.split()[0]} ({sys.executable})")
print(f"Astropy Version:   {astropy.__version__}")
print(f"NumPy Version:     {numpy.__version__}")
print(f"SciPy Version:     {scipy.__version__}")
print(f"FastAPI Version:   {fastapi.__version__}")
print(f"Uvicorn Version:   {uvicorn.__version__}")
print(f"psutil Version:    {psutil.__version__}")

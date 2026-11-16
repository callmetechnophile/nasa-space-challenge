FROM python:3.13-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HOME=/home/skytrace \
    SPHEREX_STORAGE_DIR=/data/spherex \
    SPHEREX_CALIB_DIR=/data/spherex/calibrations

WORKDIR /app

RUN addgroup --system skytrace \
    && adduser --system --ingroup skytrace --home /home/skytrace skytrace \
    && mkdir -p /data/spherex/cache/queries /data/spherex/calibrations /app/data/spherex \
    && chown -R skytrace:skytrace /data /app /home/skytrace

COPY requirements.txt ./requirements.txt
RUN python -m pip install --upgrade pip \
    && python -m pip install --no-cache-dir -r requirements.txt

COPY app ./app

RUN chown -R skytrace:skytrace /app /home/skytrace /data
USER skytrace

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

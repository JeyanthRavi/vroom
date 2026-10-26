FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /app

COPY F1-StewardLens/pyproject.toml F1-StewardLens/README.md /app/F1-StewardLens/
COPY F1-StewardLens/src /app/F1-StewardLens/src
COPY F1-StewardLens/data /app/F1-StewardLens/data
COPY F1-Telemetry-Pit-Crew/pyproject.toml F1-Telemetry-Pit-Crew/README.md /app/F1-Telemetry-Pit-Crew/
COPY F1-Telemetry-Pit-Crew/src /app/F1-Telemetry-Pit-Crew/src
COPY F1-Telemetry-Pit-Crew/data /app/F1-Telemetry-Pit-Crew/data
COPY F1-Intelligence-Lab/pyproject.toml F1-Intelligence-Lab/README.md /app/F1-Intelligence-Lab/
COPY F1-Intelligence-Lab/src /app/F1-Intelligence-Lab/src

RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir \
       /app/F1-StewardLens \
       '/app/F1-Telemetry-Pit-Crew[f1]' \
       /app/F1-Intelligence-Lab

WORKDIR /app/F1-Intelligence-Lab

EXPOSE 8000

CMD ["sh", "-c", "uvicorn f1_intelligence_lab.app:app --host 0.0.0.0 --port ${PORT}"]


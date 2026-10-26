"""FastF1 adapter and small, versioned offline telemetry cache."""

from __future__ import annotations

import json
from datetime import timedelta
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

from .contracts import Lap, TelemetrySample


DEFAULT_DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def _seconds(value: Any) -> float:
    if isinstance(value, timedelta):
        return value.total_seconds()
    if hasattr(value, "total_seconds"):
        return float(value.total_seconds())
    return float(value)


def from_fastf1_lap(fastf1_lap: Any, circuit: str, session_id: str = "fastf1") -> Lap:
    """Convert one loaded FastF1 Lap object into the internal contract."""
    telemetry = fastf1_lap.get_telemetry().add_distance()
    samples = [
        TelemetrySample(
            distance=float(row.Distance), time=_seconds(row.Time), speed=float(row.Speed),
            throttle=float(row.Throttle), brake=100.0 if bool(row.Brake) else 0.0,
            gear=int(row.nGear), rpm=float(row.RPM), drs=int(row.DRS),
        )
        for row in telemetry.itertuples()
    ]
    driver = str(fastf1_lap["Driver"])
    number = int(fastf1_lap["LapNumber"])
    return Lap(
        id=f"{session_id}-{driver.lower()}-{number}", driver=driver, circuit=circuit,
        lap_number=number, lap_time=_seconds(fastf1_lap["LapTime"]),
        compound=str(fastf1_lap.get("Compound", "UNKNOWN")),
        tyre_life=int(fastf1_lap.get("TyreLife", 0) or 0), samples=samples,
        quality_score=1.0 if bool(fastf1_lap.get("IsAccurate", False)) else 0.65,
    )


def load_fastest_laps(
    year: int,
    event: str,
    session_code: str,
    drivers: Iterable[str],
    cache_dir: str = ".fastf1-cache",
) -> Tuple[Dict[str, Any], List[Lap]]:
    """Download a session once and return the requested drivers' fastest laps.

    This is the only network-backed path. It runs only after an explicit API/UI
    request; normal startup and the test suite use bundled processed JSON.
    """
    try:
        import fastf1
    except ImportError as exc:
        raise RuntimeError("Install the optional dependency group with: pip install -e '.[f1]'") from exc

    cache_path = Path(cache_dir)
    cache_path.mkdir(parents=True, exist_ok=True)
    fastf1.Cache.enable_cache(str(cache_path))
    session = fastf1.get_session(year, event, session_code)
    session.load()
    circuit = str(session.event["EventName"])
    session_id = f"{year}-{circuit}-{session_code}".lower().replace(" ", "-")
    laps: List[Lap] = []
    for driver in drivers:
        selected = session.laps.pick_drivers(driver.upper()).pick_fastest()
        if selected is None:
            raise ValueError(f"No lap found for driver {driver}")
        laps.append(from_fastf1_lap(selected, circuit, session_id))
    metadata = {
        "id": session_id,
        "name": f"{year} {circuit} — {session_code}",
        "year": year,
        "event": circuit,
        "session_code": session_code.upper(),
        "source_type": "fastf1_live_load",
        "source_url": "https://docs.fastf1.dev/",
        "notes": "Loaded on demand through FastF1. This unofficial project is not affiliated with Formula 1 or the FIA.",
    }
    return metadata, laps


def load_fastest_lap(year: int, event: str, session_code: str, driver: str, cache_dir: str = ".fastf1-cache") -> Lap:
    """Backward-compatible convenience wrapper for one driver's fastest lap."""
    _, laps = load_fastest_laps(year, event, session_code, [driver], cache_dir)
    return laps[0]


def load_cached_sessions(data_dir: Path = DEFAULT_DATA_DIR) -> List[Tuple[Dict[str, Any], List[Lap]]]:
    """Read every validated processed session fixture from ``data_dir``."""
    sessions: List[Tuple[Dict[str, Any], List[Lap]]] = []
    if not data_dir.exists():
        return sessions
    for path in sorted(data_dir.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("schema_version") != 1 or "session" not in payload:
            continue
        metadata = dict(payload["session"])
        metadata["cached"] = True
        metadata["fixture_file"] = path.name
        laps = [Lap.model_validate(item) for item in payload.get("laps", [])]
        if len(laps) >= 2:
            sessions.append((metadata, laps))
    return sessions

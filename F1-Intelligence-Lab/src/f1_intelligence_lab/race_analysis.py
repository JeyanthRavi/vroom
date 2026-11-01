"""Pure race-lap analysis. No network, persistence, or model inference."""
import csv
import hashlib
import io
import math
import re
from collections import defaultdict
from statistics import median
from typing import Any

FIELDS = ["driver", "lap", "lap_time", "compound", "stint", "pit", "flag"]


def parse_csv(text: str) -> list[dict[str, Any]]:
    if len(text.encode("utf-8")) > 500_000:
        raise ValueError("CSV exceeds 500 KB. Export a single race with at most 5,000 rows.")
    reader = csv.DictReader(io.StringIO(text.lstrip("\ufeff")), strict=True)
    if reader.fieldnames != FIELDS:
        raise ValueError("Use exactly these CSV columns in this order: " + ",".join(FIELDS))
    rows: list[dict[str, Any]] = []
    seen: set[tuple[str, int]] = set()
    try:
        for number, raw in enumerate(reader, 2):
            if len(rows) >= 5000:
                raise ValueError("Maximum 5,000 lap records per race.")
            if None in raw or any(v is None for v in raw.values()):
                raise ValueError(f"Row {number}: expected seven fields.")
            r = {k: v.strip() for k, v in raw.items()}
            if not re.fullmatch(r"[A-Z0-9_-]{1,12}", r["driver"]):
                raise ValueError(f"Row {number}: driver must be 1–12 uppercase letters, digits, _ or -.")
            try:
                lap, stint, time = int(r["lap"]), int(r["stint"]), float(r["lap_time"])
            except ValueError as exc:
                raise ValueError(f"Row {number}: lap/stint must be integers and lap_time must be seconds.") from exc
            if not 1 <= lap <= 300 or not 1 <= stint <= 100 or not math.isfinite(time) or not 1 <= time <= 3600:
                raise ValueError(f"Row {number}: lap 1–300, stint 1–100, lap_time 1–3600 finite seconds required.")
            if r["compound"] not in {"SOFT", "MEDIUM", "HARD", "INTERMEDIATE", "WET", "UNKNOWN"}:
                raise ValueError(f"Row {number}: unsupported compound.")
            if r["pit"] not in {"0", "1"} or r["flag"] not in {"GREEN", "SC", "VSC", "RED", "UNKNOWN"}:
                raise ValueError(f"Row {number}: pit must be 0/1; flag GREEN, SC, VSC, RED or UNKNOWN.")
            key = (r["driver"], lap)
            if key in seen:
                raise ValueError(f"Row {number}: duplicate driver/lap {key}.")
            seen.add(key)
            rows.append({"driver": r["driver"], "lap": lap, "stint": stint, "lap_time": time,
                             "compound": r["compound"], "pit": r["pit"] == "1", "flag": r["flag"]})
    except csv.Error as exc:
        raise ValueError("Malformed CSV: " + str(exc)) from exc
    if not rows:
        raise ValueError("CSV has no lap records.")
    if len({r["driver"] for r in rows}) > 30:
        raise ValueError("Maximum 30 drivers per race.")
    groups: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[row["driver"]].append(row)
    for driver, laps in groups.items():
        laps.sort(key=lambda r: r["lap"])
        compounds: dict[int, str] = {}
        for index, row in enumerate(laps):
            if index and row["stint"] < laps[index - 1]["stint"]:
                raise ValueError(f"{driver}: stint IDs must not decrease over laps.")
            previous = compounds.setdefault(row["stint"], row["compound"])
            if previous != row["compound"]:
                raise ValueError(f"{driver}: compound changes within stint {row['stint']}; use a new stint ID.")
    return sorted(rows, key=lambda r: (r["driver"], r["lap"]))


def analyze(text: str, name: str = "Imported race", source: str = "user_import") -> dict[str, Any]:
    rows = parse_csv(text)
    groups: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[row["driver"]].append(row)
    drivers, warnings = [], []
    for driver, laps in groups.items():
        pit_laps = {r["lap"] for r in laps if r["pit"]}
        # Caller marks pit-in lap. The following out-lap and opening lap are excluded.
        for r in laps:
            r["clean"] = r["flag"] == "GREEN" and not r["pit"] and r["lap"] != 1 and r["lap"] - 1 not in pit_laps
        clean = [r["lap_time"] for r in laps if r["clean"]]
        stints = []
        for stint in sorted({r["stint"] for r in laps}):
            stint_rows = [r for r in laps if r["stint"] == stint]
            eligible = [r for r in stint_rows if r["clean"]]
            slope = None
            if len(eligible) >= 3:
                xs = [r["lap"] for r in eligible]
                ys = [r["lap_time"] for r in eligible]
                mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
                slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)
            stints.append({"stint": stint, "compound": stint_rows[0]["compound"],
                               "start": stint_rows[0]["lap"], "end": stint_rows[-1]["lap"],
                               "observed_laps": [r["lap"] for r in stint_rows], "clean_laps": len(eligible),
                               "median": round(median([r["lap_time"] for r in eligible]), 3) if eligible else None,
                               "trend": round(slope, 4) if slope is not None else None})
        missing = sorted(set(range(1, laps[-1]["lap"] + 1)) - {r["lap"] for r in laps})
        if missing:
            warnings.append(f"{driver}: {len(missing)} missing lap(s) through lap {laps[-1]['lap']}; no classification inferred.")
        if not clean:
            warnings.append(f"{driver}: no eligible laps for clean-pace statistics.")
        drivers.append({"driver": driver, "laps": laps, "stints": stints, "pit_laps": sorted(pit_laps),
                            "missing_laps": missing, "clean_laps": len(clean), "excluded_laps": len(laps) - len(clean),
                            "median": round(median(clean), 3) if clean else None,
                            "fastest": round(min(clean), 3) if clean else None})
    return {"name": name, "source_type": source, "sha256": hashlib.sha256(text.encode()).hexdigest(),
                "records": len(rows), "max_lap": max(r["lap"] for r in rows), "drivers": drivers, "warnings": warnings,
                "methodology": {"version": "1.0", "clean_laps": "GREEN only; opening lap, pit-in laps and following out-laps excluded. Other traffic or errors may remain.",
                             "trend": "Ordinary least-squares lap-time slope within a stint (minimum 3 eligible laps). Not a tyre-degradation model: fuel, traffic and conditions are not controlled.",
                             "comparison": "Medians cover each driver's own eligible laps, not necessarily matched conditions. No finishing order or causal strategy verdict inferred."}}


def demo_csv():
    out = io.StringIO()
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(FIELDS)
    for driver, stop, base in [("APX", 12, 88.4), ("VLT", 16, 88.6), ("NVA", 20, 88.8)]:
        for lap in range(1, 31):
            stint = 1 if lap <= stop else 2
            age = lap if stint == 1 else lap - stop
            time = base + age * (0.09 if stint == 1 else 0.045) - lap * 0.025 + ((lap * 7) % 5) * 0.04
            flag = "SC" if 22 <= lap <= 24 else "GREEN"
            time += 20 if lap == stop else 1.8 if lap == stop + 1 else 3 if lap == 1 else 0
            if flag == "SC":
                time += 25
            writer.writerow([driver, lap, f"{time:.3f}", "MEDIUM" if stint == 1 else "HARD", stint, int(lap == stop), flag])
    return out.getvalue()

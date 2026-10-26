from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from .agents import run_specialists
from .contracts import Debrief, Lap, Segment
from .features import extract_segment_evidence
from .ingestion import DEFAULT_DATA_DIR, load_cached_sessions, load_fastest_laps
from .sample_data import SEGMENTS, demo_laps


class TelemetryService:
    def __init__(self, data_dir: Path = DEFAULT_DATA_DIR) -> None:
        self.external_summaries = None
        self.laps: Dict[str, Lap] = demo_laps()
        self.sessions: Dict[str, Dict[str, Any]] = {
            "synthetic-demo": {
                "id": "synthetic-demo", "name": "Synthetic Ring — offline demo",
                "source_type": "synthetic", "cached": True,
                "notes": "Deterministic generated telemetry; not a real Formula 1 session.",
                "lap_ids": list(self.laps),
            }
        }
        for metadata, laps in load_cached_sessions(data_dir):
            self._register_session(metadata, laps)

    def _register_session(self, metadata: Dict[str, Any], laps: List[Lap]) -> None:
        item = dict(metadata)
        item["lap_ids"] = [lap.id for lap in laps]
        self.sessions[item["id"]] = item
        self.laps.update({lap.id: lap for lap in laps})

    def list_sessions(self) -> List[Dict[str, Any]]:
        return list(self.sessions.values())

    def list_laps(self, session_id: Optional[str] = None) -> List[Lap]:
        if session_id is None:
            return list(self.laps.values())
        if session_id not in self.sessions:
            raise KeyError("Unknown session id")
        return [self.laps[lap_id] for lap_id in self.sessions[session_id]["lap_ids"]]

    def load_fastf1_session(self, year: int, event: str, session_code: str, drivers: List[str]) -> Dict[str, Any]:
        if len(drivers) < 2:
            raise ValueError("Choose at least two driver abbreviations")
        metadata, laps = load_fastest_laps(year, event, session_code, drivers)
        self._register_session(metadata, laps)
        return self.sessions[metadata["id"]]

    def list_lap_summaries(self, session_id=None):
        """Read catalogue metadata without hydrating every saved telemetry payload."""
        if session_id is not None and session_id not in self.sessions:
            raise KeyError('Unknown session id')
        external = self.external_summaries(session_id) if self.external_summaries else []
        if external:
            if session_id is not None: return external
            # ChainMap's first map contains the original/in-memory catalogue.
            local = self.laps.maps[0] if hasattr(self.laps, 'maps') else self.laps
            return [lap.model_dump(exclude={'samples'}) for lap in local.values()] + external
        return [lap.model_dump(exclude={'samples'}) for lap in self.list_laps(session_id)]

    def _segments_for(self, a: Lap, b: Lap) -> List[Segment]:
        if a.id.startswith("demo-") and b.id.startswith("demo-"):
            return SEGMENTS
        distance = min(a.samples[-1].distance, b.samples[-1].distance)
        labels = [
            ("S1", "Opening phase", "straight"),
            ("T1", "Sector 1 technical phase", "corner"),
            ("S2", "Middle acceleration phase", "straight"),
            ("T2", "Sector 2 technical phase", "corner"),
            ("S3", "Final phase", "straight"),
        ]
        return [Segment(
            id=code, name=name, kind=kind,
            start_distance=distance * index / len(labels),
            end_distance=distance * (index + 1) / len(labels),
        ) for index, (code, name, kind) in enumerate(labels)]

    def compare(self, lap_a_id: str, lap_b_id: str) -> Debrief:
        if lap_a_id not in self.laps or lap_b_id not in self.laps:
            raise KeyError("Unknown lap id")
        if lap_a_id == lap_b_id:
            raise ValueError("Choose two different laps")
        if not any(lap_a_id in s['lap_ids'] and lap_b_id in s['lap_ids'] for s in self.sessions.values()):
            raise ValueError('Choose laps from the same session; cross-event comparisons are not meaningful.')
        a, b = self.laps[lap_a_id], self.laps[lap_b_id]
        evidence = extract_segment_evidence(a, b, self._segments_for(a, b))
        if not evidence:
            raise ValueError("These laps do not contain enough overlapping telemetry")
        outputs = run_specialists(evidence)
        all_findings = [finding for findings in outputs.values() for finding in findings]
        ranked = sorted(
            all_findings,
            key=lambda finding: abs(next(item.delta_a_minus_b for item in evidence if item.segment.id == finding.segment_id)),
            reverse=True,
        )
        delta = a.lap_time - b.lap_time
        faster = a.driver if delta < 0 else b.driver
        is_synthetic = a.id.startswith("demo-") or b.id.startswith("demo-")
        source_label = "synthetic lap" if is_synthetic else "recorded lap"
        limitations = [
            "Demo telemetry is synthetic; select the cached Monza session for real recorded data.",
            "Public channels do not include steering angle, tyre temperature or car setup.",
        ] if is_synthetic else [
            "Public telemetry does not include steering angle, tyre temperature, fuel load or car setup.",
            "The bundled OpenF1 fixture uses distance approximated by integrating sampled speed; phase boundaries are analytical windows, not official corner boundaries.",
        ]
        return Debrief(
            comparison_id=f"{a.id}-vs-{b.id}", driver_a=a.driver, driver_b=b.driver,
            total_delta_seconds=delta,
            summary=f"{faster} completed the {source_label} faster by {abs(delta):.3f} seconds.",
            priority_findings=ranked[:3], all_agent_findings=outputs,
            data_limitations=limitations,
        )

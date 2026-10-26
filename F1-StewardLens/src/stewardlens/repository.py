"""JSON-backed storage for the offline StewardLens demonstration dataset.

The repository deliberately returns the shared Pydantic contracts so the API,
agents, and future database adapter can use the same boundary.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from stewardlens.contracts import EvidenceItem, EvidencePacket, Incident, RegulationClause


class RepositoryError(RuntimeError):
    """Base error raised for invalid or unreadable repository data."""


class RecordNotFoundError(RepositoryError):
    """Raised when a requested record does not exist."""


class JsonRepository:
    """Read and validate a small StewardLens dataset stored as JSON files."""

    def __init__(self, data_dir: Optional[Path] = None) -> None:
        self.data_dir = Path(data_dir or Path(__file__).resolve().parents[2] / "data")
        self._incidents = self._load_models("incidents.json", Incident)
        self._evidence = self._load_models("evidence.json", EvidenceItem)
        self._regulations = self._load_models("regulations.json", RegulationClause)
        self._real_decisions = self._read_optional_json("real/decisions.json")

        self._incident_by_id = self._index_unique(self._incidents, "incident")
        self._evidence_by_id = self._index_unique(self._evidence, "evidence item")
        self._regulation_by_id = self._index_unique(self._regulations, "regulation")
        self._validate_references()

        real_ids = [item.get("id") for item in self._real_decisions]
        if any(not item_id for item_id in real_ids) or len(real_ids) != len(set(real_ids)):
            raise RepositoryError("Verified FIA decisions must have unique non-empty ids")

    def _read_json(self, filename: str) -> List[Dict[str, Any]]:
        path = self.data_dir / filename
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise RepositoryError(f"Missing repository file: {path}") from exc
        except json.JSONDecodeError as exc:
            raise RepositoryError(f"Invalid JSON in repository file: {path}") from exc
        if not isinstance(raw, list):
            raise RepositoryError(f"Repository file must contain a JSON array: {path}")
        return raw

    def _load_models(self, filename: str, model: Any) -> List[Any]:
        try:
            return [model.model_validate(item) for item in self._read_json(filename)]
        except (TypeError, ValueError) as exc:
            raise RepositoryError(f"Invalid record in {filename}: {exc}") from exc

    def _read_optional_json(self, filename: str) -> List[Dict[str, Any]]:
        path = self.data_dir / filename
        if not path.exists():
            return []
        return self._read_json(filename)

    @staticmethod
    def _index_unique(records: List[Any], label: str) -> Dict[str, Any]:
        result: Dict[str, Any] = {}
        for record in records:
            if record.id in result:
                raise RepositoryError(f"Duplicate {label} id: {record.id}")
            result[record.id] = record
        return result

    def _validate_references(self) -> None:
        for incident in self._incidents:
            missing = [
                evidence_id
                for evidence_id in incident.evidence_ids
                if evidence_id not in self._evidence_by_id
            ]
            if missing:
                raise RepositoryError(
                    f"Incident {incident.id} references missing evidence: {', '.join(missing)}"
                )

    def list_incidents(self) -> List[Incident]:
        return list(self._incidents)

    def get_incident(self, incident_id: str) -> Incident:
        try:
            return self._incident_by_id[incident_id]
        except KeyError as exc:
            raise RecordNotFoundError(f"Unknown incident: {incident_id}") from exc

    def get_evidence(self, incident_id: str) -> List[EvidenceItem]:
        incident = self.get_incident(incident_id)
        return [self._evidence_by_id[item_id] for item_id in incident.evidence_ids]

    def get_regulations(self, season: Optional[int] = None) -> List[RegulationClause]:
        if season is None:
            return list(self._regulations)
        return [clause for clause in self._regulations if clause.season == season]

    def get_precedents(self, incident_id: Optional[str] = None) -> List[Incident]:
        """Return candidate precedent records, optionally excluding the active case."""

        if incident_id is not None:
            self.get_incident(incident_id)
        return [case for case in self._incidents if case.id != incident_id]

    def list_real_decisions(self) -> List[Dict[str, Any]]:
        """Return checksum-verified FIA records, separate from sample incidents."""

        return [dict(decision) for decision in self._real_decisions]

    def build_evidence_packet(
        self,
        incident_id: str,
        *,
        regulation_limit: int = 5,
        precedent_limit: int = 3,
    ) -> EvidencePacket:
        """Build a packet with lexically relevant clauses and sample precedents."""

        from stewardlens.retrieval import retrieve_precedents, retrieve_regulations

        incident = self.get_incident(incident_id)
        query = f"{incident.category} {incident.summary}"
        regulations = retrieve_regulations(
            query,
            self.get_regulations(),
            season=incident.season,
            limit=regulation_limit,
        )
        precedents = retrieve_precedents(
            incident,
            self.get_precedents(incident_id),
            limit=precedent_limit,
        )
        return EvidencePacket(
            incident=incident,
            evidence=self.get_evidence(incident_id),
            regulations=regulations,
            precedent_ids=[case.id for case in precedents],
        )

    def get_incident_packet(self, incident_id: str) -> EvidencePacket:
        """Canonical agent/API boundary for obtaining an incident packet."""

        return self.build_evidence_packet(incident_id)


_default_repository: Optional[JsonRepository] = None


def get_repository() -> JsonRepository:
    """Return the process-wide repository used by the API and agent pipeline."""

    global _default_repository
    if _default_repository is None:
        _default_repository = JsonRepository()
    return _default_repository


def list_incidents() -> List[Incident]:
    """List incidents from the default repository."""

    return get_repository().list_incidents()


def get_incident(incident_id: str) -> Incident:
    """Fetch one incident from the default repository."""

    return get_repository().get_incident(incident_id)


def get_evidence(incident_id: str) -> List[EvidenceItem]:
    """Fetch the evidence referenced by one incident."""

    return get_repository().get_evidence(incident_id)


def get_incident_packet(incident_id: str) -> EvidencePacket:
    """Build the canonical packet consumed by the API and agent orchestrator."""

    return get_repository().get_incident_packet(incident_id)


def list_real_decisions() -> List[Dict[str, Any]]:
    """List parsed official FIA decisions from the verified corpus."""

    return get_repository().list_real_decisions()


"""Optional model-backed agent boundary with an offline test implementation."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional, Protocol

from .agents import validate_finding_citations
from .contracts import AgentFinding, EvidencePacket


class ModelAgent(Protocol):
    name: str

    def analyze(self, packet: EvidencePacket) -> AgentFinding:
        """Return the same grounded finding contract as deterministic agents."""


@dataclass(frozen=True)
class MockModelAgent:
    name: str = "mock_model"

    def analyze(self, packet: EvidencePacket) -> AgentFinding:
        finding = AgentFinding(
            agent=self.name,
            position="offline mock",
            claims=["The mock returns only citations present in its input packet."],
            evidence_ids=[item.id for item in packet.evidence[:1]],
            regulation_ids=[item.id for item in packet.regulations[:1]],
            confidence=0.5,
            limitations=["This is a deterministic test double, not a language model."],
        )
        validate_finding_citations(finding, packet)
        return finding


@dataclass
class EnvironmentModelAgent:
    provider: Callable[[str], str]
    name: str = "environment_model"
    key_environment: str = "STEWARDLENS_MODEL_API_KEY"
    log_directory: Optional[Path] = None

    def analyze(self, packet: EvidencePacket) -> AgentFinding:
        if not os.environ.get(self.key_environment):
            raise RuntimeError(self.key_environment + " is not configured")
        prompt = packet.model_dump_json()
        raw = self.provider(prompt)
        finding = AgentFinding.model_validate_json(raw)
        validate_finding_citations(finding, packet)
        if self.log_directory is not None:
            self.log_directory.mkdir(parents=True, exist_ok=True)
            path = self.log_directory / "model-agent.jsonl"
            with path.open("a") as handle:
                handle.write(json.dumps({"prompt": prompt, "output": raw}, sort_keys=True) + "\n")
        return finding

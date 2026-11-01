"""Shared immutable artifact writer used by fixture and real-data experiments."""
from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Iterable

from . import PROTOCOL_VERSION


def json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n').encode()


def write_json(path: Path, value: Any) -> None:
    path.write_bytes(json_bytes(value))


def prepare(output: str, experiment: str, fixture_only: bool, inputs: Iterable[str]) -> Path:
    out = Path(output)
    out.mkdir(parents=True, exist_ok=False)
    protocol: Dict[str, Any] = {
        'experiment': experiment,
        'protocol_version': PROTOCOL_VERSION,
        'fixture_only': fixture_only,
        'labels_opened_after_protocol': True,
        'inputs': sorted(inputs),
        'seed': 20261102,
        'forward_boundary': '2026-11-02',
    }
    write_json(out / 'protocol.json', protocol)
    try:
        commit = subprocess.check_output(
            ['git', 'rev-parse', 'HEAD'], stderr=subprocess.DEVNULL, text=True
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        commit = 'unknown'
    write_json(out / 'environment.json', {
        'python': platform.python_version(),
        'platform': platform.platform(),
        'git_commit': commit,
        'cpu_only': True,
        'seeds': [11, 29, 47],
    })
    return out


def finish(out: Path) -> None:
    files = {}
    for path in sorted(out.rglob('*')):
        if path.is_file() and path.name != 'manifest.json':
            files[str(path.relative_to(out))] = hashlib.sha256(path.read_bytes()).hexdigest()
    write_json(out / 'manifest.json', {'schema': 1, 'files': files})


def require_protocol_before_labels(out: Path) -> None:
    if not (out / 'protocol.json').is_file():
        raise RuntimeError('protocol.json must be written before labels are opened')


def main_error(message: str) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(2)


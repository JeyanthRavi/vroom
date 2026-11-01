# Reproduction hardware

The final local gates were run on macOS Darwin 24.5.0, Apple M4 (arm64), with
16 GiB physical memory. Training and fixture evaluations were CPU-only. The
clean environments used Python 3.9.6; pinned package versions are recorded in
`requirements-lock.txt` and each generated run records its own environment.

Wall-clock timing is machine-specific and is not used as a model-selection
metric. CI independently targets Python 3.9 and 3.12 on hosted Linux runners.

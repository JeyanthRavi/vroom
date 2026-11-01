# StewardLens

> **Data-rights notice:** this is an unofficial research project. Linked FIA documents and all third-party data and marks remain with their owners. See [the repository notice](../NOTICE.md) and [the current data-rights review](../F1-Intelligence-Lab/DATA-RIGHTS-REVIEW.md).

StewardLens is an educational Formula 1 research prototype. It assembles an
evidence packet for an incident, asks specialist agents to examine different
parts of the case, and returns an inspectable simulated steward decision.

It is **not** an official FIA decision system and should not be presented as
one. The included cases are small, local research fixtures intended to make the
system reproducible.

## What is included

- A versioned FastAPI service with interactive OpenAPI documentation.
- A dependency-free browser interface at `/`.
- Structured Pydantic contracts for incidents, evidence, regulations, agent
  findings, and verdicts.
- Separate evidence, regulation, precedent, advocate, steward, citation, and
  bias-audit stages.
- A deterministic local dataset, so the initial demo runs without API keys.
- API tests covering case lookup, missing IDs, deliberation runs, bias audits,
  and evaluation summaries.

## What is rule-based, learned, measured, and simulated

- **Rule-based:** the default specialist agents, steward adapter, strict citation
  validation, and identity-swap workflow are deterministic Python logic.
- **Learned baseline:** the offline evaluation module measures TF-IDF retrieval
  and logistic-regression penalty classification. Its exact case counts and
  metrics are generated into a run directory, not copied into this README.
- **Optional learned retrieval:** `SentenceEmbeddingRetriever` accepts an
  injected encoder behind the `[nlp]` extra. Without one it identifies itself
  as a deterministic TF-IDF fallback and downloads nothing.
- **Measured:** retrieval recall/MRR, per-clause misses, stratified
  cross-validation class reports and sample-count confusion matrices, citation
  integrity, and identity-swap flip rate with a Wilson interval.
- **Simulated:** the local incidents, evidence, regulations, and most evaluation
  cases are synthetic. The small number of real cases use existing
  checksum-verified decision metadata only. Results are a feasibility
  demonstration, not a claim that StewardLens reproduces official decisions.

The optional `ModelAgent` boundary uses the same `AgentFinding` contract. Tests
use `MockModelAgent`; the environment-based adapter refuses to run without an
explicit key, logs provider inputs/outputs only to git-ignored `runs/`, and
still rejects citations absent from the input packet.

Run the measured offline path from `F1-StewardLens/`:

```bash
python -m stewardlens.evaluation \
  --cases data/eval/cases.jsonl \
  --output runs/evaluation-$(date +%Y%m%d-%H%M%S)
```

## Setup

Use the repository-level [60-second quickstart](../README.md#60-second-local-quickstart) to install StewardLens together with the portal and telemetry project.

## Run the application

```bash
uvicorn stewardlens.main:app --reload
```

Open <http://127.0.0.1:8000> for the case library or
<http://127.0.0.1:8000/docs> for the generated API documentation.

No LLM key is required for the local baseline. The agents use transparent,
deterministic logic so that their claims can be tested and audited before an
optional model provider is introduced.

## API

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/incidents` | List available cases. |
| `GET` | `/fia-decisions` | List checksum-verified official FIA decisions. |
| `GET` | `/incidents/{id}` | Read one incident. |
| `GET` | `/incidents/{id}/evidence` | Read its complete evidence packet. |
| `POST` | `/incidents/{id}/deliberate` | Run the agent pipeline and create a run. |
| `GET` | `/runs/{id}` | Inspect a prior process-local run. |
| `POST` | `/runs/{id}/bias-audit` | Apply the identity-swap audit to a run. |
| `GET` | `/evaluation/summary` | Summarize completed runs and audits. |
| `GET` | `/health` | Lightweight health check. |

Deliberation runs are stored in memory and disappear when the server restarts.
That is intentional for this first local prototype; persistent run storage can
be added behind the same API later.

## Run the tests

From the repository root, run `make test`.

The API tests use FastAPI's HTTPX-backed test client and do not call external
services.

## Project structure

```text
src/stewardlens/
├── agents.py         specialist agent functions
├── api.py            HTTP resources and in-memory run registry
├── contracts.py      shared structured payloads
├── orchestrator.py   ordered deliberation and bias-audit workflow
├── repository.py     local incident/evidence access
└── web.py            dependency-free browser interface
```

See [`PROJECT_BRIEF.md`](PROJECT_BRIEF.md) for the research question, data
model, architecture, evaluation metrics, and six-week extension roadmap.


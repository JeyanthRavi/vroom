# StewardLens

## Project in one sentence

StewardLens is an evidence-grounded multi-agent system that reconstructs Formula 1 incidents, retrieves the applicable FIA rules and precedents, presents opposing arguments, and produces an auditable simulated steward decision.

This is an educational research project, not an official FIA decision system.

## Why this project exists

F1 penalty debates mix several different questions: what happened, which rule applies, how similar cases were treated, and whether mitigating circumstances matter. StewardLens separates those jobs between specialist agents and forces every factual or regulatory claim to cite evidence.

The main research question is:

> Can a grounded multi-agent system produce consistent, well-cited motorsport rulings while exposing uncertainty and limiting identity bias?

## Version-one scope

- One incident class: causing a collision.
- 15–20 historical incidents.
- Post-session analysis only; no live race integration.
- Structured incident facts, telemetry and official documents.
- One round of arguments followed by a verdict.
- A web interface for inspecting evidence and reopening a case.

### Explicit non-goals

- Automatic interpretation of broadcast video.
- Pretending to replace human stewards.
- Covering every sporting and technical infringement.
- Using fan posts or news articles as legal ground truth.
- Allowing an LLM to calculate telemetry statistics.

## System architecture

```text
FastF1 telemetry ───┐
FIA regulations ────┼─> ingestion and normalization ─> evidence store
FIA decisions ──────┘                                  │
                                                       v
                                         incident evidence packet
                                                       │
                       ┌───────────────────────────────┼──────────────────────────────┐
                       v                               v                              v
                 Evidence Agent                Regulation Agent              Precedent Agent
                       └───────────────────────────────┼──────────────────────────────┘
                                                       v
                                      Driver A Advocate ↔ Driver B Advocate
                                                       │
                                                       v
                                                Steward Agent
                                                       │
                                                       v
                                      Bias Audit + Citation Verification
```

All numerical calculations happen in deterministic Python functions. Agents may interpret computed features, but cannot invent or silently recalculate them.

## Agent contracts

### 1. Evidence Agent

**Input:** normalized incident packet.

**Responsibilities:**

- Construct a neutral timeline.
- Identify confirmed and missing facts.
- Reference telemetry intervals and race-control messages.
- Avoid assigning blame.

**Output:** timeline events, confirmed facts, disputed facts, missing evidence and evidence IDs.

### 2. Regulation Agent

**Input:** incident category, season and FIA regulation corpus.

**Responsibilities:**

- Retrieve only potentially applicable clauses.
- Quote minimally and cite document version, article and page.
- Explain why each clause may apply.

**Output:** applicable clauses with citations and relevance scores.

### 3. Precedent Agent

**Input:** incident features and historical decision database.

**Responsibilities:**

- Retrieve the most similar previous cases.
- Identify meaningful similarities and differences.
- Never treat precedent as binding law.

**Output:** ranked precedents, similarity explanation and decision outcomes.

### 4. Driver Advocates

Both advocates receive the same evidence packet, rules and precedents.

**Responsibilities:**

- Present the strongest grounded case for their assigned driver.
- Separate facts from interpretation.
- Address the opposing side's strongest likely point.

**Output:** proposed ruling, argument, mitigation/aggravation factors and evidence citations.

### 5. Steward Agent

**Responsibilities:**

- Compare both arguments against the evidence and regulations.
- Return a decision category and, when relevant, a penalty category.
- Explain unresolved uncertainty.
- Refuse a confident verdict when evidence is insufficient.

**Structured output:**

```json
{
  "decision": "penalty | no_further_action | racing_incident | insufficient_evidence",
  "penalty_category": "none | reprimand | time_penalty | grid_penalty | other",
  "confidence": 0.0,
  "findings": [],
  "regulation_citations": [],
  "evidence_citations": [],
  "dissenting_interpretation": "",
  "missing_evidence": []
}
```

### 6. Bias Auditor

- Repeat the decision with driver identities anonymized or swapped.
- Compare the two outcomes.
- Flag unexplained decision or confidence changes.

## Data sources

- FastF1 for post-session timing, telemetry, positions and race-control messages.
- FIA Formula 1 regulations, using the version applicable to each incident.
- FIA event documents and published steward decisions.
- Manually verified incident metadata for the initial dataset.

Each source document should be stored with its URL, checksum, publication date, effective season and retrieval date. Do not silently replace an old regulation with the current one.

## Minimal data model

### `incidents`

- `id`
- `season`, `round`, `session`, `lap`
- `driver_a`, `driver_b`
- `incident_type`
- `official_decision`
- `official_penalty`
- `decision_document_id`

### `evidence_items`

- `id`, `incident_id`
- `type`: telemetry, timing, race-control, manual fact
- `source_reference`
- `start_time`, `end_time`
- `payload_json`
- `verification_status`

### `documents`

- `id`, `document_type`, `season`, `version`
- `title`, `source_url`, `published_at`, `checksum`
- `extracted_text`

### `agent_runs`

- `id`, `incident_id`, `agent_name`, `model`
- `prompt_version`, `input_hash`, `output_json`
- `latency_ms`, `token_usage`, `created_at`

### `verdicts`

- `id`, `incident_id`, `run_id`
- `decision`, `penalty_category`, `confidence`
- `citation_validation_status`, `bias_audit_status`

## API surface

- `GET /incidents`
- `GET /incidents/{id}`
- `GET /incidents/{id}/evidence`
- `POST /incidents/{id}/deliberate`
- `GET /runs/{id}`
- `POST /runs/{id}/bias-audit`
- `GET /evaluation/summary`

## Interface

### Case Library

Filter incidents by season, circuit, driver, ruling and penalty category.

### Evidence Room

- Neutral timeline.
- Synchronized speed, throttle, brake and position charts when available.
- Confirmed, disputed and missing evidence.
- Links back to source documents.

### Deliberation Room

- Applicable regulations.
- Similar cases.
- Side-by-side advocate arguments.
- Final verdict, confidence and dissenting interpretation.

### Research Dashboard

- Agreement with official rulings.
- Citation validity.
- Confidence calibration.
- Identity-swap stability.
- Unsupported-claim rate.

## Evaluation plan

Use a locked test set that was not used while writing prompts.

### Primary measurements

- **Decision agreement:** simulated versus official decision category.
- **Penalty agreement:** exact and adjacent-category agreement.
- **Citation precision:** cited passages that genuinely support the claim.
- **Citation completeness:** important claims with at least one valid citation.
- **Unsupported-claim rate:** claims without document or evidence support.
- **Identity-swap stability:** outcome changes after anonymizing/swapping identities.
- **Confidence calibration:** whether high-confidence decisions are more often correct.

The goal is not perfect agreement with FIA decisions. Disagreements should be inspectable and attributable to evidence, rules, precedent selection or interpretation.

## Six-week roadmap

### Week 1 — Dataset and ingestion

- Select one incident category and 20 candidate cases.
- Download and version FIA documents.
- Create incident and document schemas.
- Load telemetry for five proof-of-concept cases.

### Week 2 — Evidence construction

- Build deterministic telemetry feature functions.
- Create the incident timeline format.
- Manually verify five complete evidence packets.

### Week 3 — Retrieval agents

- Implement regulation and precedent retrieval.
- Add exact citation metadata.
- Test retrieval precision with hand-written questions.

### Week 4 — Deliberation

- Implement advocates and steward with typed outputs.
- Add schema validation, timeouts and one controlled retry.
- Reject numerical claims without evidence IDs.

### Week 5 — Evaluation

- Complete 15–20 cases.
- Run official-decision comparison and identity-swap tests.
- Record prompt/model versions for reproducibility.

### Week 6 — Product polish

- Finish Streamlit interface.
- Add evaluation dashboard and case-study pages.
- Write technical report, README and limitations.
- Record a three-minute demonstration.

## Suggested repository structure

```text
stewardlens/
  app/
    api/
    agents/
    retrieval/
    services/
    ui/
  data/
    manifests/
    processed/
  evals/
    cases/
    graders/
  notebooks/
  tests/
  scripts/
  README.md
```

## Definition of done

- At least 15 verified cases are browsable.
- Every verdict contains traceable evidence and regulation citations.
- Unsupported numerical claims are blocked.
- The system survives one agent timing out and reports partial results.
- Bias-swap and citation evaluations run from one command.
- The README contains architecture, limitations, reproducible setup and results.

## Portfolio pitch

> Built an evidence-grounded multi-agent F1 incident tribunal using telemetry, versioned FIA regulations and historical steward decisions. Evaluated ruling agreement, citation accuracy, confidence calibration and identity bias across a held-out incident set.


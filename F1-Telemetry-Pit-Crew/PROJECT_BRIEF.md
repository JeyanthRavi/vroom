# Telemetry Pit Crew

## Project in one sentence

Telemetry Pit Crew is a multi-agent lap-analysis system that compares Formula 1 telemetry, identifies where lap time was gained or lost, and produces an evidence-linked race-engineering debrief.

## Why this project exists

Telemetry dashboards show curves, but they rarely explain which differences mattered. This project converts synchronized lap data into corner-level findings while keeping mathematical computation separate from LLM interpretation.

The main research question is:

> Can specialist agents turn incomplete public telemetry into useful, correctly grounded lap diagnoses without overstating what the data proves?

## Version-one scope

- One circuit and one race weekend initially.
- Comparison of two clean laps from two drivers or from one driver's separate stints.
- Speed, throttle, brake, gear, RPM, DRS, distance and lap-time delta.
- Automatic track segmentation into straights and corner phases.
- Four specialist agents and one race-engineer agent.
- Post-session data only.

### Explicit non-goals

- Claiming access to complete team telemetry.
- Inferring tyre temperature, setup, steering angle or energy deployment as facts.
- Live communication with a real driver.
- Recommending safety-critical real-world driving actions.
- Letting an LLM compute braking points or time deltas.

## System architecture

```text
FastF1 session
      │
      v
lap selection and quality filters
      │
      v
distance alignment and corner segmentation
      │
      v
deterministic feature engine
      │
      ├──────────┬───────────┬────────────┬──────────────┐
      v          v           v            v              v
 Braking     Cornering    Traction    Straight-line   Data-quality
  Agent        Agent        Agent          Agent          Critic
      └──────────┴───────────┴────────────┴──────────────┘
                              │
                              v
                      Race Engineer Agent
                              │
                              v
               debrief + charts + evidence references
```

## Deterministic feature engine

This layer should produce all measurements used by agents:

- Align both laps to a shared distance grid.
- Calculate cumulative and local time delta.
- Detect braking onset and release.
- Estimate minimum speed and its location.
- Detect throttle pickup and full-throttle point.
- Measure entry, apex and exit speed differences.
- Calculate straight-line speed and acceleration differences.
- Track gear and DRS-state differences.
- Assign a data-quality score to each segment.

Store each result as an evidence object with units, calculation version and source interval.

## Agent contracts

### 1. Braking Agent

**Reads:** braking onset, speed, deceleration proxy, brake release and entry delta.

**Produces:** which driver braked earlier/later, whether the difference correlated with time gain, and any evidence-quality warnings.

It must not call later braking "better" unless the exit and total segment delta support that conclusion.

### 2. Cornering Agent

**Reads:** entry speed, minimum speed, apex location and corner-phase delta.

**Produces:** corner-level differences and alternative explanations.

Public telemetry lacks steering angle and detailed vehicle-state data, so conclusions must use language such as “consistent with” rather than claiming a definite driving technique.

### 3. Traction Agent

**Reads:** throttle pickup, time to full throttle, exit speed and exit delta.

**Produces:** evidence-grounded assessment of exit performance.

### 4. Straight-Line Agent

**Reads:** speed traces, DRS state, gear, RPM and acceleration proxy.

**Produces:** straight-line gains and whether DRS or the preceding corner plausibly contributed.

### 5. Data-Quality Critic

- Checks GPS/telemetry gaps and inconsistent sampling.
- Flags traffic, pit laps, yellow flags and non-representative laps.
- Blocks conclusions below a configurable quality threshold.
- Challenges causal language unsupported by available channels.

### 6. Race Engineer Agent

Combines the specialist findings into no more than three major takeaways, ordered by lap-time impact.

**Structured output:**

```json
{
  "lap_summary": "",
  "total_delta_seconds": 0.0,
  "priority_findings": [
    {
      "segment_id": "T04",
      "time_impact_seconds": 0.0,
      "finding": "",
      "evidence_ids": [],
      "confidence": 0.0,
      "alternative_explanation": ""
    }
  ],
  "data_limitations": []
}
```

## Data sources

- FastF1 as the main Python data source.
- OpenF1 as an optional REST/CSV source and later replay integration.
- Circuit metadata from FastF1 circuit information, followed by manual correction where automatic corner segmentation fails.

Cache complete source responses and record library/API versions. The same lap pair should produce identical deterministic features when rerun under the same feature-engine version.

## Minimal data model

### `sessions`

- `id`, `season`, `round`, `session_type`
- `circuit`, `session_date`, `source_version`

### `laps`

- `id`, `session_id`, `driver`, `lap_number`
- `lap_time`, `compound`, `tyre_life`
- `track_status`, `is_accurate`, `quality_score`

### `telemetry_samples`

- `lap_id`, `distance`, `time`
- `speed`, `throttle`, `brake`, `gear`, `rpm`, `drs`

### `segments`

- `id`, `session_id`, `name`, `segment_type`
- `distance_start`, `distance_end`, `corner_number`

### `computed_features`

- `comparison_id`, `segment_id`, `feature_name`
- `driver_a_value`, `driver_b_value`, `unit`
- `calculation_version`, `quality_score`, `evidence_id`

### `debrief_runs`

- `id`, `comparison_id`, `prompt_version`, `model`
- `specialist_outputs_json`, `final_output_json`
- `latency_ms`, `token_usage`, `created_at`

## API surface

- `GET /sessions`
- `GET /sessions/{id}/laps`
- `POST /comparisons`
- `GET /comparisons/{id}/telemetry`
- `POST /comparisons/{id}/analyze`
- `GET /analyses/{id}`
- `GET /evaluation/summary`

## Interface

### Session and Lap Selector

- Circuit, year and session selection.
- Driver and lap selection.
- Filters for clean/accurate laps, compounds and tyre age.

### Telemetry Workbench

- Synchronized speed, throttle, brake and gear charts.
- Lap-time delta chart.
- Track map coloured by time gained or lost.
- Clickable corner/segment cards.

### Engineering Debrief

- Three priority findings.
- Evidence links that highlight the relevant chart region.
- Confidence and alternative explanation for each finding.
- Explicit missing-channel and data-quality warnings.

### Evaluation Dashboard

- Grounding accuracy.
- Numerical consistency.
- Segment-ranking accuracy.
- Unsupported causal-claim rate.
- Agent latency and cost.

## Evaluation plan

Create a hand-labelled test set of 30–50 lap segments.

### Deterministic layer tests

- Alignment correctness on identical and synthetic laps.
- Known-shift tests for braking-point detection.
- Time-delta integration within a defined tolerance.
- Robustness to missing and unevenly sampled telemetry.

### Agent layer tests

- **Numerical consistency:** every number matches a feature object.
- **Evidence grounding:** every major conclusion cites the correct interval.
- **Impact ranking:** the largest findings correspond to the largest verified deltas.
- **Uncertainty discipline:** low-quality segments receive weaker or refused conclusions.
- **Paraphrase stability:** equivalent prompts produce materially consistent findings.
- **Unsupported causal claims:** claims about setup, tyres or driver intent without data.

## Six-week roadmap

### Week 1 — Data and lap selection

- Load one weekend with FastF1.
- Cache session data.
- Build clean-lap filters and comparison selection.
- Plot synchronized raw channels.

### Week 2 — Feature engine

- Align laps by distance.
- Calculate local and cumulative deltas.
- Implement initial braking, apex and throttle features.
- Add unit tests using synthetic traces.

### Week 3 — Track segmentation

- Import circuit corner metadata.
- Build corner/straight boundaries.
- Add track-map delta visualization.
- Hand-verify the first circuit.

### Week 4 — Specialist agents

- Implement four specialist agents with typed outputs.
- Add the data-quality critic.
- Reject outputs containing uncited numbers.

### Week 5 — Race engineer and evaluation

- Implement synthesis and priority ranking.
- Label 30–50 test segments.
- Measure grounding and unsupported-claim rate.

### Week 6 — Product polish

- Finish Streamlit interface.
- Add shareable comparison pages.
- Complete README, architecture diagram and technical report.
- Record a three-minute demo using a memorable driver comparison.

## Suggested repository structure

```text
telemetry-pit-crew/
  app/
    api/
    agents/
    features/
    ingestion/
    ui/
  data/
    cache/
    manifests/
  evals/
    labelled_segments/
    graders/
  notebooks/
  tests/
  scripts/
  README.md
```

## Definition of done

- A user can select and compare two valid laps without editing code.
- At least one circuit is correctly segmented and visually mapped.
- Every reported number comes from a versioned feature object.
- Findings link directly to relevant telemetry intervals.
- Low-quality data triggers warnings or abstention.
- Unit and evaluation tests run from one command.
- README documents public-telemetry limitations without overclaiming.

## Portfolio pitch

> Built a multi-agent Formula 1 telemetry engineering assistant that decomposes lap performance into braking, cornering, traction and straight-line analysis. Kept numerical reasoning deterministic and evaluated agent grounding, uncertainty handling and causal overclaiming on a hand-labelled telemetry test set.


# Optional telemetry representation experiment

Status: **not run**.

The bundled Monza telemetry fixture contains two laps. That is sufficient to
exercise the existing comparison UI, but not to estimate whether a learned
embedding reconstructs traces better than PCA or whether nearest neighbours
preserve driver/session identity. Synthetic augmentation would test plumbing,
not the stated representation question, and would add a second fixture-only DL
pipeline without strengthening the release evidence.

The experiment is therefore deferred until a rights-reviewed local corpus has
enough independent laps, drivers, and sessions for a held-out evaluation. No
telemetry performance claim is made.

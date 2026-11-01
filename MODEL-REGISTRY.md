# Local model registry policy

The registry is a git-ignored JSON list under `.local-data/ml-runs/`. Every
entry has an explicit `status`. Automated code may write only `staging`,
`rejected`, or `archived`; `production` is rejected by the registry API.

Vroom has no automatic promotion workflow. A future public release would need
an owner-reviewed policy, rights approval, independent evaluation, rollback
artifact, and a separate manual promotion mechanism. None is implemented here.

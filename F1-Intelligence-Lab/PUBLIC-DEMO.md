# Public replay deployment record

Published 28 October 2026:
https://vroom-race-replay-jeyanth.quantum-banana.chatgpt.site

## Scope

36 historical races, five baseline/model options, precomputed predictions only.
No live inference, training endpoint, model weights, raw caches, or private user
files. The main JeyanthRavi/vroom GitHub repository remains private. Static Site
source is isolated in the sibling `vroom-replay-site` directory outside that repo.
No paid service or billing plan was provisioned. This is not a guarantee about
the hosting provider's future pricing or quotas.

## Deployment identity

- Project: `appgprj_6ae2071d34d08191a075f7c1814e0217`
- Saved version: `appgprj_6ae2071d34d08191a075f7c1814e0217~appgver_6a1a2348f3548191b8dc2152fd6b3add`
- Source commit: `4eebeecc6f5c9a4600867ca26124f5fcc9184d36`
- Successful deployment: `appgdep_6ae20797775881918ba386865d62fdb7`
- Audience: public

## Post-deployment checks

Anonymous HTTP GET requests returned 200 for `/`, `/demo.js` and `/data.json`.
Published JavaScript (4,065 bytes) and prediction data (7,568,824 bytes) match the
verified local export byte-for-byte. HTML includes the hosting provider's
Cloudflare challenge injection, so raw HTML hashes differ from the export.
This HTTP check does not substitute for a post-publication browser interaction
test. Selector/chart/evidence-table checks were completed locally before release.

## Updates and rollback

Keep the existing Site ID in `vroom-replay-site/.openai/hosting.json`. Rebuild and
verify a fresh export before replacing the Site's three static assets. Use the
Sites source/package/save/deploy workflow; do not publish the full research repo.
Retain the version ID above. After a later faulty deployment, redeploy that saved
version using Sites, then verify the deployment status and public assets again.
No newer-version rollback has been exercised on this public Site yet.

### Immediate privacy rollback while rights remain unresolved

This is an owner action; the release process does not change hosting visibility automatically.

1. Open the hosting project identified above and change its audience from public to private/owner-only. If that host does not offer private visibility, disable or unpublish the deployment without deleting the saved version.
2. From a signed-out browser, request `/`, `/demo.js`, and `/data.json`. Each must require authentication or return a non-success response; a `200` response means the rollback is incomplete.
3. Keep the saved version ID and local checksum manifest so the reviewed build remains recoverable.
4. Before any later public restoration, obtain and record the relevant rights clarification, build the default aggregate export, verify its checksums, and repeat anonymous browser checks.

## Remaining limits

- [Rights review](DATA-RIGHTS-REVIEW.md): public redistribution permission remains
  unresolved; recommend owner-private access pending written clarification.
- [Hosted mobile QA](MOBILE-QA.md): interactions work at phone widths, with
  readability and scroll-discoverability issues recorded.
- No scheduled monitoring, live inference SLA or automatic retraining.
- Container build remains unverified because the local Docker daemon was unavailable.
- 2026 results are reused regression evidence, not an untouched test set.

See [ML release](ML-RELEASE.md) and [model card](MODEL-CARD.md).

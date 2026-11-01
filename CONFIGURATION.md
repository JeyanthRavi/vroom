# Configuration

All settings are optional. Network/disk-writing HTTP endpoints are disabled by default.

| Variable | Meaning | Default | Example safe value |
|---|---|---|---|
| `F1_ADMIN_TOKEN` | Shared secret required by import/write endpoints | unset; endpoints disabled | a long random value supplied only in the server environment |
| `F1_ALLOW_LOCAL_IMPORT` | Explicitly allow imports without a token when client and bind host are loopback | `0` | `1` for a local-only workstation |
| `F1_BIND_HOST` | Host used by the local-import safety check | `127.0.0.1` | `127.0.0.1`; never use local bypass with `0.0.0.0` |
| `F1_LAB_DATA` | SQLite/cache root | `F1-Intelligence-Lab/.local-data` | an absolute private directory outside a public web root |
| `F1_DEMO_EXPORT` | Checksum-verified static replay directory | unset; replay returns 503 | absolute path to `.build/public-demo` after `make public-demo` |
| `F1_ML_DATASET` | Audited feature dataset root for local historical inference | unset | absolute git-ignored dataset directory |
| `F1_ML_RUN` | Classical model run directory | unset | absolute git-ignored run directory |
| `F1_DL_RUN` | Sequence/GRU results directory exposed read-only | unset | absolute git-ignored run directory |
| `F1_ROBUST_RUN` | Restart-aware model run exposed read-only | unset | absolute git-ignored run directory |
| `F1_CROSS_SEASON_RUN` | Frozen cross-season evaluation directory | unset | absolute git-ignored run directory |

Never commit tokens, model checkpoints, raw caches, or `.env` files. Public deployments should use the read-only `demo_app` with the aggregate export.


# Repository Management

## Quick Reference

| Task | Command |
|------|---------|
| Setup everything | `./bin/setup` |
| Setup Python only | `./bin/setup --python` |
| Setup Node only | `./bin/setup --node` |
| Recreate venv from scratch | `./bin/setup --clean-venv` |
| See what's eating space | `./bin/size-report` |
| Detailed breakdown | `./bin/size-report --detail` |
| Preview cleanup | `./bin/cleanup --all --dry-run` |
| Clean generated artifacts | `./bin/cleanup --artifacts` |
| Clean caches only | `./bin/cleanup --caches` |
| Remove all dependencies | `./bin/cleanup --deps` |
| Nuclear cleanup | `./bin/cleanup --all` |

## Disk Space Budget

ettametta's working directory can grow to 8GB+ if left unmanaged. Here's where the space goes:

| Category | Typical Size | Reinstallable? | Managed By |
|----------|-------------|----------------|------------|
| `.venv/` (Python) | ~2 GB | Yes | `./bin/setup --python` |
| `node_modules/` (dashboard) | ~500 KB | Yes | `./bin/setup --node` |
| `apps/remotion-studio/node_modules/` | ~320 MB | Yes | `./bin/setup --node` |
| `outputs/` (generated videos) | ~2.5 GB | No | `./bin/cleanup --artifacts` |
| `output/` (older outputs) | ~1.6 GB | No | `./bin/cleanup --artifacts` |
| `temp/` | ~340 MB | No | `./bin/cleanup --artifacts` |
| `__pycache__/` | ~50 MB | Yes | `./bin/cleanup --caches` |
| `*.db` files | ~5 MB | Yes | `./bin/cleanup --dbs` |
| `*.tar.gz` patches | ~15 MB | No | `./bin/cleanup --artifacts` |

## Typical Workflows

### Fresh clone setup
```bash
git clone <repo>
cd ettametta
./bin/setup            # Creates .venv + installs all deps
```

### Daily development
```bash
source .venv/bin/activate
uvicorn src.api.main:app --reload
# In another terminal:
cd apps/dashboard && npm run dev
```

### Periodic cleanup (weekly recommended)
```bash
./bin/cleanup --artifacts --caches    # Free ~3-4 GB
./bin/cleanup --all --dry-run         # Preview full cleanup
```

### Full reset
```bash
./bin/cleanup --all                   # Remove everything
./bin/setup                           # Reinstall from scratch
```

### Before committing
```bash
./bin/size-report --git               # Check for tracked bloat
```

## What Lives Where

```
ettametta/
├── src/                    # Python source (API + services)
├── apps/
│   ├── dashboard/          # Next.js frontend
│   └── remotion-studio/    # Video rendering
├── data/                   # Runtime data (DBs, models, training)
├── bin/                    # Management scripts (setup, cleanup, size-report)
├── .venv/                  # Python virtual environment (gitignored)
├── requirements.txt        # Python dependencies
├── docker-compose.yml      # Full stack orchestration
└── docs/                   # Documentation
```

## Gitignore Policy

The `.gitignore` covers:
- **Dependencies**: `.venv/`, `venv/`, `node_modules/`
- **Generated outputs**: `outputs/`, `output/`, `temp/`, `*.mp4`, `*.mp3`
- **Caches**: `__pycache__/`, `.ruff_cache/`, `.pytest_cache/`
- **Databases**: `*.db` (all SQLite files)
- **AI tool state**: `.kilo/`, `.kilocode/`, `.dag_cache/`
- **Credentials**: `.env`, `*.pem`, `*.key`, `key_raw.txt`
- **Archives**: `*.tar.gz`

If you find tracked files that should be ignored:
```bash
git rm --cached <file>     # Untrack without deleting locally
```

## openclaw Extraction

See [OPENCLAW_EXTRACTION.md](OPENCLAW_EXTRACTION.md) for the plan to extract openclaw as a standalone package.

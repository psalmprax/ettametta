# openclaw Extraction Plan

## Why Extract?

`src/services/openclaw/` is the largest service in ettametta (80 Python files). It's a self-contained agent/skill framework with its own:
- Skill registry and execution engine
- Configuration system
- Multiple video generation skills (Runway, Haiper, Genmo, Vidu, etc.)
- Workflow orchestration
- Self-healing capabilities
- Data scraping skills

This makes it a natural candidate for extraction into its own package/repo.

## Recommended Approach: Git Subtree Split

Use `git subtree` to preserve history while extracting openclaw into its own repo.

### Step 1: Create the standalone repo

```bash
# Create a new repo on GitHub: openclaw
# Then extract with history:
git subtree split --prefix=src/services/openclaw -b openclaw-extract
```

### Step 2: Push to new repo

```bash
# Add the remote
git remote add openclaw git@github.com:<org>/openclaw.git

# Push the extracted branch
git push openclaw openclaw-extract:main
```

### Step 3: Restructure the extracted repo

The new `openclaw` repo should have this structure:
```
openclaw/
├── openclaw/
│   ├── __init__.py
│   ├── config.py
│   ├── main.py
│   ├── base_skill.py
│   └── skills/
│       ├── runway.py
│       ├── haiper.py
│       ├── genmo.py
│       └── ...
├── tests/
├── pyproject.toml
├── requirements.txt
└── README.md
```

### Step 4: Install as dependency in ettametta

In ettametta's `requirements.txt`, replace the local openclaw code with:
```
openclaw @ git+https://github.com/<org>/openclaw.git@main
```

Or for development, use a local editable install:
```bash
pip install -e ../openclaw
```

### Step 5: Update imports in ettametta

Change all imports from:
```python
from src.services.openclaw.main import ...
from src.services.openclaw.skills.runway import ...
```
To:
```python
from openclaw.main import ...
from openclaw.skills.runway import ...
```

## Alternative: PyPI Package

If openclaw should be publicly available:

1. Add `pyproject.toml` with proper metadata
2. Build and publish: `python -m build && twine upload dist/*`
3. Install via: `pip install openclaw`

## Dependency Map

Before extracting, verify which ettametta services openclaw depends on:

```
openclaw currently imports from:
- src.services.openclaw.* (self-contained)
- src.api.config (settings)
- src.api.utils.database (DB session)
- src.shared.observability (logging)
```

These dependencies need to be either:
- Injected via dependency injection at runtime
- Passed as configuration
- Made available as a shared `ettametta-core` package

## Risks

- **Circular dependencies**: openclaw may import from other ettametta services
- **Shared state**: Database sessions, Redis connections, config objects
- **Testing**: Integration tests may need the full ettametta stack

## Recommended Next Steps

1. Run a dependency analysis: `grep -r "from src\." src/services/openclaw/ | sort -u`
2. Identify which imports are truly external to openclaw
3. Design the dependency injection interface
4. Extract and restructure
5. Update ettametta to use the package

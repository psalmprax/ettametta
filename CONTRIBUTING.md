# Contributing to ettametta

Thank you for your interest in contributing to ettametta! This document provides guidelines and workflows for contributing.

## Code of Conduct

By participating, you agree to uphold our [Code of Conduct](./CODE_OF_CONDUCT.md). Please report unacceptable behavior to the maintainers.

## Getting Started

1. **Fork** the repository.
2. **Clone** your fork:
   ```bash
   git clone https://github.com/your-username/ettametta.git
   cd ettametta
   ```
3. **Set up the development environment**:
   ```bash
   docker compose -f docker-compose.dev.yml up -d
   ```
   Or for local development:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r src/api/requirements.txt
   ```

## Development Workflow

### Branching

- `main` — production-ready code
- `stage` — staging / pre-release
- Feature branches: `feat/short-description`
- Bugfix branches: `fix/short-description`

### Commit Messages

We use conventional commits:
```
feat: add multi-platform publishing
fix: resolve discovery service timeout
chore: update dependencies
docs: add API reference
```

### Pull Requests

1. Create a feature branch from `stage`.
2. Make your changes.
3. Write or update tests.
4. Run the test suite:
   ```bash
   pytest tests/ -v --tb=short
   ```
5. Push and open a PR against `stage`.

### PR Requirements

- Clear title and description
- Link to related issue (if applicable)
- Tests for new functionality
- No breaking changes without discussion
- Update documentation if needed

## Project Structure

```
ettametta/
├── src/api/           # FastAPI backend
├── src/services/      # Business logic services
├── apps/              # Frontend applications
│   ├── dashboard/     # Next.js dashboard
│   └── remotion-studio/
├── data/              # Runtime data storage
├── infra/             # Infrastructure configs
└── docs/              # Documentation
```

## Testing

- **Backend**: `pytest tests/ -v --tb=short`
- **Frontend**: `cd apps/dashboard && npm test`
- **E2E**: Playwright tests in `tests/e2e/`

## Code Style

- **Python**: Follow PEP 8, use type hints
- **TypeScript/React**: Use the existing patterns in the codebase
- Run pre-commit hooks before pushing

## Questions?

Open a [Discussion](https://github.com/psalmprax/ettametta/discussions) or join our community.

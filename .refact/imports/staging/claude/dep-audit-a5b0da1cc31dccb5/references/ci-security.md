# CI Security Scan Configuration

## Current Setup (Non-Blocking)

### ci-cd.yml (lines 71-86)
```yaml
security-scan:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.10'
    - name: Install dependencies
      run: pip install bandit safety
    - name: Security scan
      run: |
        bandit -r src/api/ -f json -o bandit-report.json || true
        safety check --full-report || true
```

### ci.yml (lines 46-56)
```yaml
- name: Security scan
  run: |
    safety check --json > security_report.json || true
    bandit -r . -f json -o bandit_report.json || true
```

## Problem

Both use `|| true` — **scan failures do not block builds or deploys**.

## What's Missing

- No Dependabot configuration (`.github/dependabot.yml`)
- No Renovate configuration
- No Snyk integration
- No Trivy for Docker image scanning
- No pip-audit
- No npm audit in CI

## Recommended Fixes

### 1. Make scans blocking
```yaml
- name: Security scan
  run: |
    bandit -r src/api/ -f json -o bandit-report.json
    safety check --full-report
```

### 2. Add Dependabot
```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: pip
    directory: /src/api
    schedule:
      interval: weekly
  - package-ecosystem: npm
    directory: /
    schedule:
      interval: weekly
  - package-ecosystem: docker
    directory: /
    schedule:
      interval: weekly
```

### 3. Add pip-audit to CI
```yaml
- name: Audit Python dependencies
  run: |
    pip install pip-audit
    pip-audit -r src/api/requirements.txt
```

### 4. Add npm audit to CI
```yaml
- name: Audit Node dependencies
  run: npm audit --production
```

### 5. Add Trivy for Docker images
```yaml
- name: Scan Docker image
  uses: aquasecurity/trivy-action@master
  with:
    image-ref: ettametta-api:latest
    severity: CRITICAL,HIGH
    exit-code: 1
```

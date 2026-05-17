# Security Policy

## Supported Versions

| Version | Supported          |
|---------|--------------------|
| 0.9.x   | :white_check_mark: |
| < 0.9   | :x:                |

## Reporting a Vulnerability

We take the security of ettametta seriously. If you believe you have found a
security vulnerability, please **do not** open a public issue.

Instead, report it privately by emailing the maintainers or opening a
[GitHub Security Advisory](https://github.com/psalmprax/ettametta/security/advisories/new).

### What to include

- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

### Response Timeline

- **24 hours**: Acknowledgment of receipt
- **7 days**: Initial assessment and remediation plan
- **30 days**: Fix deployed (depending on severity)

## Security Measures

- API keys and secrets are stored in a secure vault (not in code)
- Authentication enforced on all sensitive endpoints
- SQL injection prevention via SQLAlchemy parameterized queries
- OAuth tokens stored with user isolation
- CORS configured for production domains only
- Rate limiting on auth endpoints
- `httpx` with limited timeouts to prevent SSRF abuse

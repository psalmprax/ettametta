# Deployment Guide

The full deployment guide lives at **[`../docs/deployment_guide.md`](../docs/deployment_guide.md)**.

For convenience, the **§ 0. Remote Jumpbox Targets** section (added 2026-06-15) is the canonical home for the named SSH endpoints used by ops:

| Name | Host | User | Key | Notes |
|---|---|---|---|---|
| `ettametta-prod` | `149.104.110.122` (`w5m8yij9.vm`) | `root` | `~/.ssh/ettametta_prod` (chmod 600) | API on host `:7201` (container `:8000`); Traefik `:80/:443/:8080` |

Add the `Host` block from the real guide to your local `~/.ssh/config` to get
`ssh ettametta-prod '...'` for one-line ops commands.

See the full guide for: OCI S3 setup, YouTube/TikTok cookies, YouTube Data API,
Telegram bots, Jenkins CI/CD, and the code-fix history.

#!/usr/bin/env bash
# =============================================================================
# ettametta — Comprehensive Server Provisioning Script
# =============================================================================
# Performs a complete server setup from scratch:
#   1. OS detection + system dependency installation (Docker, ffmpeg, git, etc.)
#   2. Git clone (or pull if already present)
#   3. .env generation from .env.production.template with auto-generated secrets
#   4. Database bootstrap (admin user, credits)
#   5. Alembic migrations (upgrade head)
#   6. Docker Compose build + start
#   7. Post-deploy health verification
#
# Usage:
#   # Interactive mode (prompts for API keys and admin credentials)
#   ./scripts/setup-server.sh
#
#   # Non-interactive (CI/CD) — all values from environment variables
#   ./scripts/setup-server.sh --non-interactive
#
#   # Skip Docker install on already-provisioned machines
#   ./scripts/setup-server.sh --skip-docker
#
#   # Skip clone if repo already present
#   ./scripts/setup-server.sh --skip-clone
#
#   # Dry-run: print what WOULD be done without doing it
#   ./scripts/setup-server.sh --dry-run
#
# Environment variables (for --non-interactive mode):
#   Required:
#     BOOTSTRAP_ADMIN_USERNAME   — admin username
#     BOOTSTRAP_ADMIN_EMAIL      — admin email
#     GOOGLE_CLIENT_ID           — Google OAuth client ID
#     GOOGLE_CLIENT_SECRET       — Google OAuth client secret
#     TIKTOK_CLIENT_KEY          — TikTok client key
#     TIKTOK_CLIENT_SECRET       — TikTok client secret
#     GROQ_API_KEY              — Groq API key (or OPENAI_API_KEY)
#
#   Optional (auto-generated if unset):
#     POSTGRES_USER              — defaults to "ettametta"
#     POSTGRES_PASSWORD          — auto-generated 32-char random
#     REDIS_PASSWORD             — auto-generated 32-char random
#     AI_CLUSTER_SECRET          — auto-generated 32-char random
#     SECRET_KEY                 — auto-generated 64-char random
#     INTERNAL_API_TOKEN         — auto-generated 48-char random
#     BOOTSTRAP_ADMIN_PASSWORD   — auto-generated 24-char random
#     TRAEFIK_DASHBOARD_USERS    — auto-generated (pure Python bcrypt, no htpasswd needed)
#
#   Configurable:
#     ETTA_REPO_URL              — Git repo URL (default: https://github.com/nashsu/ettametta.git)
#     ETTA_REPO_BRANCH           — Branch to checkout (default: master)
#     ETTA_INSTALL_DIR           — Install directory (default: /opt/ettametta)
#     BOOTSTRAP_ADMIN_ROLE       — Admin role (default: admin)
#     BOOTSTRAP_ADMIN_SUBSCRIPTION — Subscription tier (default: premium)
#     BOOTSTRAP_INITIAL_CREDITS  — Starting credits (default: 1000)
#     CELERY_CONCURRENCY         — Celery worker concurrency (default: 2)
#     PRODUCTION_DOMAIN          — Production domain
#     CORS_ORIGINS               — CORS origins
# =============================================================================

set -euo pipefail

# ── Color helpers ────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

step()  { echo -e "\n${BOLD}${BLUE}═══ ${1}${NC}"; }
info()  { echo -e "${CYAN}  ℹ ${1}${NC}"; }
ok()    { echo -e "${GREEN}  ✓ ${1}${NC}"; }
warn()  { echo -e "${YELLOW}  ⚠ ${1}${NC}"; }
err()   { echo -e "${RED}  ✗ ${1}${NC}"; }
fatal() { echo -e "${RED}${BOLD}FATAL: ${1}${NC}"; exit 1; }

# ── Banner ───────────────────────────────────────────────────────────────────
echo -e "${BOLD}${CYAN}"
echo "  ╔══════════════════════════════════════════════╗"
echo "  ║       ettametta Server Provisioner           ║"
echo "  ║  AI-Powered Viral Content Engine Setup       ║"
echo "  ╚══════════════════════════════════════════════╝"
echo -e "${NC}"

# ── Parse flags ──────────────────────────────────────────────────────────────
NON_INTERACTIVE=false
SKIP_DOCKER=false
SKIP_CLONE=false
DRY_RUN=false

for arg in "$@"; do
    case "$arg" in
        --non-interactive) NON_INTERACTIVE=true ;;
        --skip-docker)     SKIP_DOCKER=true ;;
        --skip-clone)      SKIP_CLONE=true ;;
        --dry-run)         DRY_RUN=true ;;
        --help|-h)
            echo "Usage: $0 [--non-interactive] [--skip-docker] [--skip-clone] [--dry-run]"
            echo ""
            echo "  --non-interactive   Run without prompts (uses env vars)"
            echo "  --skip-docker       Skip Docker installation"
            echo "  --skip-clone        Skip git clone"
            echo "  --dry-run           Print what would be done without doing it"
            exit 0
            ;;
        *) err "Unknown flag: $arg"; exit 1 ;;
    esac
done

# ── Defaults ──────────────────────────────────────────────────────────────────
export ETTA_REPO_URL="${ETTA_REPO_URL:-https://github.com/nashsu/ettametta.git}"
export ETTA_REPO_BRANCH="${ETTA_REPO_BRANCH:-master}"
export ETTA_INSTALL_DIR="${ETTA_INSTALL_DIR:-/opt/ettametta}"
export BOOTSTRAP_ADMIN_ROLE="${BOOTSTRAP_ADMIN_ROLE:-admin}"
export BOOTSTRAP_ADMIN_SUBSCRIPTION="${BOOTSTRAP_ADMIN_SUBSCRIPTION:-premium}"
export BOOTSTRAP_INITIAL_CREDITS="${BOOTSTRAP_INITIAL_CREDITS:-1000}"
export CELERY_CONCURRENCY="${CELERY_CONCURRENCY:-2}"

# Only default if not already set in env (non-interactive mode)
export POSTGRES_USER="${POSTGRES_USER:-ettametta}"
export PRODUCTION_DOMAIN="${PRODUCTION_DOMAIN:-https://ettametta.example.com}"
export CORS_ORIGINS="${CORS_ORIGINS:-https://dashboard.ettametta.example.com,https://api.ettametta.example.com}"
export ENV="${ENV:-production}"
export STORAGE_PROVIDER="${STORAGE_PROVIDER:-LOCAL}"

if [ "$DRY_RUN" = true ]; then
    warn "DRY RUN MODE — no changes will be made."
fi

# ── Helper: generate a cryptographically secure random string ─────────────────
# Prefers Python's secrets module. Falls back to openssl rand -hex (no
# problematic chars like /+= from base64). Last resort: /dev/urandom.
gen_secret() {
    local length="${1:-32}"
    python3 -c "import secrets; print(secrets.token_urlsafe(${length}))" 2>/dev/null \
        || openssl rand -hex "$(( length * 3 / 4 + 1 ))" 2>/dev/null \
        || cat /dev/urandom 2>/dev/null | tr -dc 'a-zA-Z0-9' | fold -w "${length}" | head -n 1
}

# ── Helper: generate SHA-512 htpasswd string using pure Python stdlib ─────────
# Uses crypt.crypt with $6$ (SHA-512) which is universally supported by glibc
# on ALL Linux distributions. Traefik accepts this for basic auth.
# Prior art: $2b$ (bcrypt) is not available on older glibc (returns *0).
gen_traefik_htpasswd() {
    local username="${1:-admin}"
    local password="${2:-$(gen_secret 16)}"
    python3 -c "
import crypt, base64, os, sys
password = sys.argv[1] if len(sys.argv) > 1 else '$password'
# $6$ = SHA-512 (universally supported); $2b$ = bcrypt (glibc-dependent)
# We try bcrypt first, fall back to SHA-512 if crypt returns failure marker
salt_bcrypt = base64.b64encode(os.urandom(16)).decode('ascii')[:22]
salt_bcrypt = ''.join(c for c in salt_bcrypt if c in './ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789')[:22]
h = crypt.crypt(password, '\$2b\$10\$' + (salt_bcrypt or 'x' * 22))
if not h or h.startswith('*') or h == password:
    # bcrypt failed — fall back to SHA-512 (works everywhere)
    salt_sha = base64.b64encode(os.urandom(6)).decode('ascii')[:8]
    h = crypt.crypt(password, '\$6\$' + salt_sha)
print(f'{username}:{h}')
" "$password" 2>/dev/null
}

# ── Helper: prompt or use env var ─────────────────────────────────────────────
prompt_required() {
    local var_name="$1"
    local prompt_text="$2"
    local current_value="${!var_name:-}"

    if [ -n "$current_value" ]; then
        ok "${var_name} already set (using environment value)"
        return 0
    fi

    if [ "$NON_INTERACTIVE" = true ]; then
        # Collect missing vars instead of failing immediately
        MISSING_REQUIRED_VARS="${MISSING_REQUIRED_VARS:-} ${var_name} (${prompt_text})"
        return 0
    fi

    while [ -z "${!var_name:-}" ]; do
        echo -ne "${YELLOW}${prompt_text}: ${NC}"
        read -r input
        export "${var_name}=${input}"
    done
}

prompt_optional() {
    local var_name="$1"
    local prompt_text="$2"
    local default_value="${3:-}"
    local current_value="${!var_name:-}"

    if [ -n "$current_value" ]; then
        info "${var_name} already set (using environment value)"
        return 0
    fi

    if [ "$NON_INTERACTIVE" = true ]; then
        export "${var_name}=${default_value}"
        return 0
    fi

    echo -ne "${YELLOW}${prompt_text} [${default_value}]: ${NC}"
    read -r input
    export "${var_name}=${input:-$default_value}"
}

# Collect required vars for non-interactive mode validation
MISSING_REQUIRED_VARS=""

# ═══════════════════════════════════════════════════════════════════════════
# STEP 1: OS Detection
# ═══════════════════════════════════════════════════════════════════════════
step "1/7 — OS Detection & Prerequisites"

OS="$(uname -s)"
OS_ID=""

if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS_ID="${ID}"
fi

info "Detected OS: ${OS} / ${OS_ID:-unknown}"

# ── STEP 2: Install Docker ───────────────────────────────────────────────────
if [ "$SKIP_DOCKER" = true ]; then
    step "2/7 — Docker Installation (SKIPPED)"
else
    step "2/7 — Docker Installation"

    if command -v docker &>/dev/null; then
        ok "Docker $(docker --version | awk '{print $3}' | tr -d ',') already installed"
    else
        info "Installing Docker..."
        if [ "$DRY_RUN" = true ]; then
            info "[DRY-RUN] Would install Docker"
        else
            case "${OS_ID}" in
                ubuntu|debian)
                    apt-get update -qq
                    apt-get install -y -qq ca-certificates curl
                    install -m 0755 -d /etc/apt/keyrings
                    curl -fsSL "https://download.docker.com/linux/${OS_ID}/gpg" \
                        -o /etc/apt/keyrings/docker.asc
                    chmod a+r /etc/apt/keyrings/docker.asc
                    # shellcheck disable=SC1091
                    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/${OS_ID} $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
                        > /etc/apt/sources.list.d/docker.list
                    apt-get update -qq
                    apt-get install -y -qq docker-ce docker-ce-cli containerd.io \
                        docker-buildx-plugin docker-compose-plugin
                    ;;
                centos|rhel|fedora)
                    dnf -y install dnf-plugins-core
                    dnf config-manager --add-repo "https://download.docker.com/linux/${OS_ID}/docker-ce.repo"
                    dnf install -y docker-ce docker-ce-cli containerd.io \
                        docker-buildx-plugin docker-compose-plugin
                    systemctl enable --now docker
                    ;;
                amzn)
                    yum install -y docker
                    systemctl enable --now docker
                    mkdir -p /usr/local/lib/docker/cli-plugins
                    curl -fsSL "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" \
                        -o /usr/local/lib/docker/cli-plugins/docker-compose
                    chmod +x /usr/local/lib/docker/cli-plugins/docker-compose
                    ;;
                *)
                    warn "Unrecognized OS '${OS_ID}'. Attempting generic Docker install via convenience script..."
                    curl -fsSL https://get.docker.com | sh
                    ;;
            esac
            ok "Docker installed"
        fi
    fi

    # Verify Docker is running
    if [ "$DRY_RUN" = false ]; then
        if ! docker info &>/dev/null; then
            info "Starting Docker daemon..."
            systemctl start docker 2>/dev/null || service docker start 2>/dev/null || true
            sleep 2
        fi

        if ! docker info &>/dev/null; then
            fatal "Docker daemon is not running. Start it manually and re-run."
        fi
        ok "Docker daemon is running"
    fi

    # Ensure docker compose (plugin) is available
    if [ "$DRY_RUN" = false ]; then
        if ! docker compose version &>/dev/null; then
            warn "docker compose plugin not found. Installing..."
            DOCKER_CONFIG="${DOCKER_CONFIG:-$HOME/.docker}"
            mkdir -p "${DOCKER_CONFIG}/cli-plugins"
            curl -fsSL "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" \
                -o "${DOCKER_CONFIG}/cli-plugins/docker-compose"
            chmod +x "${DOCKER_CONFIG}/cli-plugins/docker-compose"
        fi
        ok "docker compose plugin: $(docker compose version 2>/dev/null | head -1)"
    fi
fi

# ── STEP 3: System Dependencies ───────────────────────────────────────────────
step "3/7 — System Dependencies"

install_sys_deps() {
    local deps="git curl python3 python3-pip ffmpeg"
    info "Installing: ${deps}"

    if [ "$DRY_RUN" = true ]; then
        info "[DRY-RUN] Would install: ${deps}"
        return 0
    fi

    case "${OS_ID}" in
        ubuntu|debian)
            apt-get update -qq
            apt-get install -y -qq ${deps}
            ;;
        centos|rhel|fedora)
            dnf install -y ${deps}
            ;;
        amzn)
            yum install -y ${deps}
            ;;
        *)
            warn "Unrecognized OS — please install manually: ${deps}"
            ;;
    esac

    ok "System dependencies installed"
}

# Quick check: are the key binaries present?
MISSING_DEPS=""
for bin in git curl python3 ffmpeg; do
    if ! command -v "$bin" &>/dev/null; then
        MISSING_DEPS="${MISSING_DEPS} ${bin}"
    fi
done

if [ -n "$MISSING_DEPS" ]; then
    install_sys_deps
else
    ok "All system dependencies present (git, curl, python3, ffmpeg)"
fi

# ── STEP 4: Git Clone or Pull ─────────────────────────────────────────────────
if [ "$SKIP_CLONE" = true ]; then
    step "4/7 — Repository Setup (SKIPPED — using directory: ${ETTA_INSTALL_DIR})"
    if [ ! -d "${ETTA_INSTALL_DIR}" ]; then
        fatal "ETTA_INSTALL_DIR (${ETTA_INSTALL_DIR}) does not exist and --skip-clone is set."
    fi
    cd "${ETTA_INSTALL_DIR}"
else
    step "4/7 — Repository Setup"

    if [ -d "${ETTA_INSTALL_DIR}/.git" ]; then
        info "Repository exists at ${ETTA_INSTALL_DIR} — pulling latest"
        if [ "$DRY_RUN" = false ]; then
            cd "${ETTA_INSTALL_DIR}"
            git fetch origin "${ETTA_REPO_BRANCH}" 2>/dev/null || warn "Could not fetch; continuing with local state"
            git checkout "${ETTA_REPO_BRANCH}" 2>/dev/null || warn "Could not checkout ${ETTA_REPO_BRANCH}; staying on current branch"
            git pull origin "${ETTA_REPO_BRANCH}" 2>/dev/null || info "Pull skipped (may already be up-to-date or offline)"
        fi
        ok "Repository updated at ${ETTA_INSTALL_DIR}"
    else
        info "Cloning ${ETTA_REPO_URL} (branch: ${ETTA_REPO_BRANCH})"
        if [ "$DRY_RUN" = false ]; then
            mkdir -p "$(dirname "${ETTA_INSTALL_DIR}")"
            git clone --branch "${ETTA_REPO_BRANCH}" "${ETTA_REPO_URL}" "${ETTA_INSTALL_DIR}"
        fi
        ok "Repository cloned to ${ETTA_INSTALL_DIR}"
    fi

    cd "${ETTA_INSTALL_DIR}"
fi

# ── STEP 5: .env Generation ──────────────────────────────────────────────────
step "5/7 — Environment Configuration (.env)"

# Auto-generate all secrets (secure random strings)
export POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-$(gen_secret 32)}"
export REDIS_PASSWORD="${REDIS_PASSWORD:-$(gen_secret 32)}"
export AI_CLUSTER_SECRET="${AI_CLUSTER_SECRET:-$(gen_secret 32)}"
export SECRET_KEY="${SECRET_KEY:-$(gen_secret 48)}"
export INTERNAL_API_TOKEN="${INTERNAL_API_TOKEN:-$(gen_secret 36)}"
export BOOTSTRAP_ADMIN_PASSWORD="${BOOTSTRAP_ADMIN_PASSWORD:-$(gen_secret 24)}"

# Build DATABASE_URL (docker-internal: used by containers) and REDIS_URL
export DATABASE_URL="${DATABASE_URL:-postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/ettametta}"
export REDIS_URL="${REDIS_URL:-redis://:${REDIS_PASSWORD}@redis:6379/0}"

if [ -z "${TRAEFIK_DASHBOARD_USERS:-}" ]; then
    TRAEFIK_TMP_PW="$(gen_secret 16)"
    TRAEFIK_DASHBOARD_USERS="$(gen_traefik_htpasswd admin "${TRAEFIK_TMP_PW}")"
    # Verify the generated hash looks valid (starts with $ for crypt format)
    if [ -z "${TRAEFIK_DASHBOARD_USERS:-}" ] || echo "${TRAEFIK_DASHBOARD_USERS}" | grep -qv '^admin:\$'; then
        warn "Python crypt.crypt failed. Installing apache2-utils for htpasswd..."
        apt-get install -y -qq apache2-utils 2>/dev/null \
            || dnf install -y httpd-tools 2>/dev/null \
            || yum install -y httpd-tools 2>/dev/null \
            || true
        if command -v htpasswd &>/dev/null; then
            TRAEFIK_DASHBOARD_USERS="$(htpasswd -nbB admin "${TRAEFIK_TMP_PW}")"
        else
            fatal "Cannot generate TRAEFIK_DASHBOARD_USERS. Set it manually in the environment."
        fi
    fi
    info "Traefik dashboard password: ${TRAEFIK_TMP_PW} (save this!)"
    export TRAEFIK_DASHBOARD_USERS
fi

# Prompt for required API keys (interactive mode) or collect them (CI mode)
if [ "$NON_INTERACTIVE" = true ]; then
    info "Non-interactive mode — validating required env vars..."
    prompt_required BOOTSTRAP_ADMIN_USERNAME "BOOTSTRAP_ADMIN_USERNAME (required)"
    prompt_required BOOTSTRAP_ADMIN_EMAIL    "BOOTSTRAP_ADMIN_EMAIL (required)"

    if [ -n "${MISSING_REQUIRED_VARS:-}" ]; then
        fatal "Missing required environment variables:${MISSING_REQUIRED_VARS}"
    fi

    if [ -z "${GROQ_API_KEY:-}" ] && [ -z "${OPENAI_API_KEY:-}" ]; then
        warn "Neither GROQ_API_KEY nor OPENAI_API_KEY is set. AI features will not work."
    fi
else
    echo ""
    echo -e "${BOLD}── Admin User Setup ──${NC}"
    prompt_required BOOTSTRAP_ADMIN_USERNAME "Admin username"
    prompt_required BOOTSTRAP_ADMIN_EMAIL    "Admin email"
    echo -e "${CYAN}  ℹ Admin password auto-generated: ${BOOTSTRAP_ADMIN_PASSWORD}${NC}"
    echo ""

    echo -e "${BOLD}── AI Provider Keys (at least one required) ──${NC}"
    echo -e "${CYAN}  ℹ Leave blank if you don't have a key yet; AI features will be disabled${NC}"
    prompt_optional GROQ_API_KEY         "  Groq API Key" ""
    prompt_optional OPENAI_API_KEY       "  OpenAI API Key" ""
    echo ""

    echo -e "${BOLD}── OAuth / Social Media (required for publishing) ──${NC}"
    echo -e "${CYAN}  ℹ Leave blank to skip; you can configure these later in .env${NC}"
    prompt_optional GOOGLE_CLIENT_ID     "  Google OAuth Client ID" ""
    prompt_optional GOOGLE_CLIENT_SECRET "  Google OAuth Client Secret" ""
    prompt_optional TIKTOK_CLIENT_KEY    "  TikTok Client Key" ""
    prompt_optional TIKTOK_CLIENT_SECRET "  TikTok Client Secret" ""
    echo ""

    echo -e "${BOLD}── Optional API Keys ──${NC}"
    prompt_optional YOUTUBE_API_KEY      "  YouTube Data API Key" ""
    prompt_optional PEXELS_API_KEY       "  Pexels API Key" ""
    prompt_optional ELEVENLABS_API_KEY   "  ElevenLabs API Key" ""
    prompt_optional STRIPE_SECRET_KEY    "  Stripe Secret Key" ""
    prompt_optional STRIPE_WEBHOOK_SECRET "  Stripe Webhook Secret" ""
    echo ""

    echo -e "${BOLD}── Production Domain ──${NC}"
    prompt_optional PRODUCTION_DOMAIN    "  Production Domain URL" "${PRODUCTION_DOMAIN}"
    prompt_optional CORS_ORIGINS         "  CORS Origins (comma-separated)" "${CORS_ORIGINS}"
    echo ""
fi

# ── Write .env file (template-based, injecting resolved values) ──────────────
write_env_file() {
    local env_file="${ETTA_INSTALL_DIR}/.env"
    local template="${ETTA_INSTALL_DIR}/.env.production.template"

    # Start with a header
    cat > "${env_file}" << ENVEOF
# =============================================================================
# ettametta — Generated by setup-server.sh at $(date -u +"%Y-%m-%dT%H:%M:%SZ")
# =============================================================================
ENVEOF

    # Append from template if it exists, then override with our resolved values
    if [ -f "$template" ]; then
        info "Reading .env.production.template and injecting values..."
        # Read the template, strip comments that are just instructions (keep
        # section headers), then append. We replace placeholder-like lines
        # with our resolved values in a second pass.
        cat "${template}" >> "${env_file}"
        echo "" >> "${env_file}"
        echo "# ── Resolved by setup-server.sh ──" >> "${env_file}"
    fi

    # Always append the critical resolved values so they take precedence
    # (later entries in .env override earlier ones for docker compose).
    cat >> "${env_file}" << ENVEOF

# ═══════════════════════════════════════════════════════════════════════════
# Auto-generated values (setup-server.sh)
# ═══════════════════════════════════════════════════════════════════════════
ENV=${ENV}
SECRET_KEY=${SECRET_KEY}
PRODUCTION_DOMAIN=${PRODUCTION_DOMAIN}
CORS_ORIGINS=${CORS_ORIGINS}
INTERNAL_API_TOKEN=${INTERNAL_API_TOKEN}
AI_CLUSTER_SECRET=${AI_CLUSTER_SECRET}
POSTGRES_USER=${POSTGRES_USER}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
DATABASE_URL=${DATABASE_URL}
REDIS_PASSWORD=${REDIS_PASSWORD}
REDIS_URL=${REDIS_URL}
TRAEFIK_DASHBOARD_USERS=${TRAEFIK_DASHBOARD_USERS}
GROQ_API_KEY=${GROQ_API_KEY:-}
OPENAI_API_KEY=${OPENAI_API_KEY:-}
GOOGLE_CLIENT_ID=${GOOGLE_CLIENT_ID:-}
GOOGLE_CLIENT_SECRET=${GOOGLE_CLIENT_SECRET:-}
TIKTOK_CLIENT_KEY=${TIKTOK_CLIENT_KEY:-}
TIKTOK_CLIENT_SECRET=${TIKTOK_CLIENT_SECRET:-}
YOUTUBE_API_KEY=${YOUTUBE_API_KEY:-}
PEXELS_API_KEY=${PEXELS_API_KEY:-}
ELEVENLABS_API_KEY=${ELEVENLABS_API_KEY:-}
TIKTOK_API_KEY=${TIKTOK_API_KEY:-}
RENDER_NODE_URL=${RENDER_NODE_URL:-}
STORAGE_PROVIDER=${STORAGE_PROVIDER}
AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID:-}
AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY:-}
AWS_REGION=${AWS_REGION:-us-east-1}
AWS_STORAGE_BUCKET_NAME=${AWS_STORAGE_BUCKET_NAME:-}
STRIPE_SECRET_KEY=${STRIPE_SECRET_KEY:-}
STRIPE_WEBHOOK_SECRET=${STRIPE_WEBHOOK_SECRET:-}
SHOPIFY_SHOP_URL=${SHOPIFY_SHOP_URL:-}
SHOPIFY_ACCESS_TOKEN=${SHOPIFY_ACCESS_TOKEN:-}
TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN:-}
TELEGRAM_ADMIN_ID=${TELEGRAM_ADMIN_ID:-}
CELERY_CONCURRENCY=${CELERY_CONCURRENCY}
BOOTSTRAP_ADMIN_USERNAME=${BOOTSTRAP_ADMIN_USERNAME:-}
BOOTSTRAP_ADMIN_EMAIL=${BOOTSTRAP_ADMIN_EMAIL:-}
BOOTSTRAP_ADMIN_PASSWORD=${BOOTSTRAP_ADMIN_PASSWORD:-}
BOOTSTRAP_ADMIN_ROLE=${BOOTSTRAP_ADMIN_ROLE}
BOOTSTRAP_ADMIN_SUBSCRIPTION=${BOOTSTRAP_ADMIN_SUBSCRIPTION}
BOOTSTRAP_INITIAL_CREDITS=${BOOTSTRAP_INITIAL_CREDITS}
AI_VIDEO_PROVIDER=${AI_VIDEO_PROVIDER:-none}
RUNWAY_API_KEY=${RUNWAY_API_KEY:-}
PIKA_API_KEY=${PIKA_API_KEY:-}
LUMA_API_KEY=${LUMA_API_KEY:-}
ENABLE_PERSISTED_ANALYSIS=${ENABLE_PERSISTED_ANALYSIS:-false}
ENVEOF

    ok ".env file written to ${env_file}"
}

if [ "$DRY_RUN" = false ]; then
    write_env_file
else
    info "[DRY-RUN] Would write .env to ${ETTA_INSTALL_DIR}/.env"
fi

# ── Print generated credentials so the operator can save them ────────────────
if [ "$NON_INTERACTIVE" = false ]; then
    echo ""
    echo -e "${BOLD}${YELLOW}╔══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BOLD}${YELLOW}║  SAVE THESE CREDENTIALS — not stored elsewhere           ║${NC}"
    echo -e "${BOLD}${YELLOW}╚══════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "  Admin username:  ${GREEN}${BOOTSTRAP_ADMIN_USERNAME}${NC}"
    echo -e "  Admin password:  ${GREEN}${BOOTSTRAP_ADMIN_PASSWORD}${NC}"
    echo -e "  Admin email:     ${GREEN}${BOOTSTRAP_ADMIN_EMAIL}${NC}"
    echo -e "  DB user:         ${GREEN}${POSTGRES_USER}${NC}"
    echo -e "  DB password:     ${GREEN}${POSTGRES_PASSWORD}${NC}"
    if [ -n "${TRAEFIK_TMP_PW:-}" ]; then
        echo -e "  Traefik dash:    ${GREEN}admin / ${TRAEFIK_TMP_PW}${NC}"
    fi
    echo ""
fi

# ═══════════════════════════════════════════════════════════════════════════
# STEP 6: Database Bootstrap + Alembic Migrations
# ═══════════════════════════════════════════════════════════════════════════
step "6/7 — Database Setup"

if [ "$DRY_RUN" = true ]; then
    info "[DRY-RUN] Would start DB, run bootstrap, and run alembic upgrade head"
else
    # Start database + redis so the api service's depends_on are satisfied.
    # docker compose validates ALL services against env vars (not just the
    # ones being started), so TRAEFIK_DASHBOARD_USERS must be set above.
    info "Starting PostgreSQL + Redis..."
    docker compose up -d db redis 2>&1 | tail -3

    # Wait for DB to be healthy
    info "Waiting for PostgreSQL to be ready..."
    for i in $(seq 1 30); do
        if docker compose exec -T db pg_isready -U "${POSTGRES_USER}" -d ettametta &>/dev/null; then
            ok "PostgreSQL is ready"
            break
        fi
        if [ "$i" -eq 30 ]; then
            fatal "PostgreSQL did not become ready within 30 seconds"
        fi
        sleep 1
    done

    # ── Run bootstrap_db.py ──────────────────────────────────────────────────
    # docker compose run creates a TEMPORARY api container (respects
    # depends_on: db + redis). This avoids needing an already-running api
    # container (docker compose exec requires one).
    info "Bootstrapping database (via docker compose run)..."
    if docker compose run --rm -T api python3 scripts/bootstrap_db.py 2>&1; then
        ok "Database bootstrapped successfully"
    else
        # Tables may already exist from a previous run. That's fine — alembic
        # handles the remaining schema changes.
        warn "bootstrap_db.py exited non-zero (tables may already exist); continuing..."
    fi

    # ── Run alembic upgrade head ─────────────────────────────────────────────
    info "Running alembic upgrade head..."
    if docker compose run --rm -T api alembic upgrade head 2>&1; then
        ok "Alembic migrations applied successfully"
    else
        fatal "Alembic migrations failed. Check database connectivity and migration state."
    fi
fi

# ═══════════════════════════════════════════════════════════════════════════
# STEP 7: Docker Compose Build + Start
# ═══════════════════════════════════════════════════════════════════════════
step "7/7 — Docker Compose Build & Start"

if [ "$DRY_RUN" = true ]; then
    info "[DRY-RUN] Would run: docker compose build && docker compose up -d"
else
    cd "${ETTA_INSTALL_DIR}"

    info "Building Docker images (this may take several minutes)..."
    if docker compose build --parallel 2>&1; then
        ok "Docker images built successfully"
    else
        warn "Some images failed to build. Attempting to start anyway..."
    fi

    info "Starting all services..."
    docker compose up -d 2>&1

    ok "Services starting up..."
    echo ""
    docker compose ps --format table 2>/dev/null || docker compose ps 2>/dev/null
    echo ""

    # ── Post-deploy health verification ────────────────────────────────────
    info "Waiting for services to become healthy (this may take 30-60s)..."

    # Determine the API port: check docker-compose for the host port
    API_PORT="7201"  # default from docker-compose.yml
    API_HOST="localhost"

    # Wait for API health endpoint
    HEALTHY=false
    for i in $(seq 1 60); do
        if curl -sf "http://${API_HOST}:${API_PORT}/health" &>/dev/null; then
            HEALTH_RESPONSE="$(curl -sf "http://${API_HOST}:${API_PORT}/health" 2>/dev/null)"
            HEALTHY=true
            break
        fi
        if [ "$((i % 5))" -eq 0 ]; then
            info "Still waiting for API... (${i}s)"
        fi
        sleep 1
    done

    if [ "$HEALTHY" = true ]; then
        ok "API is healthy: ${HEALTH_RESPONSE}"
    else
        warn "API health check timed out. Check logs: docker compose logs api --tail 50"
    fi

    # Verify docs/OpenAPI endpoints
    DOCS_CODE="$(curl -s -o /dev/null -w '%{http_code}' "http://${API_HOST}:${API_PORT}/docs" 2>/dev/null || echo "000")"
    OPENAPI_CODE="$(curl -s -o /dev/null -w '%{http_code}' "http://${API_HOST}:${API_PORT}/openapi.json" 2>/dev/null || echo "000")"
    info "API docs: ${DOCS_CODE}  |  OpenAPI: ${OPENAPI_CODE}"

    # ── Final summary ──────────────────────────────────────────────────────
    echo ""
    echo -e "${BOLD}${GREEN}╔══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BOLD}${GREEN}║  🚀  ettametta deployment complete!                      ║${NC}"
    echo -e "${BOLD}${GREEN}╚══════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "  API health:   ${GREEN}http://${API_HOST}:${API_PORT}/health${NC}"
    echo -e "  API docs:     ${CYAN}http://${API_HOST}:${API_PORT}/docs${NC}"
    echo -e "  Dashboard:    ${CYAN}http://${API_HOST}:7200${NC}"
    echo -e "  Traefik dash: ${CYAN}http://${API_HOST}:8080${NC}  (login: admin / see .env)"
    echo ""
    echo -e "  View logs:    ${YELLOW}cd ${ETTA_INSTALL_DIR} && docker compose logs -f${NC}"
    echo -e "  Stop:         ${YELLOW}cd ${ETTA_INSTALL_DIR} && docker compose down${NC}"
    echo -e "  Restart:      ${YELLOW}cd ${ETTA_INSTALL_DIR} && docker compose restart${NC}"
    echo ""
    echo -e "  ${BOLD}Services:${NC}"
    docker compose ps --format "table {{.Name}}\t{{.State}}\t{{.Health}}" 2>/dev/null \
        || docker compose ps 2>/dev/null
    echo ""
fi

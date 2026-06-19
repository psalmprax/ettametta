#!/usr/bin/env bash
# =============================================================================
# ettametta — Interactive .env Generator
# =============================================================================
# Reads .env.production.template, auto-discovers all required/optional
# variables, auto-generates secrets where sensible, and prompts the user
# for API keys and domain configuration.
#
# Usage:
#   ./scripts/generate-env.sh                    # Interactive mode
#   ./scripts/generate-env.sh --non-interactive  # CI mode (reads env vars)
#   ./scripts/generate-env.sh --dry-run          # Print what would be generated
#   ./scripts/generate-env.sh --output .env.staging  # Custom output path
# =============================================================================

set -euo pipefail

# ── Colors ───────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'
ok()   { echo -e "${GREEN}  ✓ ${1}${NC}"; }
info() { echo -e "${CYAN}  ℹ ${1}${NC}"; }
warn() { echo -e "${YELLOW}  ⚠ ${1}${NC}"; }

# ── Globals ──────────────────────────────────────────────────────────────────
TEMPLATE=".env.production.template"
OUTPUT=".env"
NON_INTERACTIVE=false
DRY_RUN=false

for arg in "$@"; do
    case "$arg" in
        --non-interactive) NON_INTERACTIVE=true ;;
        --dry-run)         DRY_RUN=true ;;
        --output)          OUTPUT="${2:-.env}"; shift ;;
        --help|-h)
            echo "Usage: $0 [--non-interactive] [--dry-run] [--output FILE]"
            exit 0 ;;
    esac
done

if [ ! -f "$TEMPLATE" ]; then
    echo "Template not found: $TEMPLATE"
    exit 1
fi

if [ "$DRY_RUN" = true ]; then
    warn "DRY RUN — no file will be written."
fi

# ── Secret Generator ─────────────────────────────────────────────────────────
gen_secret() {
    local length="${1:-32}"
    python3 -c "import secrets; print(secrets.token_urlsafe(${length}))" 2>/dev/null \
        || openssl rand -hex "$(( length * 3 / 4 + 1 ))" 2>/dev/null \
        || cat /dev/urandom 2>/dev/null | tr -dc 'a-zA-Z0-9' | fold -w "${length}" | head -n 1
}

# Generate Traefik htpasswd using Python crypt (SHA-512 fallback, universally supported)
gen_traefik_htpasswd() {
    local pw="${1:-$(gen_secret 16)}"
    # All Python code in single quotes — no bash variable expansion at all.
    # Password passed as argv[1].
    local result
    result="$(python3 -c '
import crypt, base64, os, sys
pw = sys.argv[1]
sb = "".join(c for c in base64.b64encode(os.urandom(16)).decode()[:22] if c in "./ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789")[:22]
h = crypt.crypt(pw, "$2b$10$" + (sb or "x"*22))
if not h or h.startswith("*") or h == pw:
    ss = base64.b64encode(os.urandom(6)).decode()[:8]
    h = crypt.crypt(pw, "$6$" + ss)
print(f"admin:{h}")
' "$pw" 2>/dev/null)" || true
    if [ -n "$result" ]; then
        echo "$result"
        return 0
    fi
    # Python crypt failed — try htpasswd if available
    if command -v htpasswd &>/dev/null; then
        htpasswd -nbB admin "$pw" 2>/dev/null && return 0
    fi
    # Ultimate fallback: install htpasswd
    apt-get install -y -qq apache2-utils 2>/dev/null \
        || dnf install -y httpd-tools 2>/dev/null \
        || yum install -y httpd-tools 2>/dev/null \
        || true
    if command -v htpasswd &>/dev/null; then
        htpasswd -nbB admin "$pw" 2>/dev/null && return 0
    fi
    # Cannot generate — return empty, caller handles
    return 1
}

# ── Prompt Helpers ───────────────────────────────────────────────────────────
prompt_user() {
    local var="$1" desc="$2" default="${3:-}"
    if [ "$NON_INTERACTIVE" = true ] || [ "$DRY_RUN" = true ]; then
        return 0
    fi
    local prompt_text="${var}"
    [ -n "$desc" ] && prompt_text="${prompt_text} — ${desc}"
    if [ -n "$default" ]; then
        echo -ne "  ${YELLOW}${prompt_text} [${default}]: ${NC}"
    else
        echo -ne "  ${YELLOW}${prompt_text}: ${NC}"
    fi
    read -r input
    if [ -n "$input" ]; then
        RESOLVED_VARS["$var"]="$input"
    elif [ -n "$default" ]; then
        RESOLVED_VARS["$var"]="$default"
    fi
}

# ── Main ─────────────────────────────────────────────────────────────────────
main() {
    # ── State ────────────────────────────────────────────────────────────────
    declare -A RESOLVED_VARS
    declare -A VAR_COMMENTS
    declare -a PROMPT_ORDER
    declare -a REQUIRED_VARS

    # ═══════════════════════════════════════════════════════════════════════════
    # PHASE 1: Parse the template to discover variables and their requirement level
    # ═══════════════════════════════════════════════════════════════════════════
    echo -e "${BOLD}${CYAN}Parsing template: ${TEMPLATE}${NC}"

    current_section=""
    current_section_name=""
    pending_comment=""

    while IFS= read -r line; do
        # Skip empty lines (but clear pending comment)
        if [ -z "$line" ]; then
            pending_comment=""
            continue
        fi

        # Track section headers: "# --- NAME (P0) ---"
        if [[ "$line" =~ ^#[[:space:]]*---[[:space:]]+(.+)[[:space:]]+\((P[0-3])\).*--- ]]; then
            current_section_name="${BASH_REMATCH[1]}"
            current_section="${BASH_REMATCH[2]}"
            info "Section: ${current_section_name} (${current_section})"
            pending_comment=""
            continue
        fi

        # Collect comment lines (for REQUIRED: annotations)
        if [[ "$line" =~ ^#[[:space:]]*(.+) ]]; then
            pending_comment="${BASH_REMATCH[1]}"
            continue
        fi

        # Parse KEY=VALUE lines
        if [[ "$line" =~ ^([A-Za-z_][A-Za-z0-9_]*)=(.*) ]]; then
            key="${BASH_REMATCH[1]}"
            val="${BASH_REMATCH[2]}"

            # Strip trailing inline comment (everything after " #")
            raw_val="$val"
            inline_comment=""
            if [[ "$val" =~ ^(.*)[[:space:]]+#[[:space:]]*(.*) ]]; then
                raw_val="${BASH_REMATCH[1]}"
                inline_comment="${BASH_REMATCH[2]}"
            fi
            # Trim trailing whitespace
            raw_val="${raw_val%"${raw_val##*[![:space:]]}"}"

            # Classify: is this REQUIRED?
            is_required=false
            if [[ "$pending_comment" =~ REQUIRED ]] || [[ "$inline_comment" =~ REQUIRED ]]; then
                is_required=true
            elif [ "$current_section" = "P0" ] && [ -z "$raw_val" ]; then
                is_required=true
            fi

            if [ "$is_required" = true ]; then
                REQUIRED_VARS+=("$key")
            fi

            # Build description
            desc=""
            [ -n "$pending_comment" ] && desc="$pending_comment"
            [ -n "$inline_comment" ] && desc="${desc:+${desc} — }${inline_comment}"
            VAR_COMMENTS["$key"]="$desc"

            # Auto-generate secrets for well-known variables
            if [[ "$key" =~ ^(SECRET_KEY|INTERNAL_API_TOKEN|POSTGRES_PASSWORD|REDIS_PASSWORD|AI_CLUSTER_SECRET|BOOTSTRAP_ADMIN_PASSWORD)$ ]]; then
                gen_len=32
                [ "$key" = "SECRET_KEY" ] && gen_len=48
                [ "$key" = "INTERNAL_API_TOKEN" ] && gen_len=36
                RESOLVED_VARS["$key"]="$(gen_secret "$gen_len")"
                ok "Auto-generated: ${key}"

            elif [[ "$raw_val" =~ \<generate ]]; then
                # Template has a generate-me placeholder
                RESOLVED_VARS["$key"]="$(gen_secret 32)"
                ok "Auto-generated: ${key} (from placeholder)"

            elif [ -n "$raw_val" ] && [ "$raw_val" != "${raw_val//\$\{/}" ]; then
                # Value contains ${VAR} references — defer resolution
                RESOLVED_VARS["$key"]="$raw_val"
                info "Deferred: ${key} (references other vars)"

            elif [ -n "$raw_val" ]; then
                # Use the template's default value
                RESOLVED_VARS["$key"]="$raw_val"
                info "Default: ${key}=${raw_val}"

            elif [ "$is_required" = true ] || [ -z "$raw_val" ]; then
                # Empty value — collect for prompting
                PROMPT_ORDER+=("$key")
            else
                RESOLVED_VARS["$key"]="$raw_val"
            fi

            pending_comment=""
        else
            pending_comment=""
        fi
    done < "$TEMPLATE"

    # ── Add docker-compose extras not in template ────────────────────────────
    for extra in REDIS_PASSWORD AI_CLUSTER_SECRET TRAEFIK_DASHBOARD_USERS \
                  BOOTSTRAP_ADMIN_USERNAME BOOTSTRAP_ADMIN_EMAIL \
                  BOOTSTRAP_ADMIN_PASSWORD BOOTSTRAP_ADMIN_ROLE \
                  BOOTSTRAP_ADMIN_SUBSCRIPTION BOOTSTRAP_INITIAL_CREDITS \
                  CELERY_CONCURRENCY; do
        if [[ ! -v RESOLVED_VARS["$extra"] ]]; then
            case "$extra" in
                REDIS_PASSWORD|AI_CLUSTER_SECRET|BOOTSTRAP_ADMIN_PASSWORD)
                    RESOLVED_VARS["$extra"]="$(gen_secret 32)"
                    ok "Auto-generated (docker-compose): ${extra}"
                    ;;
                TRAEFIK_DASHBOARD_USERS)
                    TRAEFIK_DASHBOARD_USERS="$(gen_traefik_htpasswd "$(gen_secret 16)" 2>/dev/null || true)"
                    if [ -n "$TRAEFIK_DASHBOARD_USERS" ]; then
                        RESOLVED_VARS["$extra"]="$TRAEFIK_DASHBOARD_USERS"
                        ok "Auto-generated: TRAEFIK_DASHBOARD_USERS"
                    else
                        warn "Could not generate TRAEFIK_DASHBOARD_USERS — set manually in .env"
                    fi
                    ;;
                CELERY_CONCURRENCY)
                    RESOLVED_VARS["$extra"]="${CELERY_CONCURRENCY:-2}" ;;
                BOOTSTRAP_ADMIN_ROLE)
                    RESOLVED_VARS["$extra"]="admin" ;;
                BOOTSTRAP_ADMIN_SUBSCRIPTION)
                    RESOLVED_VARS["$extra"]="premium" ;;
                BOOTSTRAP_INITIAL_CREDITS)
                    RESOLVED_VARS["$extra"]="1000" ;;
                *)
                    PROMPT_ORDER+=("$extra")
                    REQUIRED_VARS+=("$extra")
                    ;;
            esac
        fi
    done

    # ═══════════════════════════════════════════════════════════════════════════
    # PHASE 2: Prompt user for unresolved required variables
    # ═══════════════════════════════════════════════════════════════════════════
    if [ ${#PROMPT_ORDER[@]} -gt 0 ]; then
        echo ""
        echo -e "${BOLD}═══ Interactive Configuration ═══${NC}"
        echo -e "${CYAN}  Press Enter to accept defaults or leave blank to skip.${NC}"
        echo ""

        # First pass: required (REQUIRED or P0 empty)
        for key in "${PROMPT_ORDER[@]}"; do
            is_req=false
            for r in "${REQUIRED_VARS[@]}"; do
                [ "$r" = "$key" ] && { is_req=true; break; }
            done
            if [ "$is_req" = true ]; then
                desc="${VAR_COMMENTS["$key"]:-}"
                current="${RESOLVED_VARS["$key"]:-}"
                echo -e "  ${BOLD}${key}${NC} ${RED}[REQUIRED]${NC}"
                [ -n "$desc" ] && echo -e "    ${CYAN}${desc}${NC}"
                prompt_user "$key" "$desc" "$current"
            fi
        done

        # Second pass: optional
        echo ""
        echo -e "${BOLD}── Optional (press Enter to skip) ──${NC}"
        for key in "${PROMPT_ORDER[@]}"; do
            is_req=false
            for r in "${REQUIRED_VARS[@]}"; do
                [ "$r" = "$key" ] && { is_req=true; break; }
            done
            if [ "$is_req" = false ]; then
                desc="${VAR_COMMENTS["$key"]:-}"
                [ -n "$desc" ] && echo -e "    ${CYAN}${desc}${NC}"
                prompt_user "$key" "" ""
            fi
        done
    fi

    # ═══════════════════════════════════════════════════════════════════════════
    # PHASE 3: Derive composite variables
    # ═══════════════════════════════════════════════════════════════════════════
    # Derive DATABASE_URL and REDIS_URL — always recompute from their components
    # since the template values contain placeholder references.
    pg_user="${RESOLVED_VARS["POSTGRES_USER"]:-ettametta}"
    pg_pass="${RESOLVED_VARS["POSTGRES_PASSWORD"]:-}"
    RESOLVED_VARS["DATABASE_URL"]="postgresql://${pg_user}:${pg_pass}@db:5432/ettametta"
    ok "Derived: DATABASE_URL"

    redis_pass="${RESOLVED_VARS["REDIS_PASSWORD"]:-$(gen_secret 32)}"
    RESOLVED_VARS["REDIS_URL"]="redis://:${redis_pass}@redis:6379/0"
    ok "Derived: REDIS_URL"

    # Set remaining defaults
    [ -z "${RESOLVED_VARS["ENV"]:-}" ] && RESOLVED_VARS["ENV"]="production"
    [ -z "${RESOLVED_VARS["STORAGE_PROVIDER"]:-}" ] && RESOLVED_VARS["STORAGE_PROVIDER"]="LOCAL"
    [ -z "${RESOLVED_VARS["AWS_REGION"]:-}" ] && RESOLVED_VARS["AWS_REGION"]="us-east-1"
    [ -z "${RESOLVED_VARS["POSTGRES_USER"]:-}" ] && RESOLVED_VARS["POSTGRES_USER"]="ettametta"

    # ═══════════════════════════════════════════════════════════════════════════
    # PHASE 4: Write .env file
    # ═══════════════════════════════════════════════════════════════════════════
    echo ""
    echo -e "${BOLD}═══ Writing ${OUTPUT} ═══${NC}"

    write_env() {
        local out="$1"
        {
            echo "# ============================================================================="
            echo "# ettametta — Generated by generate-env.sh at $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
            echo "# Source: ${TEMPLATE}"
            echo "# ============================================================================="
            echo ""

            # Write sections in template order, substituting resolved values
            while IFS= read -r tline; do
                if [[ "$tline" =~ ^([A-Za-z_][A-Za-z0-9_]*)=(.*) ]]; then
                    local tk="${BASH_REMATCH[1]}"
                    if [[ -v RESOLVED_VARS["$tk"] ]]; then
                        echo "${tk}=${RESOLVED_VARS["$tk"]}"
                    else
                        echo "$tline"
                    fi
                else
                    echo "$tline"
                fi
            done < "$TEMPLATE"

            # Append docker-compose extras
            echo ""
            echo "# ── DOCKER-COMPOSE EXTRAS (auto-generated) ──"
            echo "AI_CLUSTER_SECRET=${RESOLVED_VARS["AI_CLUSTER_SECRET"]:-}"
            echo "TRAEFIK_DASHBOARD_USERS=${RESOLVED_VARS["TRAEFIK_DASHBOARD_USERS"]:-}"
            echo ""
            echo "# ── BOOTSTRAP ──"
            echo "BOOTSTRAP_ADMIN_USERNAME=${RESOLVED_VARS["BOOTSTRAP_ADMIN_USERNAME"]:-}"
            echo "BOOTSTRAP_ADMIN_EMAIL=${RESOLVED_VARS["BOOTSTRAP_ADMIN_EMAIL"]:-}"
            echo "BOOTSTRAP_ADMIN_PASSWORD=${RESOLVED_VARS["BOOTSTRAP_ADMIN_PASSWORD"]:-}"
            echo "BOOTSTRAP_ADMIN_ROLE=${RESOLVED_VARS["BOOTSTRAP_ADMIN_ROLE"]:-admin}"
            echo "BOOTSTRAP_ADMIN_SUBSCRIPTION=${RESOLVED_VARS["BOOTSTRAP_ADMIN_SUBSCRIPTION"]:-premium}"
            echo "BOOTSTRAP_INITIAL_CREDITS=${RESOLVED_VARS["BOOTSTRAP_INITIAL_CREDITS"]:-1000}"
            echo ""
            echo "# ── CELERY ──"
            echo "CELERY_CONCURRENCY=${RESOLVED_VARS["CELERY_CONCURRENCY"]:-2}"
        } > "$out"
    }

    if [ "$DRY_RUN" = true ]; then
        info "Would write to ${OUTPUT}"
        echo ""
        for k in $(for key in "${!RESOLVED_VARS[@]}"; do echo "$key"; done | sort); do
            v="${RESOLVED_VARS["$k"]}"
            if [[ "$k" =~ PASSWORD|SECRET|TOKEN|KEY ]]; then
                printf "  %-35s = [REDACTED:%d chars]\n" "$k" "${#v}"
            else
                printf "  %-35s = %s\n" "$k" "${v:0:60}"
            fi
        done
    else
        write_env "$OUTPUT"
        ok "Written to ${OUTPUT}"
    fi

    # ── Report missing required vars ─────────────────────────────────────────
    echo ""
    missing_count=0
    for r in "${REQUIRED_VARS[@]}"; do
        if [ -z "${RESOLVED_VARS["$r"]:-}" ]; then
            if [ "$missing_count" -eq 0 ]; then
                echo -e "${RED}${BOLD}⚠ Missing required variables:${NC}"
            fi
            echo -e "  ${YELLOW}${r}${NC} — ${VAR_COMMENTS["$r"]:-no description}"
            missing_count=$((missing_count + 1))
        fi
    done
    if [ "$missing_count" -gt 0 ]; then
        echo ""
        echo -e "${YELLOW}  Edit ${OUTPUT} to fill them in before starting the stack.${NC}"
    else
        ok "All required variables are set."
    fi

    echo ""
    echo -e "${GREEN}${BOLD}Done. Run: docker compose up -d${NC}"
}

main

# ettametta 🚀

Autonomous multi-platform viral content discovery, transformation, optimization, and publishing engine — powered by AI. Now with **Neural Security Sentinel** and **Consolidated AIWorker**.

## 📁 Project Structure

```
ettametta/
├── api/                  # FastAPI backend
├── apps/dashboard/       # Next.js 14 frontend
├── services/
│   ├── discovery/        # Multi-platform trend scanners
│   ├── video_engine/     # FFmpeg/MoviePy video processing
│   ├── nexus_engine/     # Thumbnail & content generation
│   └── monetization/     # Revenue tracking & optimization
├── alembic/              # Database migrations
├── terraform/            # OCI infrastructure as code
├── scripts/              # Automation & setup utilities
└── docker-compose.yml    # Local & production orchestration
```

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3.10+, FastAPI, Uvicorn |
| **Frontend** | Next.js 14, Tailwind CSS, Lucide Icons |
| **AI / LLM** | Groq (`llama-3.3-70b`), AIWorker Consolidation |
| **Video** | FFmpeg, MoviePy, Fast-Whisper |
| **Queue** | Celery + Redis |
| **Database** | PostgreSQL (primary), Redis (cache) |
| **Agent** | OpenClaw + Telegram (`@Psalmpraxbot`) |
| **Infra** | Oracle Cloud (Always-Free ARM), Terraform |
| **CI/CD** | Jenkins + GitHub Actions |

## 🚀 Quick Start

### 1. Clone & configure environment

```bash
git clone https://github.com/YOUR_USERNAME/ettametta.git
cd ettametta
cp .env.example .env
# Edit .env with your actual values (see Environment Variables below)
```

### 2. Run with Docker

```bash
docker-compose up -d --build
```

### 3. Access services

| Service | URL |
|---|---|
| API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| Dashboard | http://localhost:3000 |

## 🔐 Environment Variables

Copy `.env.example` to `.env` and fill in:

| Variable | Description | Where to get it |
|---|---|---|
| `GROQ_API_KEY` | Groq LLM API key | [console.groq.com](https://console.groq.com) |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token | [@BotFather](https://t.me/BotFather) on Telegram |
| `POSTGRES_PASSWORD` | PostgreSQL password | Set your own |
| `REDIS_PASSWORD` | Redis password | Set your own |
| `JWT_SECRET_KEY` | JWT signing secret | Run: `openssl rand -hex 32` |
| `OPENAI_API_KEY` | OpenAI API key (optional fallback) | [platform.openai.com](https://platform.openai.com) |

## ☁️ OCI Deployment (Terraform)

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your OCI credentials
terraform init
terraform plan
terraform apply
```

> ⚠️ **Never commit `terraform.tfvars`** — it contains real OCI credentials. It is gitignored by default.

OCI credentials needed in `terraform.tfvars`:

| Field | Where to find it |
|---|---|
| `tenancy_ocid` | OCI Console → Profile → Tenancy |
| `user_ocid` | OCI Console → Profile → User Settings |
| `fingerprint` | OCI Console → API Keys |
| `private_key_path` | Path to your `.pem` key file |
| `region` | Your OCI home region (e.g. `eu-frankfurt-1`) |

## 🔄 CI/CD (Jenkins)

The `Jenkinsfile` defines a full pipeline: lint → build → push → deploy → health check.

**Add these credentials in Jenkins → Manage Jenkins → Credentials → Global:**

| Credential ID | Type | Description |
|---|---|---|
| `GITHUB_CREDENTIALS` | Username + Password | GitHub username + Personal Access Token |
| `OCI_SSH_KEY` | SSH Private Key | Your OCI instance `.pem` key |
| `DOCKER_HUB_CREDENTIALS` | Username + Password | Docker Hub login |
| `GROQ_API_KEY` | Secret text | Groq API key |
| `TELEGRAM_BOT_TOKEN` | Secret text | Telegram bot token |
| `POSTGRES_PASSWORD` | Secret text | Production DB password |
| `REDIS_PASSWORD` | Secret text | Redis password |
| `JWT_SECRET_KEY` | Secret text | JWT secret (`openssl rand -hex 32`) |

**Edit the top variables in `Jenkinsfile` to match your setup:**
```groovy
def OCI_HOST    = "YOUR_OCI_IP"
def GITHUB_REPO = "YOUR_USERNAME/ettametta"
def DOCKER_IMAGE = "YOUR_DOCKERHUB_USER/ettametta"
```

## 🤖 OpenClaw Agent (Telegram)

The AI agent runs on the OCI server and is accessible via Telegram at `@Psalmpraxbot`.

```bash
# On OCI server — managed by systemd
sudo systemctl status openclaw-gateway
sudo systemctl restart openclaw-gateway

# Approve a new Telegram user
openclaw pairing approve telegram <PAIRING_CODE>
```

## 🧪 Testing (Playwright)

We use Playwright for end-to-end system verification. All tests are consolidated in `src/tests/e2e`.

### Run E2E Tests
```bash
cd src/tests/e2e
npm install
BASE_URL=http://localhost:3000 npx playwright test
```

### View Test Report
```bash
cd src/tests/e2e
npx playwright show-report
```

## 📝 Git Safety
- `.env` — **gitignored** (use `.env.example` as template)
- `terraform.tfvars` — **gitignored** (use `terraform.tfvars.example`)
- `terraform.tfstate` — **gitignored** (never commit state files)
- All secrets injected at deploy time via Jenkins credentials store

# ettametta Services Layer Architecture

This directory contains the core business logic and external integrations of the ettametta engine.

## Service Categories

### 🔍 **Discovery & Content Services**
| Service | Purpose | Key Features | Status |
|---------|---------|--------------|--------|
| `discovery/` | Find trending content | 16+ platforms, Redis cache, Groq expansion | ✅ Production |
| `opencli/` | Multi-platform publishing | 20+ platforms, session management | ✅ Production |
| `analytics/` | Performance tracking | YouTube API, retention analysis | ✅ Production |

### 🎬 **Video & Media Services**
| Service | Purpose | Key Features | Dependencies | Status |
|---------|---------|--------------|--------------|--------|
| `video_engine/` | Video processing | Multi-engine synthesis, GPU optimization | torch, cv2, moviepy | ⚠️ Needs deps |
| `voiceover/` | Text-to-speech | 3 engines (ElevenLabs, Fish Speech, gTTS) | httpx | ✅ Production |
| `stock_media/` | Video assets | Pexels API integration | httpx | ✅ Production |
| `visual_generator/` | Image creation | DALL-E 3 + Pollinations fallback | httpx | ✅ Production |

### 💰 **Monetization Services**
| Service | Purpose | Key Features | Status |
|---------|---------|--------------|--------|
| `monetization/` | Revenue strategies | 8 monetization channels, orchestrator | ✅ Production |
| `affiliate/` | Product links | Amazon/Impact/ShareASale integration | ✅ Production |

### 🤖 **AI & Processing Services**
| Service | Purpose | Key Features | Security | Status |
|---------|---------|--------------|----------|--------|
| `llm/` | Unified AI access | 6 providers, fallback chains | High | ✅ Production |
| `decision_engine/` | Content strategy | Pydantic models, screenplay generation | High | ✅ Production |
| `interpreter/` | Code execution | Process isolation, rate limiting | **Enhanced** | ✅ Production |
| `nexus_engine/` | Pipeline orchestration | Circuit breakers, WebSocket progress | High | ✅ Production |
| `script_generator/` | Content scripts | Templates, fallback generation | High | ✅ Production |

### 🔧 **Infrastructure Services**
| Service | Purpose | Key Features | Dependencies | Status |
|---------|---------|--------------|--------------|--------|
| `optimization/` | Publishing optimization | Rate limiting, retry logic | - | ✅ Production |
| `publisher_base/` | Social publishing | Abstract base, validation | - | ✅ Production |
| `storage/` | File management | S3/OCI/Local support | boto3 | ⚠️ Graceful degradation |
| `security/` | System monitoring | Integrity audits, threat detection | - | ✅ Production |

### 📊 **Optional/Experimental Services**
| Service | Purpose | Status | Notes |
|---------|---------|--------|-------|
| `langchain/` | Enhanced LLM chaining | ⚠️ Optional | Disabled by default |
| `crewai/` | Multi-agent orchestration | ⚠️ Optional | Disabled by default |

## Service Interaction Matrix

| Service | Primary Role | Cognitive Layer | Integrated Agents |
|---------|--------------|-----------------|-------------------|
| `nexus_engine` | Video Assembly Engine | LangChain (Vibe Check) | - |
| `decision_engine`| Strategy & Screenplay | - | CrewAI (Script Team) |
| `video_engine` | Low-level processing | - | - |
| `monetization` | Revenue Strategies | - | - |
| `discovery` | Content Discovery | - | - |

## Cognitive & Agentic Tiers

ettametta uses a tiered cognitive architecture:

1. **Standard Tier**: Uses direct LLM calls (Groq/OpenAI) for rapid decision making.
2. **Cognitive Tier (LangChain)**: Enhances the assembly pipeline with contextual memory and visual vibe analysis. (Enabled via `ENABLE_LANGCHAIN=true`)
3. **Agentic Tier (CrewAI)**: Spawns specialized multi-agent teams for high-fidelity content research and strategy. (Enabled via `ENABLE_CREWAI=true`)

## Security Features

- **Process Isolation**: Interpreter service uses subprocess execution
- **Rate Limiting**: API calls and code execution are rate-limited
- **Input Validation**: Comprehensive security checks on all inputs
- **Circuit Breakers**: Automatic failover for external service failures
- **Audit Logging**: Security events tracked in Redis

## Testing & Verification

Each service includes built-in circuit breakers and retry logic (tenacity). Verification is performed via `src/tests/`:

- **Unit Tests**: Located in `src/tests/unit/`, providing isolated, robust verification of payment/credit services, DAG compiler engine, centralized circuit breaker, and multi-platform publishing logic with 100% pass rate.
- **Integration & E2E Tests**: Verify system-level orchestration and end-to-end video processing pipelines.

### Test Coverage by Service
- ✅ LLM Service: Provider enum, initialization, fallback logic
- ✅ Script Generator: Template generation, fallback scripts
- ✅ Decision Engine: Pydantic models, screenplay generation
- ✅ Monetization: Orchestrator failover, affiliate links
- ✅ Security: Sentinel audits, rate limiting
- ✅ Interpreter: Process isolation, keyword blocking
- ✅ Analytics: Metrics calculation, retention analysis
- ✅ Video Engine: Effect delegation, rate limiting
- ✅ OpenCLI: Platform capabilities, session management

## Performance & Resilience Metrics

- **Service Initialization**: 15/18 services (83% with graceful degradation)
- **Test Suite Status**: 100% of unit tests passing, covering DAG execution, payment/credits, centralized circuit breaker, and publishing services.
- **Circuit Breakers**: Centralized resilience engine (`src/api/utils/resilience.py`) protecting external integration points.
- **Error Handling**: Robust retry policies configured with tenacity and fallback mechanisms for social publishing.

## Architecture Principles

1. **Graceful Degradation**: Services work with missing optional dependencies
2. **Circuit Breaker Pattern**: All external API calls protected
3. **Process Isolation**: Security-critical operations isolated
4. **Resilience & Testing**: 100% test pass rate with fully mocked external dependencies and centralized circuit breakers.
5. **Clear Documentation**: Each service fully documented with examples

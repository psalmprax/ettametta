# Agent Framework Hybrid Implementation Plan

**Date:** February 24, 2026  
**Goal:** Implement missing agent frameworks using hybrid approach (optional, disabled by default)

---

## Missing Tools from ai_stack_comparison

| Tool | Purpose | Priority | Hybrid Approach |
|------|---------|----------|-----------------|
| **LangChain** | LLM chaining & prompt management | High | Wrapq with Lang existing GroChain |
| **CrewAI** | Multi-agent orchestration | Medium | Add as optional agent layer |
| **Open Interpreter** | Code execution | Medium | Add as optional execution engine |
| **Affiliate APIs** | Programmatic affiliate access | High | Add affiliate network integration |
| **Trading APIs** | Market analysis & trading | Low | Add as optional module |

---

## Architecture: Hybrid Agent System

```
┌─────────────────────────────────────────────────────────────────┐
│                      OPENCLAW (Current)                         │
│                   (Telegram Controller - Always On)              │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│   BASIC    │      │  LANCHAIN   │      │   CREWAI    │
│   (current)│      │  ENABLED    │      │   ENABLED   │
└─────────────┘      └─────────────┘      └─────────────┘
        │                     │                     │
   Direct Groq          Prompt             Multi-agent
   calls              templates            orchestration
```

---

## Phase A1: LangChain Integration

### Purpose
Enhance existing Groq integration with proper LLM chaining, memory, and prompt management.

### Implementation
```python
# services/langchain/__init__.py
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, SystemMessage
from langchain_community.chat_models import ChatGroq

class LangChainService:
    """Optional LangChain enhancement - disabled by default"""
    
    def __init__(self):
        self.enabled = os.getenv("ENABLE_LANGCHAIN", "false").lower() == "true"
        # Use existing Groq as backend
        self.llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            api_key=settings.GROQ_API_KEY
        )
    
    async def chain_prompt(self, prompt: str, context: dict) -> str:
        """Use LangChain for structured prompting"""
        # Implementation...
```

### Config
```bash
# .env
ENABLE_LANGCHAIN=false
```

---

## Phase A2: CrewAI Integration

### Purpose
Add multi-agent orchestration for complex workflows.

### Implementation
```python
# services/crewai/__init__.py
from crewai import Agent, Task, Crew

class CrewAIService:
    """Optional CrewAI enhancement - disabled by default"""
    
    def __init__(self):
        self.enabled = os.getenv("ENABLE_CREWAI", "false").lower() == "true"
    
    async def run_content_team(self, topic: str):
        """Run content creation team"""
        # Define agents
        researcher = Agent(role="Researcher", goal="Find trends")
        writer = Agent(role="Writer", goal="Write scripts")
        
        # Define tasks
        research_task = Task(description=f"Research {topic}")
        write_task = Task(description=f"Write script about findings")
        
        # Create crew
        crew = Crew(agents=[researcher, writer], tasks=[research_task, write_task])
        
        return crew.kickoff()
```

### Config
```bash
# .env
ENABLE_CREWAI=false
CREWAI_AGENTS=researcher,writer,editor
```

---

## Phase A3: Affiliate API Integration

### Purpose
Programmatic access to affiliate networks.

### Implementation
```python
# services/affiliate/__init__.py
class AffiliateService:
    """Optional affiliate API integration"""
    
    def __init__(self):
        self.enabled = os.getenv("ENABLE_AFFILIATE_API", "false").lower() == "true"
        self.amazon_tag = os.getenv("AMAZON_ASSOCIATES_TAG", "")
    
    async def search_products(self, niche: str) -> List[dict]:
        """Search affiliate products by niche"""
        # Amazon Product API
        # Impact Radius
        # ShareASale
```

### Config
```bash
# .env
ENABLE_AFFILIATE_API=false
AMAZON_ASSOCIATES_TAG=your_tag
IMPACT_RADIUS_API_KEY=
SHAREASALE_API_KEY=
```

---

## Phase A4: Open Interpreter (Optional)

### Purpose
Enable code execution for dynamic video generation.

### Implementation
```python
# services/interpreter/__init__.py
class InterpreterService:
    """Optional Open Interpreter for code execution"""
    
    def __init__(self):
        self.enabled = os.getenv("ENABLE_INTERPRETER", "false").lower() == "true"
    
    async def execute_code(self, code: str) -> str:
        """Execute code for custom processing"""
        # Open Interpreter integration
```

---

## Phase A5: Trading APIs (Optional)

### Purpose
Add market analysis and trading automation.

### Implementation
```python
# services/trading/__init__.py
class TradingService:
    """Optional trading API integration"""
    
    def __init__(self):
        self.enabled = os.getenv("ENABLE_TRADING", "false").lower() == "true"
    
    async def get_market_sentiment(self, symbol: str) -> dict:
        """Get market sentiment for symbol"""
        # Alpha Vantage
        # CoinGecko (crypto)
    
    async def analyze_trends(self, niche: str) -> dict:
        """Analyze trading trends for niche"""
```

---

## Integration with OpenClaw

Update OpenClaw to optionally use these services:

```python
# In OpenClaw agent
if settings.ENABLE_LANGCHAIN:
    from services.langchain import langchain_service
    # Use LangChain for prompts

if settings.ENABLE_CREWAI:
    from services.crewai import crewai_service
    # Use CrewAI for complex tasks
```

---

## Environment Configuration

```bash
# Agent Framework Enablement
ENABLE_LANGCHAIN=false
ENABLE_CREWAI=false
ENABLE_INTERPRETER=false

# Affiliate & Trading
ENABLE_AFFILIATE_API=false
ENABLE_TRADING=false

# API Keys (when enabled)
AMAZON_ASSOCIATES_TAG=
IMPACT_RADIUS_API_KEY=
ALPHA_VANTAGE_API_KEY=
COINGECKO_API_KEY=
```

---

## Implementation Order

| Phase | Feature | Effort | Priority |
|-------|---------|--------|----------|
| A1 | LangChain Integration | 2 days | High |
| A2 | CrewAI Integration | 3 days | Medium |
| A3 | Affiliate API | 3 days | High |
| A4 | Open Interpreter | 4 days | Medium |
| A5 | Trading APIs | 5 days | Low |

---

## Backward Compatibility

- All new services disabled by default
- OpenClaw continues to work without changes
- Gradual adoption: enable one service at a time
- No breaking changes to existing API

---

*Agent framework hybrid implementation plan - extends video pipeline approach to agent tools*

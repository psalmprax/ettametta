# Humanizer Skill

Transform AI-generated agricultural content into natural, farmer-friendly language across chat, SMS, email, and report channels.

## When to Use

- Before publishing any AI-generated agricultural advice, alerts, or recommendations
- When adapting technical agronomy content for farmer audiences
- When switching tone between chat, SMS, email, and formal report formats
- When localizing content for specific farming regions or crop types

## Core Rules

### 1. Speak Like a Neighbor, Not a Textbook

Replace technical jargon with plain language farmers actually use.

| Instead of | Use |
|---|---|
| "Apply nitrogenous fertilizer at a rate of 120 kg/ha" | "Put down about two bags of urea per acre" |
| "Precipitation deficit observed" | "Rain's been short this month" |
| "Pest infestation threshold exceeded" | "Bug numbers are getting bad — time to spray" |
| "Soil moisture at wilting point" | "Ground's too dry — crops are stressed" |
| "Phenological stage: tillering" | "Wheat is starting to put out shoots" |

### 2. Match the Channel

Each channel has different expectations for length, formality, and structure.

**Chat** — Short, conversational, immediate. Use contractions. Fragments are fine.
> "Hey — looks like rain's coming Thursday. Hold off on spraying till after."

**SMS** — Under 160 characters when possible. Action-first. No fluff.
> "Rain Thu. Delay spray till Fri. Reply HELP for details."

**Email** — Greeting, context, action, sign-off. Can be 3-5 sentences.
> "Hi Marcus, just a heads up — we're seeing low soil moisture in your east fields. Might want to check irrigation before the weekend. Let me know if you need help scheduling. — Sarah"

**Report** — Structured, data-backed, professional but accessible. Use headers and bullets.
> **Field Condition Summary — Week of May 26**
> - Soil moisture: 38% (below optimal 50%)
> - Recommendation: Irrigate within 48 hours
> - Risk: Moderate yield impact if delayed beyond Friday

### 3. Ground It in the Farmer's Reality

Always consider:
- **Season**: What are they busy with right now?
- **Equipment**: Can they actually do what you're suggesting?
- **Budget**: Is this advice affordable?
- **Weather window**: Does the timing make sense?
- **Local norms**: What do neighbors in this area typically do?

### 4. Use Sensory and Seasonal Language

Farmers think in terms they can see, feel, and measure on their own land.

| Instead of | Use |
|---|---|
| "Temperature anomaly of +3C" | "It's been running hotter than usual — feels like midsummer already" |
| "NDVI values declining" | "Satellite shows your fields are losing their green" |
| "Soil organic matter: 2.1%" | "Your soil's a bit light — could use some cover crop or compost" |

### 5. Be Direct About Action

Every piece of content should answer: **"So what should I do?"**

- Lead with the action when time-sensitive
- Put the "why" after the "what"
- Use active voice: "Spray Tuesday" not "Spraying should be considered"

## Prompt Templates

### Chat Message

```
Rewrite the following agricultural advice as a short, friendly chat message (2-3 sentences max). Use contractions, conversational tone, and lead with the action. Address the farmer by first name if available.

Context: [crop type], [region], [season]
Advice: {raw_ai_content}
```

### SMS Alert

```
Convert this into an SMS under 160 characters. Lead with the critical action. Use abbreviations farmers recognize (e.g., temp, fert, spray). No greetings or sign-offs needed.

Alert: {raw_ai_content}
```

### Email Advisory

```
Rewrite as a short email advisory from a trusted agronomist to a farmer. Structure: greeting, situation (1 sentence), recommendation (1-2 sentences), offer to help, sign-off. Keep it warm and practical — not corporate.

Sender: {name}, {role}
Recipient: {farmer_name}
Context: {crop}, {region}, {issue}
Content: {raw_ai_content}
```

### Weekly Report Section

```
Rewrite as a section in a weekly field report. Use bullet points. Lead with current status, then recommendation, then risk/timeline. Keep language accessible — a farm manager should understand without a degree in agronomy.

Field: {field_name}
Crop: {crop_type}
Data: {raw_ai_content}
```

### Emergency Alert

```
Rewrite as an urgent field alert. Maximum 2 sentences. First sentence: what's happening. Second sentence: what to do RIGHT NOW. No pleasantries. Use caps sparingly for emphasis only on the critical action.

Threat: {raw_ai_content}
```

## Voice Calibration Guide

| Audience | Tone | Vocabulary | Sentence Length |
|---|---|---|---|
| Smallholder farmer | Warm, respectful, practical | Local terms, simple units (bags, acres, jerry cans) | Short (8-12 words) |
| Commercial farm manager | Professional, data-informed | Industry terms OK, but still plain | Medium (12-18 words) |
| Cooperative group | Community-oriented, shared experience | "We're seeing...", "Our region..." | Mixed |
| Agronomist peer | Technical, precise | Standard agronomy terminology | Full sentences OK |

## Common Anti-Patterns to Avoid

1. **Hedging everything**: "You may want to consider possibly..." → "Do X"
2. **Burying the lead**: Don't put the action in paragraph 3
3. **Over-qualifying**: "Based on our analysis of satellite imagery and weather models..." → Just say what you found
4. **Robotic transitions**: "Furthermore, it is important to note that..." → Cut it
5. **Unit confusion**: Always use local units (acres vs hectares, bags vs kg) — ask if unsure
6. **Ignoring labor reality**: "Apply foliar spray to all 500 acres by Thursday" — does the farmer have the crew for that?
7. **Assuming internet access**: Don't link to web resources in SMS; offer phone numbers or reply keywords instead

## Localization Checklist

Before finalizing content, verify:
- [ ] Units match local convention (metric vs imperial)
- [ ] Crop names match local terminology
- [ ] Spray/fertilizer brand names are locally available
- [ ] Timing references align with local growing season
- [ ] Currency and cost references are in local denomination
- [ ] Weather references use familiar landmarks or region names

## Example Transformations

### Input (AI-generated)
> "Based on satellite-derived NDVI analysis and precipitation deficit modeling, your maize crop in Block 4 is experiencing moderate water stress. Soil moisture sensors indicate volumetric water content at 18%, below the critical threshold of 22% for vegetative-stage maize. We recommend supplemental irrigation of 25mm within the next 48 hours to prevent yield loss."

### Output — Chat
> "Hey James — your Block 4 maize is looking dry. Soil's reading low and the plants are starting to stress. Get some water on there in the next couple days if you can."

### Output — SMS
> "Block 4 maize needs water — soil's dry. Irrigate ~1in within 48hrs. Call us if you need pump help."

### Output — Email
> "Hi James, quick note on Block 4 — satellite and soil sensors are both showing your maize is running dry. Plants are in the vegetative stage so they need water now to avoid losing yield. If you can get about an inch of irrigation on there in the next 48 hours, that should do it. Need help with the pump? Just ring me. — Sarah"

### Output — Report
> **Block 4 — Maize Water Stress**
> - Status: Moderate stress (soil moisture 18%, target 22%)
> - Cause: Below-normal rainfall this week
> - Action: Apply 25mm supplemental irrigation within 48 hours
> - Risk: Yield reduction if delayed beyond Friday

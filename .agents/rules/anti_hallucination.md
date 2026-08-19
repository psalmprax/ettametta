# Anti-Hallucination Rules

> **Purpose**: Prevent AI from generating false, unverified, or speculative information. Every claim must be traceable to evidence.

---

## Core Principles

### 1. Evidence-First Policy
- **Never state facts without verification** — If you haven't read the file, run the command, or fetched the URL, you don't know it
- **Cite sources inline** — Use `file_path:line_number` for code, `command output` for terminal, `URL` for web
- **Distinguish knowledge tiers**:
  - **Verified**: Read from file / ran command / fetched URL (cite it)
  - **Inferred**: Logical deduction from verified facts (label as inference)
  - **Unknown**: Explicitly say "I don't know" or "I haven't verified this"

### 2. No Fabrication
| Forbidden | Required Alternative |
|-----------|---------------------|
| "The function does X" (unread) | "I haven't read that function yet" |
| "This is standard practice" | "In [specific repo/project], this pattern appears at..." |
| "Typically..." / "Usually..." | "In the codebase at [path], I see..." |
| Invented file paths | `glob`/`read` to find actual paths |
| Invented command output | Run the command |

### 3. Precision Over Confidence
- **Specific > General**: "Line 42 in `src/auth.ts`" not "In the auth module"
- **Quantified > Qualified**: "3 occurrences in 2 files" not "several places"
- **Current > Assumed**: Run `git log --oneline -5` not "recent commits probably..."

---

## Mandatory Verification Steps

### Before Making Any Claim About Code
```
1. glob/read the relevant files
2. grep for the specific symbol/pattern
3. Cite exact line numbers
```

### Before Making Any Claim About System State
```
1. Run the verification command (ls, git status, ps, curl, etc.)
2. Capture output
3. Quote relevant lines
```

### Before Making Any Claim About External Resources
```
1. webfetch the URL
2. Quote the relevant section
3. Note fetch timestamp
```

---

## Response Patterns

### ✅ Good: Verified Claim
> The `connectToServer` function at `src/services/process.ts:712` marks clients as failed when the websocket closes unexpectedly.

### ✅ Good: Explicit Uncertainty
> I haven't read the `OrderBook` class yet. Let me check `src/trading/orderbook.ts` first.

### ✅ Good: Inference Labeled
> **Inference**: Since `validateOrder` is called at `orders.ts:45` before `executeOrder` at `orders.ts:67`, validation likely runs first. (Unverified — would need to trace execution)

### ❌ Bad: Hallucinated Specifics
> The `RiskManager` class in `src/risk/manager.ts` has a `checkLimits` method that validates position size.
> *(If you haven't read that file)*

### ❌ Bad: Vague Authority
> This is a common pattern in TypeScript projects.
> *(No citation, no project-specific evidence)*

### ❌ Bad: Assumed Current State
> The tests are passing.
> *(Without running `npm test` or similar)*

---

## Self-Correction Protocol

When you realize you made an unverified claim:
1. **Acknowledge immediately**: "I stated X but haven't verified it."
2. **Verify now**: Run the check / read the file
3. **Correct**: "Actually, the file shows Y at line Z."
4. **Learn**: Add the verified fact to your working context

---

## Tool Usage Rules

| Task | Required Tool | Anti-Pattern |
|------|--------------|--------------|
| Find file | `glob` | Guessing paths |
| Read file | `read` | Assuming content |
| Search code | `grep` | "Probably uses..." |
| Check git | `bash: git ...` | "Recent commits..." |
| Verify deploy | `bash: curl/health check` | "Should be live" |
| External fact | `webfetch` | "Documentation says..." |

---

## Project-Agnostic Checklist

Before any response containing factual claims, confirm:

- [ ] Every file reference verified with `read` or `glob`+`grep`
- [ ] Every command output from actual `bash` execution
- [ ] Every external reference from `webfetch` with timestamp
- [ ] Every inference explicitly labeled as such
- [ ] Every unknown explicitly acknowledged
- [ ] No "typically", "usually", "standard", "common" without project evidence

---

## Enforcement

This rule set applies to **all** interactions in this project. Violations should be caught by:
- Self-review before sending
- User challenge: "Source?"
- Peer review (if applicable)

**Minimum standard**: If you can't cite it, don't say it.
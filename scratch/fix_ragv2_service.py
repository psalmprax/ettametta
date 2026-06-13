#!/usr/bin/env python3
"""Fix ragV2Service.ts inside the ag-dashboard-backend container."""

path = "/app/src/services/ragV2Service.ts"
with open(path) as f:
    c = f.read()

changes = 0

# 1. Add keywordScore method before rerank
marker1 = "    static async rerank("
if marker1 in c and "keywordScore" not in c:
    kw_method = """    // Lightweight keyword-overlap scorer
    private static keywordScore(queryText: string, content: string): number {
        const queryTokens = new Set(queryText.toLowerCase().split(/\\s+/).filter((w: string) => w.length > 2));
        const contentLower = content.toLowerCase();
        let matches = 0;
        for (const token of queryTokens) {
            if (contentLower.includes(token)) matches++;
        }
        return queryTokens.size > 0 ? matches / queryTokens.size : 0;
    }

"""
    c = c.replace(marker1, kw_method + marker1, 1)
    changes += 1
    print("1/4: Added keywordScore method")
else:
    print("1/4: SKIP (already present or marker not found)")

# 2. Reduce candidates from 15 to 6
if "results.slice(0, 15)" in c:
    c = c.replace("results.slice(0, 15)", "results.slice(0, 6)")
    changes += 1
    print("2/4: Reduced candidates to 6")
else:
    print("2/4: SKIP (already done or marker not found)")

# 3. Add keyword baseline before try block in rerank
marker3 = "        try {\n            const prompt = `You are a relevance scorer."
if marker3 in c and "keywordScore(queryText, c.content)" not in c:
    baseline = """
        // Apply keyword-overlap baseline scores
        for (const c of candidates) {
            c.rerankScore = RAGV2Service.keywordScore(queryText, c.content);
        }

        // Try LLM re-ranking with 5s timeout
"""
    c = c.replace(marker3, baseline + "        " + "try {\n            const prompt = `You are a relevance scorer.", 1)
    changes += 1
    print("3/4: Added keyword baseline")
else:
    print("3/4: SKIP (already present or marker not found)")

# 4. Wrap LLM call in Promise.race with 5s timeout
marker4 = "            const result = await AIRouter.routeRequest('generate', {\n                prompt,\n                options: { temperature: 0, maxTokens: 500 }\n            });"
if marker4 in c and "Promise.race" not in c:
    wrapped = """            const llmPromise = AIRouter.routeRequest('generate', {
                prompt,
                options: { temperature: 0, maxTokens: 300 }
            });
            const timeoutPromise = new Promise<never>((_, reject) =>
                setTimeout(() => reject(new Error('LLM re-ranking timed out (5s)')), 5000)
            );
            const result = await Promise.race([llmPromise, timeoutPromise]);"""
    c = c.replace(marker4, wrapped, 1)
    changes += 1
    print("4/4: Added 5s Promise.race timeout")
else:
    print("4/4: SKIP (already present or marker not found)")

with open(path, "w") as f:
    f.write(c)

print(f"\nDone! {changes} changes applied to {path}")

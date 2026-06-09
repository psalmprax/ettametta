#!/usr/bin/env node
/**
 * Fix ragV2Service.ts: add keywordScore, 5s timeout, reduce candidates
 * Run inside the ag-dashboard-backend container with: node /tmp/fix_ragv2.js
 */
const fs = require('fs');
const path = '/app/src/services/ragV2Service.ts';
let c = fs.readFileSync(path, 'utf8');
let changes = 0;

// 1. Add keywordScore method before rerank
const marker1 = '    static async rerank(';
if (c.includes(marker1) && !c.includes('keywordScore')) {
    const kwMethod = `    // Lightweight keyword-overlap scorer
    private static keywordScore(queryText: string, content: string): number {
        const queryTokens = new Set(queryText.toLowerCase().split(/\\s+/).filter((w: string) => w.length > 2));
        const contentLower = content.toLowerCase();
        let matches = 0;
        for (const token of queryTokens) {
            if (contentLower.includes(token)) matches++;
        }
        return queryTokens.size > 0 ? matches / queryTokens.size : 0;
    }

`;
    c = c.replace(marker1, kwMethod + marker1);
    changes++;
    console.log('1/4: Added keywordScore method');
} else {
    console.log('1/4: SKIP (already present or marker not found)');
}

// 2. Reduce candidates from 15 to 6
if (c.includes('results.slice(0, 15)')) {
    c = c.replace('results.slice(0, 15)', 'results.slice(0, 6)');
    changes++;
    console.log('2/4: Reduced candidates to 6');
} else {
    console.log('2/4: SKIP (already done or marker not found)');
}

// 3. Add keyword baseline before try block
const marker3 = "        try {\n            const prompt = `You are a relevance scorer.";
if (c.includes(marker3) && !c.includes('keywordScore(queryText, c.content)')) {
    const baseline = `
        // Apply keyword-overlap baseline scores
        for (const c of candidates) {
            c.rerankScore = RAGV2Service.keywordScore(queryText, c.content);
        }

        // Try LLM re-ranking with 5s timeout
`;
    c = c.replace(marker3, baseline + '        ' + "try {\n            const prompt = `You are a relevance scorer.");
    changes++;
    console.log('3/4: Added keyword baseline');
} else {
    console.log('3/4: SKIP (already present or marker not found)');
}

// 4. Wrap LLM call in Promise.race with 5s timeout
const marker4 = "            const result = await AIRouter.routeRequest('generate', {\n                prompt,\n                options: { temperature: 0, maxTokens: 500 }\n            });";
if (c.includes(marker4) && !c.includes('Promise.race')) {
    const wrapped = `            const llmPromise = AIRouter.routeRequest('generate', {
                prompt,
                options: { temperature: 0, maxTokens: 300 }
            });
            const timeoutPromise = new Promise<never>((_, reject) =>
                setTimeout(() => reject(new Error('LLM re-ranking timed out (5s)')), 5000)
            );
            const result = await Promise.race([llmPromise, timeoutPromise]);`;
    c = c.replace(marker4, wrapped);
    changes++;
    console.log('4/4: Added 5s Promise.race timeout');
} else {
    console.log('4/4: SKIP (already present or marker not found)');
}

fs.writeFileSync(path, c);
console.log(`\nDone! ${changes} changes applied to ${path}`);

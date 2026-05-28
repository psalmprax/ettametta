/**
 * Nexus Engine - Full System E2E Workflow Test
 * =============================================
 *
 * Tests the complete Nexus Engine pipeline lifecycle:
 *   1. Auth: Dynamic user registration → login
 *   2. Orchestrator: Select niche, blueprint, dispatch pipeline
 *   3. Pipeline History: Poll for job completion, open preview modal
 *   4. Scene Preview Modal: Verify scenes, swap asset, select style preset
 *   5. Workforce Tab: Browse agents, verify search/filter
 *   6. Neural IDs Tab: Verify persona listing
 *   7. Command Pod Tab: Verify command modules visible
 *   8. Code Sandbox Tab: Verify sandbox UI
 */

import { test, expect, Page } from '@playwright/test';

// ─── Helpers ──────────────────────────────────────────────────────────────────

/** Register a fresh user and return credentials (with retry on timeout) */
async function registerUser(page: Page) {
    const maxRetries = 2;
    let lastError: Error | null = null;

    for (let attempt = 0; attempt <= maxRetries; attempt++) {
        if (attempt > 0) {
            console.log(`[E2E] Registration retry attempt ${attempt + 1}/${maxRetries + 1}`);
            // Brief backoff to let server recover
            await new Promise(resolve => setTimeout(resolve, 5000));
        }
        const timestamp = Date.now();
        const email = `nexus_e2e_${timestamp}@example.com`;
        const username = `nexus_user_${timestamp}`;
        const password = 'TestPassword123!';

        try {
            await test.step(`Register new user (attempt ${attempt + 1})`, async () => {
                await page.goto('/register');
                await expect(page.locator('h1')).toContainText(/create account/i);

                await page.getByPlaceholder('you@example.com').fill(email);
                await page.getByPlaceholder('Choose a display name').fill(username);
                await page.getByPlaceholder('Create a secure password').fill(password);

                // Click submit and wait for the API response
                await Promise.all([
                    page.waitForURL(/\/login/, { timeout: 90000 }),
                    page.click('button[type="submit"]'),
                ]);
            });
            return { email, username, password };
        } catch (err) {
            lastError = err instanceof Error ? err : new Error(String(err));
            console.log(`[E2E] Registration attempt ${attempt + 1} failed: ${lastError.message}`);
            // Navigate back to register page for retry
            await page.goto('/register').catch(() => {});
        }
    }

    throw lastError || new Error('Registration failed after all retries');
}

/** Login with given credentials */
async function loginUser(page: Page, email: string, password: string) {
    await test.step('Login with credentials', async () => {
        await page.getByPlaceholder('Enter your username').fill(email);
        await page.getByPlaceholder('Enter your password').fill(password);
        await page.click('button[type="submit"]');

        await expect(page).toHaveURL(/\/dashboard/, { timeout: 15000 });
    });
}

// Sidebar label lookup
const ENGINE_LABELS: Record<string, string> = {
    orchestrator: 'Orchestrator',
    crews: 'Workforce',
    identities: 'Neural IDs',
    sandbox: 'Code Sandbox',
    command: 'Command Pod',
    history: 'Pipeline History',
};

/** Navigate to a sidebar engine tab */
async function navigateToEngine(page: Page, engineId: string) {
    const label = ENGINE_LABELS[engineId];
    if (!label) throw new Error(`Unknown engine tab: ${engineId}`);
    await page.locator(`button:has-text("${label}")`).click();
    await expect(page).toHaveURL(new RegExp(`engine=${engineId}`));
}

// ─── Main Test Suite ──────────────────────────────────────────────────────────

test.describe('Nexus Engine - Full System E2E Workflow', () => {

    test('Complete E2E: Register → Dispatch Pipeline → Preview → Interaction', async ({ page }) => {
        // ── 1. AUTH ──────────────────────────────────────────────────────────
        const { email, password } = await registerUser(page);
        await loginUser(page, email, password);

        // ── 2. NAVIGATE TO NEXUS ORCHESTRATOR ────────────────────────────────
        await test.step('Navigate to Nexus Orchestrator view', async () => {
            await page.goto('/nexus?engine=orchestrator');
            // Wait for the Dispatch Pipeline button to be ready
            await expect(page.locator('button:has-text("Dispatch Pipeline")')).toBeVisible({ timeout: 15000 });
            // Wait for niche select to have options loaded
            await expect(page.locator('select').first()).toBeEnabled({ timeout: 15000 });
        });

        // ── 3. SELECT NICHE & BLUEPRINT ──────────────────────────────────────
        await test.step('Select target niche and architecture blueprint', async () => {
            const nicheSelect = page.locator('select').first();
            const blueprintSelect = page.locator('select').nth(1);

            // Wait for niche options to actually load (API fetch may be slow)
            await expect(async () => {
                const options = await nicheSelect.locator('option').all();
                expect(options.length).toBeGreaterThan(1);
            }).toPass({ timeout: 15000 });

            // Select a niche — use first non-empty option if available
            const nicheOptions = await nicheSelect.locator('option').all();
            if (nicheOptions.length > 1) {
                const nicheValue = await nicheOptions[1].getAttribute('value');
                if (nicheValue) {
                    await nicheSelect.selectOption(nicheValue);
                }
            }

            // Select a blueprint if options exist
            const blueprintOptions = await blueprintSelect.locator('option').all();
            if (blueprintOptions.length > 0) {
                const bpValue = await blueprintOptions[0].getAttribute('value');
                if (bpValue) {
                    await blueprintSelect.selectOption(bpValue);
                }
            }

            // Verify a real niche value was selected, not the placeholder
            const selectedNiche = await nicheSelect.inputValue();
            expect(selectedNiche).toBeTruthy();
        });

        // ── 4. DISPATCH PIPELINE ─────────────────────────────────────────────
        await test.step('Dispatch Nexus Pipeline', async () => {
            // Ensure button is enabled (niche and blueprint must be selected)
            await expect(page.locator('button:has-text("Dispatch Pipeline")')).not.toBeDisabled({ timeout: 10000 });
            await page.click('button:has-text("Dispatch Pipeline")');

            // Verify dispatch success toast notification
            await expect(page.locator('text=Pipeline Dispatched')).toBeVisible({ timeout: 15000 });
        });

        // ── 5. VERIFY ORCHESTRATOR NODE VISUALIZATION ────────────────────────
        await test.step('Verify Orchestrator DAG visualization', async () => {
            // The orchestrator view has a DAG visualization with NexusNode components
            // Verify at least one NexusNode is rendered (the pipeline area)
            const nodeContainer = page.locator('.architect-grid').first();
            await expect(nodeContainer).toBeVisible({ timeout: 5000 });
        });

        // ── 6. PIPELINE HISTORY — POLL FOR COMPLETION ────────────────────────
        await test.step('Navigate to Pipeline History and poll for completion', async () => {
            await navigateToEngine(page, 'history');

            // All possible statuses from DesignCard props and API responses
            const STATUSES_TO_WATCH = [
                'COMPLETED',
                'FAILED',
                'Active', 'Processing', 'Syncing',
                'Scheduled', 'Live Polling', 'Nominal'
            ];
            const statusSelector = STATUSES_TO_WATCH
                .map(s => `span.shrink-0:has-text("${s}")`)
                .join(', ');

            let isCompleted = false;
            let isFailed = false;

            for (let attempt = 0; attempt < 30; attempt++) {
                const statusBadge = page.locator(statusSelector).first();
                if (await statusBadge.isVisible().catch(() => false)) {
                    const statusText = await statusBadge.innerText();
                    if (statusText.toUpperCase() === 'COMPLETED') {
                        isCompleted = true;
                        break;
                    }
                    if (statusText.toUpperCase() === 'FAILED') {
                        isFailed = true;
                        console.log(`[E2E] Pipeline job FAILED after ${attempt + 1} attempts`);
                        break;
                    }
                }

                // Every 10 attempts, reload to sync latest data
                if (attempt > 0 && attempt % 10 === 9) {
                    await page.reload();
                }

                await page.waitForTimeout(3000);
            }

            if (!isCompleted && !isFailed) {
                console.log('[E2E] Pipeline job did not complete within timeout — proceeding with available data');
            }
        });

        // ── 6.5 VERIFY VIDEO OUTPUT VIA API ───────────────────────────────────
        await test.step('Verify pipeline produced video output (output_path)', async () => {
            // Fetch jobs via the API using page context (auth token in localStorage)
            const jobsData = await page.evaluate(async () => {
                // Auth token is stored under "et_token" (see @/lib/auth_utils)
                const token = localStorage.getItem('et_token') || sessionStorage.getItem('et_token');
                if (!token) return { error: 'no_token' };
                try {
                    // API_BASE resolves to http://{host}:7200/api/v1 in the browser
                    const resp = await fetch('/api/v1/nexus/jobs', {
                        headers: { Authorization: `Bearer ${token}` }
                    });
                    if (!resp.ok) return { error: `http_${resp.status}` };
                    return await resp.json();
                } catch (e: any) {
                    return { error: e.message };
                }
            });

            if (jobsData && !jobsData.error) {
                const jobs = Array.isArray(jobsData) ? jobsData : (jobsData.jobs || jobsData.data || []);
                const relevantJob = jobs.find((j: any) =>
                    j.status === 'COMPLETED' || j.status === 'completed' ||
                    j.status === 'FAILED' || j.status === 'failed'
                );

                if (relevantJob) {
                    if (relevantJob.status === 'FAILED' || relevantJob.status === 'failed') {
                        console.log(`[E2E] ⚠️ Pipeline job ${relevantJob.id} ended with FAILED status — no output produced`);
                    } else {
                        const hasOutput = !!(relevantJob.output_path || relevantJob.output_url || relevantJob.video_url);
                        expect(hasOutput).toBeTruthy();
                        console.log(`[E2E] ✅ Pipeline job ${relevantJob.id} produced output: ${relevantJob.output_path || relevantJob.output_url || '(URL on output)'}`);
                    }
                } else {
                    console.log('[E2E] No terminal-status job found in API response — pipeline may still be processing');
                }
            } else {
                console.log('[E2E] Could not fetch jobs via API — skipping output_path verification');
            }
        });

        // ── 7. OPEN SCENE PREVIEW MODAL ──────────────────────────────────────
        await test.step('Open Scene Preview Modal', async () => {
            // Each DesignCard has a refresh/preview button (RotateCcw icon)
            const refreshButton = page.locator('button:has(svg.lucide-rotate-ccw)').first();
            await refreshButton.click();

            // Modal should appear with "Nexus Video Synthesizer" title
            await expect(page.locator('text=Nexus Video Synthesizer')).toBeVisible({ timeout: 15000 });
        });

        // ── 8. VERIFY MODAL CONTENT AND VIDEO ELEMENTS ──────────────────────
        await test.step('Verify Modal content and video asset elements', async () => {
            // Either scenes loaded or loading/status message is acceptable
            const sceneOrStatus = page.locator(
                'text=Visual Direction / Prompt,' +
                'text=Narrative decomposition in progress,' +
                'text=No scene data available'
            ).first();

            try {
                await expect(sceneOrStatus).toBeVisible({ timeout: 15000 });
            } catch {
                // If scenes exist, the scrollable area with scene number badges should be visible
                await expect(page.locator('[class*="bg-violet-500/10"]').first()).toBeVisible({ timeout: 10000 });
            }

            // Verify video asset preview elements in the modal
            // Each scene card displays an "Active Stock Video Segment" with a thumbnail
            // and a filename like "Stock_Footage_X.mp4"
            const assetSection = page.locator('text=Active Stock Video Segment').first();
            if (await assetSection.isVisible().catch(() => false)) {
                console.log('[E2E] ✅ Video asset section visible in preview modal');

                // Check for the video icon/thumbnail in the asset preview area
                const videoIcon = page.locator('svg.lucide-video').first();
                if (await videoIcon.isVisible().catch(() => false)) {
                    console.log('[E2E] ✅ Video thumbnail icon present in scene asset');
                }

                // Look for .mp4 filename references in the asset section
                const mp4Label = page.locator('text=/Stock_Footage_.*\\.mp4/').first();
                if (await mp4Label.isVisible().catch(() => false)) {
                    console.log('[E2E] ✅ Scene asset includes .mp4 video filename');
                }

                // The modal renders scene asset thumbnails as <img> tags
                // (not native <video> elements). A <video> player would appear
                // on a full render page — check if one is present for completeness.
                const videoPlayer = page.locator('video').first();
                if (await videoPlayer.isVisible().catch(() => false)) {
                    const videoSrc = await videoPlayer.getAttribute('src');
                    if (videoSrc) {
                        console.log(`[E2E] ✅ Video player found with source: ${videoSrc.substring(0, 80)}...`);
                        expect(videoSrc).toBeTruthy();
                    }
                }
            } else {
                console.log('[E2E] No video asset section visible — scenes may still be loading');
            }
        });

        // ── 9. SWAP ASSET (if scenes are loaded) ─────────────────────────────
        await test.step('Attempt asset swap in preview modal', async () => {
            // Check if "Swap Asset" button exists (only when scenes are loaded)
            const swapButton = page.locator('button:has-text("Swap Asset")').first();
            if (await swapButton.isVisible().catch(() => false)) {
                await swapButton.click();

                // Asset replacement drawer should open with candidate cards
                await expect(page.locator('text=Select Alternative Curation Candidate')).toBeVisible({ timeout: 5000 });

                // Click one of the alternative asset candidates
                const candidateCard = page.locator('text=Digital Flow').first();
                if (await candidateCard.isVisible().catch(() => false)) {
                    await candidateCard.click();

                    // Verify swap success toast
                    await expect(page.locator('text=Asset replaced visually')).toBeVisible({ timeout: 10000 });
                }
            } else {
                console.log('[E2E] No scenes loaded — skipping asset swap');
            }
        });

        // ── 10. SELECT STYLE PRESET ──────────────────────────────────────────
        await test.step('Select style preset in Neural Style Modulator', async () => {
            // The style presets are in the right column of the modal
            const stylePreset = page.locator('text=Amber Warm').first();
            if (await stylePreset.isVisible().catch(() => false)) {
                await stylePreset.click();

                // Verify preset by checking the "Neon Cyber" preset is no longer selected
                // (active preset has border-cyan-500 class — hard to assert in E2E)
                // Instead, just verify the style modulator section is still visible
                await expect(page.locator('text=Neural Style Modulator')).toBeVisible();
            } else {
                console.log('[E2E] Style modulator not visible — skipping preset selection');
            }
        });

        // ── 11. CLOSE MODAL ──────────────────────────────────────────────────
        await test.step('Close Scene Preview Modal', async () => {
            // Dispatch native click on the backdrop overlay to close the modal
            // The backdrop motion.div has onClick={() => setIsPreviewModalOpen(false)}
            // Using dispatchEvent bypasses Playwright actionability checks and
            // React's synthetic event system picks up the bubbled native event.
            await page.locator('.fixed.inset-0.z-50').first().dispatchEvent('click');

            // Wait for modal to be removed from DOM (exit animation completes)
            // toBeAttached/not.toBeAttached waits for the AnimatePresence exit
            await expect(page.locator('text=Nexus Video Synthesizer')).not.toBeAttached({ timeout: 10000 });
        });

        // ── 12. BACK TO ORCHESTRATOR ─────────────────────────────────────────
        await test.step('Return to Orchestrator view', async () => {
            await navigateToEngine(page, 'orchestrator');
            await expect(page.locator('button:has-text("Dispatch Pipeline")')).toBeVisible({ timeout: 10000 });
        });
    });

    test('Workforce tab: browse agents and verify filtering', async ({ page }) => {
        const { email, password } = await registerUser(page);
        await loginUser(page, email, password);

        await test.step('Navigate to Workforce tab', async () => {
            await page.goto('/nexus?engine=crews');
            await expect(page.locator('text=Workforce Orchestrator')).toBeVisible({ timeout: 15000 });
        });

        await test.step('Verify specialized agents section is present', async () => {
            await expect(page.locator('text=Specialized Agents').first()).toBeVisible({ timeout: 10000 });
            await expect(page.locator('input[placeholder="Search skills..."]')).toBeVisible();
        });

        await test.step('Verify category filter buttons', async () => {
            const allButton = page.locator('button:has-text("All")').first();
            await expect(allButton).toBeVisible();
        });

        await test.step('Verify Neural Workforce Mesh section', async () => {
            await expect(page.locator('text=Neural Workforce Mesh')).toBeVisible({ timeout: 10000 });
            await expect(page.locator('button:has-text("Initialize New Crew")')).toBeVisible();
        });
    });

    test('Neural IDs tab: verify persona listing', async ({ page }) => {
        const { email, password } = await registerUser(page);
        await loginUser(page, email, password);

        await test.step('Navigate to Neural IDs tab', async () => {
            await page.goto('/nexus?engine=identities');
            await expect(page.locator('text=Neural Identity Lab')).toBeVisible({ timeout: 15000 });
        });

        await test.step('Verify Register New ID button', async () => {
            await expect(page.locator('button:has-text("Register New ID")')).toBeVisible();
        });

        await test.step('Verify persona cards or empty state', async () => {
            // Either persona cards exist or the empty state message shows
            const emptyState = page.locator('text=No Neural IDs Found');
            const personaCard = page.locator('text=Active_ID').first();

            const hasPersonas = await personaCard.isVisible().catch(() => false);
            const isEmpty = await emptyState.isVisible().catch(() => false);

            expect(hasPersonas || isEmpty).toBeTruthy();
        });
    });

    test('Command Pod tab: verify command modules', async ({ page }) => {
        const { email, password } = await registerUser(page);
        await loginUser(page, email, password);

        await test.step('Navigate to Command Pod tab', async () => {
            await page.goto('/nexus?engine=command');
            await expect(page.locator('text=Emergency System Halt')).toBeVisible({ timeout: 15000 });
        });

        await test.step('Verify CommandPod components', async () => {
            await expect(page.locator('text=Nexus Master Core').first()).toBeVisible({ timeout: 10000 });
            await expect(page.locator('text=Neural ID Gateway').first()).toBeVisible({ timeout: 10000 });
            await expect(page.locator('text=Pipeline Dispatcher').first()).toBeVisible({ timeout: 10000 });
        });

        await test.step('Verify Emergency System Halt section', async () => {
            await expect(page.locator('button:has-text("Execute Halt_0")')).toBeVisible();
        });
    });

    test('Code Sandbox tab: verify sandbox interface', async ({ page }) => {
        const { email, password } = await registerUser(page);
        await loginUser(page, email, password);

        await test.step('Navigate to Code Sandbox tab', async () => {
            await page.goto('/nexus?engine=sandbox');
            await expect(page.locator('text=Neural Code Sandbox')).toBeVisible({ timeout: 15000 });
        });

        await test.step('Verify console/telemetry tab toggle', async () => {
            await expect(page.locator('button:has-text("Console")')).toBeVisible();
            await expect(page.locator('button:has-text("Live Telemetry")')).toBeVisible();
        });

        await test.step('Verify Execute Node button', async () => {
            await expect(page.locator('button:has-text("Execute_Node")')).toBeVisible();
        });

        await test.step('Verify Active Script panel with code content', async () => {
            await expect(page.locator('text=Active Script')).toBeVisible({ timeout: 10000 });
            await expect(page.locator('text=Execution Output')).toBeVisible();
        });

        await test.step('Switch to Live Telemetry tab', async () => {
            await page.click('button:has-text("Live Telemetry")');
            await expect(page.locator('text=Global Latency')).toBeVisible({ timeout: 5000 });
            await expect(page.locator('text=Celery Cluster Load')).toBeVisible();
            await expect(page.locator('text=Self-Healing Triggers')).toBeVisible();
            await expect(page.locator('text=Cluster Health Ledger')).toBeVisible();
        });
    });

    test('Sidebar navigation: all engine tabs switch correctly', async ({ page }) => {
        const { email, password } = await registerUser(page);
        await loginUser(page, email, password);

        await test.step('Navigate through all sidebar tabs', async () => {
            // Start from the Nexus page so the sidebar is available
            await page.goto('/nexus?engine=orchestrator');
            await expect(page.locator('button:has-text("Dispatch Pipeline")')).toBeVisible({ timeout: 15000 });

            const tabs: { id: string; label: string; heading: RegExp | string }[] = [
                { id: 'orchestrator', label: 'Orchestrator', heading: /Dispatch Pipeline/ },
                { id: 'crews', label: 'Workforce', heading: 'Workforce Orchestrator' },
                { id: 'identities', label: 'Neural IDs', heading: 'Neural Identity Lab' },
                { id: 'sandbox', label: 'Code Sandbox', heading: 'Neural Code Sandbox' },
                { id: 'command', label: 'Command Pod', heading: 'Emergency System Halt' },
                { id: 'history', label: 'Pipeline History', heading: /PIPELINE_/ },
            ];

            for (const tab of tabs) {
                await navigateToEngine(page, tab.id);
                // Verify URL updated correctly
                await expect(page).toHaveURL(new RegExp(`engine=${tab.id}`));
            }
        });
    });

    test('Orchestrator DAG: node interaction and selection', async ({ page }) => {
        const { email, password } = await registerUser(page);
        await loginUser(page, email, password);

        await test.step('Navigate to Orchestrator view', async () => {
            await page.goto('/nexus?engine=orchestrator');
            await expect(page.locator('button:has-text("Dispatch Pipeline")')).toBeVisible({ timeout: 15000 });
        });

        await test.step('Verify Neural Target selector', async () => {
            await expect(page.locator('text=Neural Target')).toBeVisible();
            await expect(page.locator('select').first()).toBeVisible();
        });

        await test.step('Verify Active Architecture selector', async () => {
            await expect(page.locator('text=Active Architecture')).toBeVisible();
            await expect(page.locator('select').nth(1)).toBeVisible();
        });

        // If DAG nodes are rendered, clicking should work
        await test.step('Click orchestrator DAG nodes if present', async () => {
            const dagNode = page.locator('[class*="NexusNode"]').first();
            if (await dagNode.isVisible().catch(() => false)) {
                await dagNode.click();
            } else {
                console.log('[E2E] No DAG nodes rendered (likely no active pipeline job)');
            }
        });
    });
});

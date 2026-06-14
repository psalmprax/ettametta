"use client";

import React, { useEffect, useState } from "react";
import { AnalysisResultsCard, AnalysisReportData } from "@/components/discovery/AnalysisResultsCard";

/**
 * Test fixture page for the AnalysisResultsCard component.
 *
 * Renders the card in isolation with hardcoded analysis data so Playwright
 * tests can verify rendering, interactions, and visual states without
 * needing a running backend.
 *
 * Route: /dev/analysis-card
 */

const SAMPLE_REPORT: AnalysisReportData = {
    candidate_id: "cand_test_e2e_001",
    hook: {
        first_3_seconds: "What if I told you 90% of creators fail at this one thing?",
        emotional_angle: "curiosity",
        scroll_stopper: true,
    },
    pacing: {
        bpm: 132,
        cuts_per_minute: 11.0,
        recommended_duration_s: 45,
    },
    structure: {
        arc: ["hook", "build", "payoff"],
        act_breaks: ["0:00", "0:15", "0:30"],
        retention_curve: [1.0, 0.85, 0.7, 0.6, 0.55],
    },
    style: {
        recommended_style: "cinematic-dark",
        motion_graphics: ["zoom-pulse", "lower-third", "b-roll"],
        color_palette: ["#0a0a0a", "#ff0066", "#00ffcc"],
        typography: "Inter Bold",
    },
    sentiment: {
        overall: "positive",
        emotional_triggers: ["curiosity", "validation", "urgency"],
        target_audience: "creators aged 18-34",
    },
    summary:
        "A punchy, high-retention hook that uses curiosity to stop the scroll. Fast pacing with 132 BPM and 11 cuts per minute keeps energy high. Emotional curve built around validation and urgency. Recommended for cinematic-dark style with b-roll motion graphics.",
    viral_score: 85,
    confidence: 0.89,
};

const LOW_SCORE_REPORT: AnalysisReportData = {
    candidate_id: "cand_low_score_002",
    hook: {
        first_3_seconds: "Slow intro with ambient music...",
        emotional_angle: "calm",
        scroll_stopper: false,
    },
    pacing: {
        bpm: 60,
        cuts_per_minute: 5.0,
        recommended_duration_s: 120,
    },
    structure: {
        arc: ["hook", "payoff"],
        act_breaks: [],
        retention_curve: [1.0, 0.5, 0.3],
    },
    style: {
        recommended_style: "minimal",
        motion_graphics: [],
    },
    sentiment: {
        overall: "neutral",
        emotional_triggers: [],
        target_audience: "general",
    },
    summary: "A slower, lower-scoring piece.",
    viral_score: 35,
    confidence: 0.45,
};

export default function AnalysisCardTestPage() {
    const [hydrated, setHydrated] = useState(false);
    useEffect(() => { setHydrated(true); }, []);

    return (
        <div
            data-hydrated={hydrated ? "true" : "false"}
            style={{ padding: "2rem", maxWidth: 720, margin: "0 auto" }}
        >
            <h1 style={{ fontSize: 20, fontWeight: 700, marginBottom: 24 }}>
                AnalysisResultsCard — Test Fixtures
            </h1>

            <section data-testid="section-high-score" style={{ marginBottom: 48 }}>
                <h2 style={{ fontSize: 14, marginBottom: 12 }}>High Viral Score (85)</h2>
                <AnalysisResultsCard report={SAMPLE_REPORT} />
            </section>

            <section data-testid="section-with-button" style={{ marginBottom: 48 }}>
                <h2 style={{ fontSize: 14, marginBottom: 12 }}>With Create Video button</h2>
                <AnalysisResultsCard
                    report={SAMPLE_REPORT}
                    onCreateVideo={(id) => console.log("Create video for:", id)}
                />
            </section>

            <section data-testid="section-low-score" style={{ marginBottom: 48 }}>
                <h2 style={{ fontSize: 14, marginBottom: 12 }}>Low Viral Score (35)</h2>
                <AnalysisResultsCard report={LOW_SCORE_REPORT} />
            </section>

            <section data-testid="section-loading" style={{ marginBottom: 48 }}>
                <h2 style={{ fontSize: 14, marginBottom: 12 }}>Loading State</h2>
                <AnalysisResultsCard
                    report={SAMPLE_REPORT}
                    isLoading={true}
                />
            </section>

            <section data-testid="section-on-close" style={{ marginBottom: 48 }}>
                <h2 style={{ fontSize: 14, marginBottom: 12 }}>With onClose callback</h2>
                <AnalysisResultsCard
                    report={SAMPLE_REPORT}
                    onClose={() => {
                        (window as any).__onCloseCalled = true;
                    }}
                />
            </section>
        </div>
    );
}

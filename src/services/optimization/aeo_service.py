"""
AEO (Answer Engine Optimization) & GEO (Generative Engine Optimization) Service
Enables ettametta scripts, transcripts, and video metadata to be discoverable,
indexed, and cited by AI engines (ChatGPT, Gemini, Perplexity, Claude, AI Overviews).
"""

import json
import logging
import re
from typing import Any, Optional
from pydantic import BaseModel, Field


class AEOScoreBreakdown(BaseModel):
    direct_answer_score: float = Field(..., description="Score 0-100 for direct answer clarity in first 10s")
    entity_density_score: float = Field(..., description="Score 0-100 for recognizable named entities & concepts")
    citation_authority_score: float = Field(..., description="Score 0-100 for verifiable claims and data points")
    conversational_qa_score: float = Field(..., description="Score 0-100 for conversational Q&A structure")
    overall_aeo_score: float = Field(..., description="Aggregate AEO/GEO readiness score 0-100")


class AEOAnalysisResult(BaseModel):
    scores: AEOScoreBreakdown
    extracted_entities: list[str]
    identified_claims: list[str]
    optimization_recommendations: list[str]
    json_ld_schema: dict[str, Any]
    optimized_faq_pairs: list[dict[str, str]]


class AEOService:
    """
    Evaluates and optimizes video scripts and metadata for Answer Engine Optimization (AEO)
    and Generative Engine Optimization (GEO).
    """

    def __init__(self):
        self.logger = logging.getLogger("AEOService")

    def analyze_and_optimize(
        self,
        title: str,
        script_or_transcript: str,
        niche: str = "general",
        target_platform: str = "youtube",
    ) -> AEOAnalysisResult:
        """
        Analyze content for LLM retrieval and generate citation-ready metadata.
        """
        words = script_or_transcript.split()
        total_words = max(len(words), 1)

        # 1. Direct Answer Analysis (Check first 40 words for clear thesis/hook)
        first_40_words = " ".join(words[:40]).lower()
        direct_indicators = [
            "here is how", "the reason is", "the secret to", "how to",
            "in this video", "step 1", "first", "because", "explained", "is actually"
        ]
        has_direct_hook = any(ind in first_40_words for ind in direct_indicators)
        direct_answer_score = 90.0 if has_direct_hook else 45.0

        # 2. Entity Density Analysis
        # Extract capitalized multi-word phrases and common tech/business terms
        entity_matches = re.findall(r'\b[A-Z][a-zA-Z0-9_]+(?:\s+[A-Z][a-zA-Z0-9_]+)*\b', script_or_transcript)
        unique_entities = list(set([e for e in entity_matches if len(e) > 2]))[:15]
        entity_ratio = len(unique_entities) / (total_words / 50.0)
        entity_density_score = min(max(entity_ratio * 35.0, 30.0), 98.0)

        # 3. Citation Authority & Factuality Markers (Numbers, stats, percentages, dates)
        stats_matches = re.findall(r'\b(?:\d+[%kKmMbB]?|\$\d+|\d+\.\d+)\b', script_or_transcript)
        citations_found = len(stats_matches)
        citation_authority_score = min(max(citations_found * 15.0 + 35.0, 30.0), 95.0)

        # 4. Conversational Q&A Structure (Questions, 'why', 'how', 'what')
        question_count = script_or_transcript.count("?")
        conversational_qa_score = min(max(question_count * 20.0 + 40.0, 35.0), 95.0)

        # 5. Calculate Aggregate Score
        overall = (
            direct_answer_score * 0.30
            + entity_density_score * 0.25
            + citation_authority_score * 0.25
            + conversational_qa_score * 0.20
        )
        scores = AEOScoreBreakdown(
            direct_answer_score=round(direct_answer_score, 1),
            entity_density_score=round(entity_density_score, 1),
            citation_authority_score=round(citation_authority_score, 1),
            conversational_qa_score=round(conversational_qa_score, 1),
            overall_aeo_score=round(overall, 1),
        )

        # 6. Generate Recommendations
        recommendations = []
        if direct_answer_score < 70:
            recommendations.append("Lead with a direct answer or core insight in the first 5 seconds to maximize AI extractability.")
        if entity_density_score < 60:
            recommendations.append("Include specific named entities, tools, and technical terms rather than vague pronouns.")
        if citation_authority_score < 60:
            recommendations.append("Incorporate verifiable statistics, benchmark metrics, or source references.")
        if conversational_qa_score < 60:
            recommendations.append("Structure sections around natural conversational questions (e.g. 'Why does X work?').")

        # 7. Generate JSON-LD Schema
        json_ld = {
            "@context": "https://schema.org",
            "@type": "VideoObject",
            "name": title,
            "description": script_or_transcript[:250] + "...",
            "keywords": unique_entities[:8],
            "about": [{"@type": "Thing", "name": e} for e in unique_entities[:5]],
        }

        # 8. Generate Structured FAQ Pairs for Search Extractors
        faq_pairs = [
            {
                "question": f"What is the main takeaway regarding {title}?",
                "answer": script_or_transcript[:180] + "...",
            }
        ]
        if unique_entities:
            faq_pairs.append({
                "question": f"How does {unique_entities[0]} apply to {niche}?",
                "answer": f"In {title}, {unique_entities[0]} is featured as a key factor in achieving high performance.",
            })

        return AEOAnalysisResult(
            scores=scores,
            extracted_entities=unique_entities,
            identified_claims=stats_matches[:10],
            optimization_recommendations=recommendations,
            json_ld_schema=json_ld,
            optimized_faq_pairs=faq_pairs,
        )


base_aeo_service = AEOService()

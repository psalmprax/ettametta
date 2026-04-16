#!/usr/bin/env python3
"""
Video Eligibility Checker - Professional Rejection Reasons
=====================================

Professional video editor standards for video selection.
Each video must pass ALL requirements to be eligible for use.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field


@dataclass
class RejectionReason:
    """Single rejection reason with details"""

    code: str
    category: str
    message: str
    severity: str = "blocking"
    fixable: bool = False


# Comprehensive rejection reasons - professional video editor standards
REJECTION_REASONS = {
    # QUALITY - MUST BE 4K OR ABOVE
    "NOT_4K": RejectionReason(
        code="NOT_4K",
        category="Quality",
        message="Video quality below 4K - must be 4K or higher resolution",
        severity="blocking",
        fixable=False,
    ),
    "HD_ONLY": RejectionReason(
        code="HD_ONLY",
        category="Quality",
        message="Only HD (1080p) - 4K required for professional output",
        severity="blocking",
        fixable=False,
    ),
    "LOW_RESOLUTION": RejectionReason(
        code="LOW_RESOLUTION",
        category="Quality",
        message="Low resolution - minimum 1920x1080 required",
        severity="blocking",
        fixable=False,
    ),
    # TALKING HEAD - Person just speaking to camera
    "TALKING_HEAD": RejectionReason(
        code="TALKING_HEAD",
        category="Content Type",
        message="Person speaking directly to camera throughout - no visual demonstration",
        severity="blocking",
        fixable=False,
    ),
    "NO_VISUAL_DEMO": RejectionReason(
        code="NO_VISUAL_DEMO",
        category="Content Type",
        message="Content lacks visual interest - viewers must see to learn",
        severity="blocking",
        fixable=False,
    ),
    "NOTHING_TO_CUT": RejectionReason(
        code="NOTHING_TO_CUT",
        category="Content Type",
        message="Pure talking head - nothing to cut to for B-roll",
        severity="blocking",
        fixable=False,
    ),
    "VLOG_CONTENT": RejectionReason(
        code="VLOG_CONTENT",
        category="Content Type",
        message="Vlog style content - not suitable for educational/professional edit",
        severity="blocking",
        fixable=False,
    ),
    "PODCAST_CLIP": RejectionReason(
        code="PODCAST_CLIP",
        category="Content Type",
        message="Podcast/interview clip - no visual aids or demonstration",
        severity="blocking",
        fixable=False,
    ),
    # QUALITY ISSUES
    "LOW_QUALITY": RejectionReason(
        code="LOW_QUALITY",
        category="Quality",
        message="Low visual quality - cannot use as B-roll",
        severity="blocking",
        fixable=False,
    ),
    "BLURRY": RejectionReason(
        code="BLURRY",
        category="Quality",
        message="Blurry footage - won't pass platform QC",
        severity="blocking",
        fixable=False,
    ),
    "DARK_FOOTAGE": RejectionReason(
        code="DARK_FOOTAGE",
        category="Quality",
        message="Too dark - poor visibility",
        severity="blocking",
        fixable=False,
    ),
    "POOR_LIGHTING": RejectionReason(
        code="POOR_LIGHTING",
        category="Quality",
        message="Poor lighting conditions - looks amateur",
        severity="blocking",
        fixable=False,
    ),
    "PIXELATED": RejectionReason(
        code="PIXELATED",
        category="Quality",
        message="Extremely pixelated - platform will reject",
        severity="blocking",
        fixable=False,
    ),
    "WRONG_ASPECT": RejectionReason(
        code="WRONG_ASPECT",
        category="Quality",
        message="Wrong aspect ratio for target platform",
        severity="warning",
        fixable=True,  # Can be cropped
    ),
    "POOR_AUDIO": RejectionReason(
        code="POOR_AUDIO",
        category="Quality",
        message="Poor audio quality - excessive noise",
        severity="blocking",
        fixable=False,
    ),
    "WATERMARK": RejectionReason(
        code="WATERMARK",
        category="Quality",
        message="Contains platform watermark",
        severity="blocking",
        fixable=False,
    ),
    # CONTENT RESTRICTIONS
    "COMPETITOR_BRAND": RejectionReason(
        code="COMPETITOR_BRAND",
        category="Legal",
        message="Contains competitor branding - legal issue",
        severity="blocking",
        fixable=False,
    ),
    "COPYRIGHTED_MUSIC": RejectionReason(
        code="COPYRIGHTED_MUSIC",
        category="Legal",
        message="Music video with copyrighted audio - claims will strike",
        severity="blocking",
        fixable=False,
    ),
    "NEWS_CONTENT": RejectionReason(
        code="NEWS_CONTENT",
        category="Relevance",
        message="News content - dated quickly",
        severity="warning",
        fixable=False,
    ),
    "EXPIRED_TREND": RejectionReason(
        code="EXPIRED_TREND",
        category="Relevance",
        message="Expired trend - no longer relevant",
        severity="blocking",
        fixable=False,
    ),
    # CONTEXT ISSUES
    "NO_DEMONSTRATION": RejectionReason(
        code="NO_DEMONSTRATION",
        category="Content Type",
        message="Person visible but not demonstrating anything",
        severity="blocking",
        fixable=False,
    ),
    "UNRELATED_TOPIC": RejectionReason(
        code="UNRELATED_TOPIC",
        category="Relevance",
        message="Unrelated to target topic",
        severity="blocking",
        fixable=False,
    ),
    "RANDOM_BROLL": RejectionReason(
        code="RANDOM_BROLL",
        category="Context",
        message="Random B-roll without narrative context",
        severity="warning",
        fixable=False,
    ),
    "TOO_SHORT": RejectionReason(
        code="TOO_SHORT",
        category="Duration",
        message="Too short to use meaningfully (under 5 seconds)",
        severity="blocking",
        fixable=False,
    ),
    "TOO_LONG": RejectionReason(
        code="TOO_LONG",
        category="Duration",
        message="Too long - would bloat final edit",
        severity="warning",
        fixable=True,  # Can trim
    ),
    # COHERENCE
    "WONT_FLOW": RejectionReason(
        code="WONT_FLOW",
        category="Coherence",
        message="Does not flow with other selected videos",
        severity="blocking",
        fixable=False,
    ),
    "INCONSISTENT_STYLE": RejectionReason(
        code="INCONSISTENT_STYLE",
        category="Coherence",
        message="Inconsistent style/quality breaks production value",
        severity="blocking",
        fixable=False,
    ),
    "WRONG_AUDIENCE": RejectionReason(
        code="WRONG_AUDIENCE",
        category="Targeting",
        message="Wrong target audience",
        severity="blocking",
        fixable=False,
    ),
    "MOOD_MISMATCH": RejectionReason(
        code="MOOD_MISMATCH",
        category="Coherence",
        message="Different mood/tone than project",
        severity="warning",
        fixable=False,
    ),
    # BRANDING
    "TEXT_CONFLICT": RejectionReason(
        code="TEXT_CONFLICT",
        category="Branding",
        message="Heavy text overlay - may conflict with our branding",
        severity="warning",
        fixable=False,
    ),
    "NEGATIVE_MOOD": RejectionReason(
        code="NEGATIVE_MOOD",
        category="Branding",
        message="Negative mood may not fit target audience",
        severity="warning",
        fixable=False,
    ),
    "INAPPROPRIATE": RejectionReason(
        code="INAPPROPRIATE",
        category="Legal",
        message="Inappropriate content - age-restricted",
        severity="blocking",
        fixable=False,
    ),
}


class VideoEligibilityChecker:
    """
    Professional video eligibility checker.
    Videos must pass ALL requirements to be eligible.
    """

    def __init__(
        self,
        target_platform: str = "youtube",
        target_audience: str = "general",
        target_mood: str = "professional",
    ):
        self.target_platform = target_platform
        self.target_audience = target_audience
        self.target_mood = target_mood

    def check_eligibility(self, video_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check if video meets ALL professional requirements.

        Returns:
        {
            "eligible": bool,
            "rejection_reasons": List[RejectionReason],
            "warnings": List[RejectionReason],
            "passed_checks": List[str],
            "overall_score": float
        }
        """
        rejections = []
        warnings = []
        passed = []
        score = 10.0  # Start perfect, deduct for issues

        # 1. CONTENT TYPE CHECK
        content_type = video_analysis.get("content_type", "unknown")

        if content_type == "talking_head":
            rejections.append(REJECTION_REASONS["TALKING_HEAD"])
            score -= 5
        elif content_type == "person_present":
            # Check if demonstrating or just talking
            person_activity = video_analysis.get("person_activity", "")
            if person_activity not in [
                "demonstrating",
                "concept_explaining",
                "screen_recording",
            ]:
                rejections.append(REJECTION_REASONS["NO_DEMONSTRATION"])
                score -= 3
            else:
                passed.append("content_type")
        else:
            passed.append("content_type")

        # 2. VISUAL QUALITY CHECK
        visual_quality = video_analysis.get("visual_quality", 10)
        if visual_quality < 5:
            rejections.append(REJECTION_REASONS["LOW_QUALITY"])
            score -= 4
        elif visual_quality < 7:
            warnings.append(REJECTION_REASONS["BLURRY"])
            score -= 2
        else:
            passed.append("visual_quality")

        # 3. RESOLUTION CHECK - MINIMUM 1080p (4K preferred)
        resolution = video_analysis.get("resolution", "4K")
        resolution_height = video_analysis.get("resolution_height", 0)

        if resolution_height > 0:
            # Below 1080p = SD → REJECT
            if resolution_height < 1080:
                rejections.append(REJECTION_REASONS["LOW_RESOLUTION"])
                score -= 6
            # 1080p-2159p = HD → Allow (not 4K but acceptable)
            elif resolution_height < 2160:
                warnings.append(
                    REJECTION_REASONS["HD_ONLY"]
                )  # Warning only, not rejection
                score -= 0
            # 2160+ = 4K/8K → PASS
            elif resolution_height >= 2160:
                passed.append("resolution_4K")
        else:
            # Unknown resolution - assume OK but warn
            warnings.append(REJECTION_REASONS["LOW_RESOLUTION"])
            score -= 1

        # 3. DURATION CHECK
        duration = video_analysis.get("duration", 0)
        if duration < 5:
            rejections.append(REJECTION_REASONS["TOO_SHORT"])
            score -= 3
        elif duration > 600:  # 10+ minutes
            warnings.append(REJECTION_REASONS["TOO_LONG"])
            score -= 1
        else:
            passed.append("duration")

        # 4. Freshness check (if published date available)
        if video_analysis.get("is_old", True):
            if video_analysis.get("age_days", 0) > 365:
                warnings.append(REJECTION_REASONS["NEWS_CONTENT"])
                score -= 1
            else:
                passed.append("freshness")

        # 5. Check for watermarks/text overlays
        if video_analysis.get("has_watermark", False):
            rejections.append(REJECTION_REASONS["WATERMARK"])
            score -= 3

        if video_analysis.get("has_text_overlay", False):
            # Not blocking, but note it
            warnings.append(REJECTION_REASONS["TEXT_CONFLICT"])
            score -= 0.5

        # Determine eligibility
        # Blocking reasons = cannot use
        # Warnings = can use but be aware
        eligible = len(rejections) == 0 and score >= 5.0

        return {
            "eligible": eligible,
            "rejection_reasons": [r.code for r in rejections],
            "rejection_details": [
                {"code": r.code, "message": r.message, "category": r.category}
                for r in rejections
            ],
            "warnings": [
                {"code": w.code, "message": w.message, "category": w.category}
                for w in warnings
            ],
            "passed_checks": passed,
            "overall_score": max(0, score),
            "recommendation": self._get_recommendation(eligible, score, len(warnings)),
        }

    def _get_recommendation(
        self, eligible: bool, score: float, warning_count: int
    ) -> str:
        """Get human-readable recommendation"""
        if not eligible:
            return "REJECT - Does not meet professional standards"
        if score >= 8:
            return "APPROVE - Excellent quality, use as primary"
        if score >= 6:
            return "APPROVE - Good quality, use as secondary"
        if warning_count > 0:
            return "APPROVE WITH CAUTION - Review warnings before use"
        return "REVIEW - Manual review recommended"


def check_video_requirements(
    video_data: Dict[str, Any], target_platform: str = "youtube"
) -> Dict[str, Any]:
    """
    Standalone function to check all requirements.

    Usage:
        result = check_video_requirements(video_analysis)
        if result["eligible"]:
            use_video(result)
        else:
            print(f"Rejected: {result['rejection_reasons']}")
    """
    checker = VideoEligibilityChecker(target_platform=target_platform)
    return checker.check_eligibility(video_data)


# Export the reasons for use in UI
REJECTION_CATEGORIES = {
    "Content Type": [
        "TALKING_HEAD",
        "NO_VISUAL_DEMO",
        "NOTHING_TO_CUT",
        "VLOG_CONTENT",
        "PODCAST_CLIP",
        "NO_DEMONSTRATION",
    ],
    "Quality": [
        "LOW_QUALITY",
        "BLURRY",
        "DARK_FOOTAGE",
        "POOR_LIGHTING",
        "PIXELATED",
        "WRONG_ASPECT",
        "POOR_AUDIO",
        "WATERMARK",
    ],
    "Legal": ["COMPETITOR_BRAND", "COPYRIGHTED_MUSIC", "INAPPROPRIATE"],
    "Relevance": ["NEWS_CONTENT", "EXPIRED_TREND", "UNRELATED_TOPIC"],
    "Coherence": ["WONT_FLOW", "INCONSISTENT_STYLE", "MOOD_MISMATCH"],
    "Targeting": ["WRONG_AUDIENCE"],
    "Duration": ["TOO_SHORT", "TOO_LONG"],
    "Branding": ["TEXT_CONFLICT", "NEGATIVE_MOOD"],
}


if __name__ == "__main__":
    # Test the checker
    test_video = {
        "content_type": "talking_head",
        "visual_quality": 4.0,
        "duration": 120,
        "age_days": 30,
    }

    result = check_video_requirements(test_video)
    print(f"Eligible: {result['eligible']}")
    print(f"Score: {result['overall_score']}/10")
    print(f"Reasons: {result['rejection_reasons']}")
    print(f"Recommendation: {result['recommendation']}")

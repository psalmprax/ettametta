import pytest
from src.services.hermes.service import base_hermes_service, HermesCycleConfig, HermesCycleResult


@pytest.mark.asyncio
async def test_hermes_autonomous_cycle_with_skill_learning():
    config = HermesCycleConfig(
        niche="ai_technology",
        target_platforms=["youtube", "tiktok"],
        autonomy_mode="AUTOPILOT",
        auto_publish=True,
    )

    result = await base_hermes_service.run_autonomous_cycle(config)

    assert isinstance(result, HermesCycleResult)
    assert result.status == "completed"
    assert result.cycle_id.startswith("hermes_")
    assert result.aeo_analysis is not None
    assert result.aeo_analysis.scores.overall_aeo_score >= 80.0
    assert len(result.learned_skills_extracted) > 0

    # Verify persistent skill store has recorded the skill
    best_skills = base_hermes_service.skill_store.get_best_skills("ai_technology")
    assert len(best_skills) > 0
    assert best_skills[0].pattern_type == "viral_hook"

import asyncio
import os
import sys
import json
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from src.services.optimization.viral_critic import base_viral_critic

async def test_audit():
    print("Testing Phase 2: ViralCritic Audit...")
    topic = "AI productivity tools viral 2026"
    
    # Mock data
    mock_script = {
        "segments": [
            {"text": "Discover the top 5 AI tools that will double your productivity in 2026!"},
            {"text": "First, we have TaskMaster AI which automates your entire schedule."},
            {"text": "Next is CodeGenius, the ultimate assistant for developers."},
            {"text": "Don't forget about VoiceFlow for seamless meeting notes."},
            {"text": "Click the link in bio to get the full list!"}
        ]
    }
    mock_metadata = {"duration": 60, "segments_used": 5}
    
    print(f"🧐 Auditing: {topic}")
    audit_report = await base_viral_critic.review_production(topic, mock_script, mock_metadata, session_id="test_audit_session")
    
    print("\n" + "="*60)
    print("AUDIT REPORT")
    print("="*60)
    print(f"Overall Score: {audit_report.get('overall_score')}/10")
    print(f"Ship Status: {audit_report.get('ship_status')}")
    print(f"Report: {audit_report.get('report')}")
    print(f"Suggestions: {audit_report.get('improvement_suggestions', [])}")
    
    if audit_report.get('overall_score', 0) >= 6.0:
        print("\n✅ Phase 2 Passed!")
    else:
        print("\n❌ Phase 2 Rejected (as intended if quality is low).")

if __name__ == "__main__":
    asyncio.run(test_audit())

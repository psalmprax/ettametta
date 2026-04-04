import os
import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class PaperclipKPITool:
    """
    Paperclip KPI tracking tool for Agent Zero.
    """
    
    def __init__(self):
        self.kpi_store = "/tmp/agent_zero_kpis.json"
        if not os.path.exists(self.kpi_store):
            with open(self.kpi_store, "w") as f:
                json.dump({}, f)
                
    def record_kpi(self, video_id: str, platform: str, views: int, revenue: float = 0.0) -> str:
        """
        Record and compare KPIs to previous baseline.
        """
        try:
            with open(self.kpi_store, "r") as f:
                data = json.load(f)
                
            prev_views = data.get(video_id, {}).get("views", 0)
            diff = views - prev_views
            
            data[video_id] = {
                "platform": platform,
                "views": views,
                "revenue": revenue,
                "delta": diff
            }
            
            with open(self.kpi_store, "w") as f:
                json.dump(data, f)
                
            trend = "📈 Trending Up" if diff > 0 else "📉 Stale"
            return f"Paperclip KPI Recorded for {video_id} ({platform}): {views} views. {trend} (+{diff})"
        except Exception as e:
            return f"Error recording KPI: {str(e)}"

    def get_scaling_advice(self) -> str:
        """
        Simple heuristic for autonomous scaling.
        """
        try:
            with open(self.kpi_store, "r") as f:
                data = json.load(f)
                
            winning_niches = {}
            for vid, kpi in data.items():
                if kpi["views"] > 500: # Threshold for 'winning'
                    winning_niches[vid] = kpi
                    
            if not winning_niches:
                return "Advice: Increase volume. No viral outliers found."
                
            return f"Advice: Found {len(winning_niches)} viral anchors. Initiate 'Organic Ad' replication in these domains."
        except Exception as e:
            return f"Error getting advice: {str(e)}"

paperclip_kpi = PaperclipKPITool()

def run(action: str, **kwargs) -> str:
    """
    Entry point for Agent Zero tool execution.
    """
    if action == "record":
        return paperclip_kpi.record_kpi(
            kwargs.get("video_id"),
            kwargs.get("platform", "TikTok"),
            kwargs.get("views", 0),
            kwargs.get("revenue", 0.0)
        )
    elif action == "advice":
        return paperclip_kpi.get_scaling_advice()
    return "Unknown action for Paperclip KPI tool."

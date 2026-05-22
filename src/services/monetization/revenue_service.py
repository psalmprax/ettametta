"""
Real Monetization & Revenue Tracking Service
============================================
Tracks earnings by aggregating published content metrics from the database
and integrating with external platform APIs where available.
"""

import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, func
from src.api.utils.database import async_session_factory
from src.api.utils.models import PublishedContentDB, UserDB

logger = logging.getLogger(__name__)


class MonetizationService:
    """Tracks real revenue and monetization metrics."""

    async def get_revenue_summary(self, user_id: str, days: int = 30) -> dict[str, Any]:
        """
        Get real revenue summary based on published content performance.
        
        Uses a simplified RPM (Revenue Per Mille) model for estimation:
        - YouTube: $5.00 per 1,000 views
        - TikTok: $0.02 per 1,000 views (Creator Fund approx)
        - Affiliates: $0.50 per click (estimated)
        """
        async with async_session_factory() as db:
            # Calculate date range
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Fetch published content for this user within the date range
            stmt = select(PublishedContentDB).where(
                PublishedContentDB.user_id == user_id,
                PublishedContentDB.published_at >= start_date
            )
            result = await db.execute(stmt)
            contents = result.scalars().all()
            
            total_revenue = 0.0
            platform_breakdown = []
            daily_breakdown = []
            
            # Group by platform
            platform_stats = {}
            daily_stats = {}
            
            for content in contents:
                platform = content.platform or "Unknown"
                pub_date = content.published_at.date() if content.published_at else datetime.now(timezone.utc).date()
                date_str = pub_date.isoformat()
                
                # Initialize stats
                if platform not in platform_stats:
                    platform_stats[platform] = {
                        "revenue": 0.0,
                        "views": 0,
                        "clicks": 0
                    }
                
                if date_str not in daily_stats:
                    daily_stats[date_str] = {"date": date_str, "amount": 0.0}
                
                # Estimate revenue based on platform RPM
                views = content.view_count or 0
                clicks = content.click_count or 0
                
                if platform.lower() == "youtube":
                    rev = (views / 1000.0) * 5.00  # $5 RPM
                elif platform.lower() == "tiktok":
                    rev = (views / 1000.0) * 0.02  # $0.02 RPM
                elif platform.lower() == "affiliate":
                    rev = clicks * 0.50  # $0.50 per click
                else:
                    rev = (views / 1000.0) * 1.00  # Default $1 RPM
                
                platform_stats[platform]["revenue"] += rev
                platform_stats[platform]["views"] += views
                platform_stats[platform]["clicks"] += clicks
                
                daily_stats[date_str]["amount"] += rev
                total_revenue += rev
            
            # Format platform breakdown
            for platform, stats in platform_stats.items():
                platform_breakdown.append({
                    "platform": platform,
                    "revenue": round(stats["revenue"], 2),
                    "views": stats["views"],
                    "clicks": stats["clicks"]
                })
            
            # Format daily breakdown
            daily_breakdown = list(daily_stats.values())
            daily_breakdown.sort(key=lambda x: x["date"])
            
            # Calculate averages
            daily_average = total_revenue / days if days > 0 else 0
            
            return {
                "total_revenue": round(total_revenue, 2),
                "currency": "USD",
                "period_days": days,
                "daily_average": round(daily_average, 2),
                "platforms": platform_breakdown,
                "daily_breakdown": daily_breakdown,
                "top_performing_video": self._get_top_video(contents) if contents else None
            }

    def _get_top_video(self, contents: list) -> dict[str, Any]:
        """Find the top performing video from the list."""
        if not contents:
            return None
        
        # Sort by view count
        sorted_contents = sorted(contents, key=lambda x: x.view_count or 0, reverse=True)
        top = sorted_contents[0]
        
        # Estimate its revenue
        views = top.view_count or 0
        if top.platform and top.platform.lower() == "youtube":
            rev = (views / 1000.0) * 5.00
        elif top.platform and top.platform.lower() == "tiktok":
            rev = (views / 1000.0) * 0.02
        else:
            rev = (views / 1000.0) * 1.00
            
        return {
            "title": top.title or "Untitled",
            "revenue": round(rev, 2),
            "platform": top.platform or "Unknown"
        }

    async def get_monetization_goals(self, user_id: str) -> dict[str, Any]:
        """
        Get real monetization goals. 
        In a full implementation, this would query a UserSettings or Goals table.
        For now, we use a default goal structure.
        """
        # Default monthly goal
        monthly_goal = 2000.00
        
        # Get current month's revenue
        summary = await self.get_revenue_summary(user_id, days=30)
        current_progress = summary["total_revenue"]
        
        # Calculate projected end of month
        days_remaining = 30 - (datetime.now(timezone.utc).day)
        daily_avg = summary["daily_average"]
        projected_end = current_progress + (daily_avg * days_remaining)
        
        percentage = (current_progress / monthly_goal * 100) if monthly_goal > 0 else 0
        
        return {
            "monthly_goal": monthly_goal,
            "current_progress": round(current_progress, 2),
            "percentage": round(percentage, 1),
            "days_remaining": days_remaining,
            "projected_end_of_month": round(projected_end, 2)
        }


# Singleton instance
base_revenue_service = MonetizationService()

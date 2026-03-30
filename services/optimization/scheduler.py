from datetime import datetime, timedelta
import random
from typing import List

class SmartScheduler:
    def __init__(self):
        # Default peak engagement windows (Fallback)
        self.default_windows = [
            {"start": 9, "end": 11},  # Morning rush
            {"start": 12, "end": 14}, # Lunch break
            {"start": 18, "end": 21}  # Evening peak
        ]

    def _get_peak_windows_from_db(self, user_id: int = None) -> List[dict]:
        """
        Dynamically calculate peak engagement windows based on historic real performance.
        Falls back to default windows if insufficient data.
        """
        try:
            from api.utils.database import SessionLocal
            from api.utils.models import PublishedContentDB
            from sqlalchemy import extract, func
            
            db = SessionLocal()
            try:
                # Query views grouped by the hour the post was created/published
                query = db.query(
                    extract('hour', PublishedContentDB.published_at).label('hour'),
                    func.avg(PublishedContentDB.view_count).label('avg_views')
                ).filter(PublishedContentDB.status == "Published", PublishedContentDB.view_count > 0)
                
                if user_id:
                    query = query.filter(PublishedContentDB.user_id == user_id)
                
                results = query.group_by(extract('hour', PublishedContentDB.published_at)) \
                               .order_by(func.avg(PublishedContentDB.view_count).desc()) \
                               .limit(3).all()
                               
                if len(results) >= 2:
                    # Construct smart windows based on top performing hours
                    windows = []
                    for row in results:
                        hour = int(row.hour)
                        windows.append({"start": hour, "end": hour + 2})
                    return sorted(windows, key=lambda x: x["start"])
            finally:
                db.close()
        except Exception as e:
            # If DB error or missing models, we fall back to defaults
            import logging
            logging.getLogger("SmartScheduler").warning(f"Failed to calculate dynamic peak windows: {e}. Using fallback.")
            
        return self.default_windows

    def calculate_next_posting_time(self, last_post_time: Optional[datetime] = None, user_id: int = None) -> datetime:
        """
        Calculates the optimal next posting window based on current trends and peak times.
        """
        now = datetime.utcnow()
        base_time = last_post_time if last_post_time and last_post_time > now else now
        
        # Add random buffer to avoid bot detection patterns (30-90 mins)
        next_time = base_time + timedelta(minutes=random.randint(30, 90))
        
        # Adjust to nearest peak window
        peak_windows = self._get_peak_windows_from_db(user_id)
        current_hour = next_time.hour
        for window in peak_windows:
            if current_hour >= window["start"] and current_hour <= window["end"]:
                return next_time
        
        # If not in window, find the next one
        for window in peak_windows:
            if window["start"] > current_hour:
                return next_time.replace(hour=window["start"], minute=random.randint(0, 30))
        
        # Next day first window
        return (next_time + timedelta(days=1)).replace(hour=peak_windows[0]["start"], minute=random.randint(0, 30))

smart_scheduler = SmartScheduler()

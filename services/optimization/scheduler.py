from datetime import datetime, timedelta
import random
from typing import List

class SmartScheduler:
    def __init__(self):
        # Peak engagement windows (mocked)
        self.peak_windows = [
            {"start": 9, "end": 11},  # Morning rush
            {"start": 12, "end": 14}, # Lunch break
            {"start": 18, "end": 21}  # Evening peak
        ]

    def calculate_next_posting_time(self, last_post_time: Optional[datetime] = None) -> datetime:
        """
        Calculates the optimal next posting window based on current trends and peak times.
        """
        now = datetime.utcnow()
        base_time = last_post_time if last_post_time and last_post_time > now else now
        
        # Add random buffer to avoid bot detection patterns (30-90 mins)
        next_time = base_time + timedelta(minutes=random.randint(30, 90))
        
        # Adjust to nearest peak window
        current_hour = next_time.hour
        for window in self.peak_windows:
            if current_hour >= window["start"] and current_hour <= window["end"]:
                return next_time
        
        # If not in window, find the next one
        for window in self.peak_windows:
            if window["start"] > current_hour:
                return next_time.replace(hour=window["start"], minute=random.randint(0, 30))
        
        # Next day first window
        return (next_time + timedelta(days=1)).replace(hour=self.peak_windows[0]["start"], minute=random.randint(0, 30))

smart_scheduler = SmartScheduler()

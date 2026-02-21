import os
import sys

# Ensure project root is in path
sys.path.append(os.getcwd())

from api.utils.database import SessionLocal
from api.utils.models import MonitoredNiche
from services.discovery.tasks import sentinel_trend_watcher

def verify_sentinel():
    print("🚀 Verifying ettametta Sentinel Automation...")
    
    db = SessionLocal()
    try:
        # 1. Check Seeding
        niches = db.query(MonitoredNiche).all()
        if not niches:
            print("❌ No niches found. Seeding now for test...")
            default_niches = ["Motivation", "AI Technology", "Stoic Wisdom"]
            for n in default_niches:
                db.add(MonitoredNiche(niche=n, is_active=True))
            db.commit()
            niches = db.query(MonitoredNiche).all()
        
        print(f"✅ Found {len(niches)} monitored niches: {[n.niche for n in niches]}")
        
        # 2. Trigger Sentinel Task Manually (Sync for testing)
        print("\n📡 Triggering Sentinel Watcher...")
        result = sentinel_trend_watcher()
        print(f"✅ Sentinel Result: {result}")
        
        # 3. Verify last_scanned_at update
        db.expire_all()
        updated_niche = db.query(MonitoredNiche).first()
        if updated_niche.last_scanned_at:
             print(f"✅ Niches timestamped: {updated_niche.last_scanned_at}")
        else:
             print("❌ Niches not timestamped!")

    finally:
        db.close()

if __name__ == "__main__":
    verify_sentinel()

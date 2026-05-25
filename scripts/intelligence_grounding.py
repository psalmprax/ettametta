import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from api.utils.database import SessionLocal
from api.utils.models import AffiliateLinkDB
from api.utils.user_models import UserDB
from sqlalchemy.orm import Session

def seed_intelligence():
    db: Session = SessionLocal()
    try:
        # 1. Ensure a default user exists
        user = db.query(UserDB).filter(UserDB.username == "psalmprax").first()
        if not user:
            print("Creating default user 'psalmprax'...")
            user = UserDB(
                username="psalmprax",
                email="psalmprax@ettametta.io",
                hashed_password="hashed_placeholder", # Not used for this script
                role="admin",
                subscription="sovereign"
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        
        # 2. Seed Affiliate Links with 2026 Source Data
        affiliates = [
            # AI / SaaS
            {
                "product_name": "AdCreative.ai (Enterprise)",
                "niche": "AI SaaS",
                "link": "https://free-trial.adcreative.ai/ettametta-nexus",
                "cta_text": "GENERATE WINNING ADS"
            },
            {
                "product_name": "HubSpot Marketing Hub",
                "niche": "AI SaaS",
                "link": "https://hubspot.sjv.io/ettametta",
                "cta_text": "SCALE YOUR EMPIRE"
            },
            {
                "product_name": "Reclaim.ai Productivity",
                "niche": "Productivity",
                "link": "https://reclaim.ai/r/s/ettametta",
                "cta_text": "RECLAIM YOUR TIME"
            },
            # Biohacking / Health
            {
                "product_name": "NutriProfits Longevity Stack",
                "niche": "Biohacking",
                "link": "https://nutriprofits.com/ettametta-longevity",
                "cta_text": "UPGRADE YOUR BIOLOGY"
            },
            {
                "product_name": "Water & Wellness Quinton",
                "niche": "Biohacking",
                "link": "https://waterandwellness.com/ettametta",
                "cta_text": "HYDRATE YOUR NEURONS"
            },
            # Crypto / Finance
            {
                "product_name": "Binance Global",
                "niche": "Crypto",
                "link": "https://accounts.binance.com/register?ref=ETTAMETTA",
                "cta_text": "FUEL YOUR FLEET"
            },
            {
                "product_name": "Ledger Stax",
                "niche": "Crypto",
                "link": "https://shop.ledger.com/ettametta-stax",
                "cta_text": "SECURE YOUR ASSETS"
            }
        ]

        print(f"Seeding {len(affiliates)} high-fidelity 2026 affiliate programs...")
        for aff in affiliates:
            # Avoid duplicates
            exists = db.query(AffiliateLinkDB).filter(
                AffiliateLinkDB.product_name == aff["product_name"],
                AffiliateLinkDB.user_id == user.id
            ).first()
            
            if not exists:
                new_link = AffiliateLinkDB(
                    user_id=user.id,
                    product_name=aff["product_name"],
                    niche=aff["niche"],
                    link=aff["link"],
                    cta_text=aff["cta_text"]
                )
                db.add(new_link)
        
        db.commit()
        print("✅ Intelligence Grounding Complete.")
        
    except Exception as e:
        print(f"❌ Grounding Failed: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_intelligence()

from api.utils.database import SessionLocal
from sqlalchemy import text

def verify():
    db = SessionLocal()
    try:
        # Check if 'views' column exists in 'content_candidates'
        result = db.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='content_candidates' AND column_name='views';"))
        column = result.fetchone()
        if column:
            print("✅ 'views' column exists.")
        else:
            print("❌ 'views' column MISSING.")
    finally:
        db.close()

if __name__ == "__main__":
    verify()

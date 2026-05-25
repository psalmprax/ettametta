import os
import sys

# Add the project root to sys.path
sys.path.append(os.getcwd())

print("Importing database engine and Base...")
from api.utils.database import engine, Base
print("Importing models...")
from api.utils.models import *
print("Importing user_models...")
from api.utils.user_models import *
print("Importing credit_models...")
from api.utils.credit_models import *

def init_db():
    print("Initializing database with new UUID-based schema...")
    print(f"Engine: {engine}")
    # Drop existing tables if any (safety check)
    Base.metadata.drop_all(bind=engine)
    print("Dropped old tables (if any).")
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("Database initialized successfully.")

if __name__ == "__main__":
    init_db()

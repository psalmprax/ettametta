import sqlite3
import uuid
import os
import sys

# Add the project root to sys.path to import our models
sys.path.append(os.getcwd())

from api.utils.database import Base
from api.utils.models import *
from api.utils.user_models import *
from api.utils.credit_models import *

OLD_DB = "ettametta.db"
NEW_DB = "ettametta_uuid.db"

def migrate():
    print(f"Starting migration from {OLD_DB} to {NEW_DB}...")

    if os.path.exists(NEW_DB):
        os.remove(NEW_DB)

    # Create new tables with UUID schema
    # We need to temporarily point the engine to the new DB
    import sqlalchemy
    
    new_engine = sqlalchemy.create_engine(f"sqlite:///{NEW_DB}")
    Base.metadata.create_all(new_engine)
    
    # We'll use raw sqlite3 for speed and easier mapping of old to new IDs
    old_conn = sqlite3.connect(OLD_DB)
    old_conn.row_factory = sqlite3.Row
    new_conn = sqlite3.connect(NEW_DB)
    
    # Mapping: {table_name: {old_id: new_uuid}}
    id_map = {}

    # 1. Migrate Users first (they are the root of most FKs)
    id_map['users'] = {}
    users = old_conn.execute("SELECT * FROM users").fetchall()
    for user in users:
        new_id = str(uuid.uuid4())
        id_map['users'][user['id']] = new_id
        
        cols = [c for c in user.keys() if c != 'id']
        vals = [user[c] for c in cols]
        placeholders = ",".join(["?"] * (len(cols) + 1))
        
        new_conn.execute(f"INSERT INTO users (id, {','.join(cols)}) VALUES ({placeholders})", [new_id] + vals)
    
    print(f"Migrated {len(users)} users.")

    # 2. Migrate Tables with FKs to users
    # Order matters if there are nested FKs
    
    # Tables that depend on users
    user_dependent_tables = [
        'user_settings', 'social_accounts', 'published_content', 'video_jobs',
        'monitored_niches', 'affiliate_links', 'revenue_logs', 'personas',
        'nexus_jobs', 'ab_tests', 'scheduled_posts', 'audit_logs',
        'opencli_sessions', 'discovery_interactions', 'trading_portfolios', 'trading_alerts', 'bot_codes',
        'user_credits', 'credit_transactions', 'referrals'
    ]
    
    for table in user_dependent_tables:
        if table not in id_map: id_map[table] = {}
        rows = old_conn.execute(f"SELECT * FROM {table}").fetchall()
        for row in rows:
            new_id = str(uuid.uuid4())
            id_map[table][row['id']] = new_id
            
            row_dict = dict(row)
            row_dict['id'] = new_id
            
            # Map user_id
            if 'user_id' in row_dict and row_dict['user_id'] in id_map['users']:
                row_dict['user_id'] = id_map['users'][row_dict['user_id']]
            
            # Map account_id for publishing tables
            if table in ['published_content', 'scheduled_posts'] and 'account_id' in row_dict:
                if row_dict['account_id'] in id_map['social_accounts']:
                    row_dict['account_id'] = id_map['social_accounts'][row_dict['account_id']]
                else:
                    # If account_id doesn't exist in map (maybe legacy null/0), set to None or keep as is
                    if row_dict['account_id'] == 0 or row_dict['account_id'] is None:
                        row_dict['account_id'] = None
            
            # Specific mappings
            if table == 'referrals':
                if row_dict['referrer_id'] in id_map['users']:
                    row_dict['referrer_id'] = id_map['users'][row_dict['referrer_id']]
                if row_dict['referred_id'] in id_map['users']:
                    row_dict['referred_id'] = id_map['users'][row_dict['referred_id']]
            
            cols = list(row_dict.keys())
            vals = [row_dict[c] for c in cols]
            placeholders = ",".join(["?"] * len(cols))
            new_conn.execute(f"INSERT INTO {table} ({','.join(cols)}) VALUES ({placeholders})", vals)
        print(f"Migrated {len(rows)} from {table}.")

    # 3. Migrate tables that depend on other tables (nested FKs)
    # trading_positions -> trading_portfolios
    # trading_transactions -> trading_portfolios
    
    nested_tables = [
        ('trading_positions', 'portfolio_id', 'trading_portfolios'),
        ('trading_transactions', 'portfolio_id', 'trading_portfolios')
    ]
    
    for table, fk_col, parent_table in nested_tables:
        rows = old_conn.execute(f"SELECT * FROM {table}").fetchall()
        for row in rows:
            new_id = str(uuid.uuid4())
            row_dict = dict(row)
            row_dict['id'] = new_id
            
            if row_dict[fk_col] in id_map[parent_table]:
                row_dict[fk_col] = id_map[parent_table][row_dict[fk_col]]
            
            cols = list(row_dict.keys())
            vals = [row_dict[c] for c in cols]
            placeholders = ",".join(["?"] * len(cols))
            new_conn.execute(f"INSERT INTO {table} ({','.join(cols)}) VALUES ({placeholders})", vals)
        print(f"Migrated {len(rows)} from {table}.")

    # 4. Migrate remaining tables (no user_id or already handled)
    remaining_tables = [
        'system_settings', 'video_filters', 'content_candidates', 'viral_patterns',
        'niche_trends', 'nexus_blueprints', 'ab_variants', 'ab_test_metrics',
        'system_activity', 'webhook_events', 'credit_packages', 'credit_usage_rules', 'subscription_credits'
    ]
    # Note: ab_variants/metrics might not be in models yet or handled by ab_tests JSON nodes. 
    # Let's check which tables actually exist in old_db.
    
    existing_tables = [r[0] for r in old_conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    
    for table in remaining_tables:
        if table not in existing_tables: continue
        if table in id_map or any(table == t[0] for t in nested_tables): continue
        
        rows = old_conn.execute(f"SELECT * FROM {table}").fetchall()
        for row in rows:
            # For tables like system_settings, id might be String already or we change to UUID
            row_dict = dict(row)
            if isinstance(row['id'], int):
                new_id = str(uuid.uuid4())
                row_dict['id'] = new_id
            
            cols = list(row_dict.keys())
            vals = [row_dict[c] for c in cols]
            placeholders = ",".join(["?"] * len(cols))
            new_conn.execute(f"INSERT INTO {table} ({','.join(cols)}) VALUES ({placeholders})", vals)
        print(f"Migrated {len(rows)} from {table}.")

    new_conn.commit()
    old_conn.close()
    new_conn.close()
    print("Migration successful.")

if __name__ == "__main__":
    try:
        migrate()
    except Exception as e:
        print(f"Migration failed: {e}")
        import traceback
        traceback.print_exc()

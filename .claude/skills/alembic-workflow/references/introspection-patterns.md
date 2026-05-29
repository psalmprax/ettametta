# Introspection-Based Migration Patterns

When migrations need to be safe against databases in unknown states, use SQLAlchemy's inspector to check before modifying.

## Check if Table Exists

```python
from sqlalchemy import inspect as sa_inspect

def upgrade():
    bind = op.get_bind()
    inspector = sa_inspect(bind)
    
    if 'my_table' not in inspector.get_table_names():
        op.create_table(
            'my_table',
            sa.Column('id', sa.Integer, primary_key=True),
            sa.Column('name', sa.String(255), nullable=False),
        )
```

## Check if Column Exists

```python
def upgrade():
    bind = op.get_bind()
    inspector = sa_inspect(bind)
    columns = [c['name'] for c in inspector.get_columns('my_table')]
    
    if 'new_column' not in columns:
        op.add_column('my_table', sa.Column('new_column', sa.String(255)))
```

## Check if Index Exists

```python
def upgrade():
    bind = op.get_bind()
    inspector = sa_inspect(bind)
    indexes = [i['name'] for i in inspector.get_indexes('my_table')]
    
    if 'ix_my_table_new_column' not in indexes:
        op.create_index('ix_my_table_new_column', 'my_table', ['new_column'])
```

## Check if Constraint Exists

```python
def upgrade():
    bind = op.get_bind()
    inspector = sa_inspect(bind)
    constraints = inspector.get_unique_constraints('my_table')
    constraint_names = [c['name'] for c in constraints]
    
    if 'uq_my_table_name' not in constraint_names:
        op.create_unique_constraint('uq_my_table_name', 'my_table', ['name'])
```

## Rename Column Safely

```python
def upgrade():
    bind = op.get_bind()
    inspector = sa_inspect(bind)
    columns = [c['name'] for c in inspector.get_columns('my_table')]
    
    if 'old_name' in columns and 'new_name' not in columns:
        op.alter_column('my_table', 'old_name', new_column_name='new_name')
```

## Conditional Data Migration

```python
def upgrade():
    bind = op.get_bind()
    inspector = sa_inspect(bind)
    columns = [c['name'] for c in inspector.get_columns('my_table')]
    
    if 'status' in columns and 'new_status' not in columns:
        # Add new column
        op.add_column('my_table', sa.Column('new_status', sa.String(50)))
        
        # Migrate data
        op.execute("UPDATE my_table SET new_status = status WHERE new_status IS NULL")
        
        # Optionally drop old column
        op.drop_column('my_table', 'status')
```

## When to Use Introspection

| Scenario | Use Introspection? |
|----------|-------------------|
| Fresh database (dev/CI) | No — autogenerate is fine |
| Production with unknown manual changes | **Yes** |
| Fixing a previously failed migration | **Yes** |
| Multiple developers with different schema states | **Yes** |
| Adding a new column to an existing table | Recommended |
| Creating a new table | Optional (check first is safer) |

## Real Examples from ettametta

### 83a4ab83e579 (fix_missing_metrics_columns)

```python
def upgrade():
    bind = op.get_bind()
    inspector = sa_inspect(bind)
    
    # Check content_candidates table
    columns = [c['name'] for c in inspector.get_columns('content_candidates')]
    
    if 'engagement_rate' not in columns:
        op.add_column('content_candidates', sa.Column('engagement_rate', sa.Float))
    
    if 'viral_score' not in columns:
        op.add_column('content_candidates', sa.Column('viral_score', sa.Float))
```

### e7b99c2d1f4a (fix_ab_tests_naming)

```python
def upgrade():
    bind = op.get_bind()
    inspector = sa_inspect(bind)
    
    columns = [c['name'] for c in inspector.get_columns('ab_tests')]
    
    if 'test_name' in columns and 'name' not in columns:
        op.alter_column('ab_tests', 'test_name', new_column_name='name')
```

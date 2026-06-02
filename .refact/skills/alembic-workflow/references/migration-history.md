# Migration History Details

## Full Revision Chain

```
a4b1aaadd072 (initial_migration)
  │
  ├── 001_create_user_table ──────────────┐
  ├── add_user_id_monitored_niches ───────┤ (separate root branches)
  └── b2c3d4e5f6g7_add_is_google_oauth ──┤
                                           │
                                    merge_heads_2026 (3-way merge)
                                           │
                                    c8d2e4f5g6h7 (discovery_metrics)
                                           │
                                    2aa1c8c2bf49 (metrics to published_content)
                                           │
                                    86ebe6287aea (more metrics)
                                           │
                                    a1b2c3d4e5f (user_id to affiliate_links)
                                           │
  a1b2c3d4e5f6 (drop url column) ─┐      │
                                    ├─ efb25ef5b164 (2-way merge)
  ee8627d8341b (scheduled_posts) ──┘      │
                                           │
                                    260bae1bf65b (credit_system_tables)
                                           │
                                    f1b2c3d4e5f6 (align source_url)
                                           │
                                    g1b2c3d4e5f7 (composition_id to blueprints)
                                           │
                                    d410fb0d40a9 (align_production_schema)
                                           │
                                    83a4ab83e579 (fix_missing_metrics — introspection)
                                           │
                                    e7b99c2d1f4a (fix_ab_tests_naming — introspection)
```

## Migration Descriptions

| Revision | Description | Pattern |
|----------|-------------|---------|
| `a4b1aaadd072` | Initial: creates system_settings, modifies content_candidates | Standard autogenerate |
| `001_create_user_table` | Creates users table | Standard |
| `add_user_id_monitored_niches` | Adds user_id FK to monitored_niches | Standard |
| `b2c3d4e5f6g7` | Adds is_google_oauth fields | Standard |
| `merge_heads_2026` | Merges 3 separate root branches | Merge |
| `c8d2e4f5g6h7` | Discovery metrics columns | Standard |
| `2aa1c8c2bf49` | Published content metrics | Standard |
| `86ebe6287aea` | More published content metrics | Standard |
| `a1b2c3d4e5f` | User ID on affiliate links | Standard |
| `ee8627d8341b` | Scheduled posts columns | Standard |
| `a1b2c3d4e5f6` | Drops URL column from content_candidates | Standard |
| `efb25ef5b164` | Merges 2 separate branches | Merge |
| `260bae1bf65b` | Credit system (6 new tables) | Standard |
| `f1b2c3d4e5f6` | Source URL alignment | Standard |
| `g1b2c3d4e5f7` | Composition ID on blueprints | Standard |
| `d410fb0d40a9` | Large schema alignment (agent_zero_state, lead_gen_configs, URI migration) | Standard |
| `83a4ab83e579` | Fix missing metrics columns via introspection | **Introspection** |
| `e7b99c2d1f4a` | Fix AB test column naming via introspection | **Introspection** |

## Merge Points

1. `merge_heads_2026` — Joins `001_create_user_table`, `add_user_id_monitored_niches`, `b2c3d4e5f6g7`
2. `efb25ef5b164` — Joins `a1b2c3d4e5f6` and `ee8627d8341b`

## Introspection-Based Migrations

Two migrations use `Inspector.from_engine()` for defensive schema checks:

### 83a4ab83e579 (fix_missing_metrics_columns)
- Checks if columns exist before adding them
- Uses `inspector.get_columns('table_name')`
- Handles databases that may already have the columns

### e7b99c2d1f4a (fix_ab_tests_naming)
- Fixes column naming inconsistencies
- Uses introspection to check current column names
- Conditionally renames columns

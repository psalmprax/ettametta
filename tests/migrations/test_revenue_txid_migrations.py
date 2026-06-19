"""Tests for the 2026-06-16 revenue_logs migrations.

Covers:

  (a) ``alembic/versions/2026_06_16_revenue_metadata.py`` — adds the
      ``metadata_json`` column to ``revenue_logs`` (idempotent, schema-
      qualified existence check, ``DROP COLUMN IF EXISTS`` downgrade).

  (b) ``alembic/versions/2026_06_16_backfill_txid.py`` — backfills
      ``revenue_logs.transaction_id`` from ``metadata_json->>'transaction_id'``
      using a two-step CTE that deterministically picks the oldest
      duplicate per ``(platform, transaction_id)`` group (MVCC-safe).

The unit tests below parse the migration files with ``ast`` and assert
on the extracted structure. They do NOT require a running database —
they protect against accidental regressions in the migration file
itself (e.g. someone removing the ``IF NOT EXISTS`` check, inlining
the CTE, or changing the chain).

The optional ``TestBackfillFixturesOnPostgres`` class runs the
migrations against a real Postgres (the one configured by
``DATABASE_URL``) and verifies the 7-fixture behavior end-to-end. It
is skipped automatically if ``DATABASE_URL`` is not set, so this file
is safe to run in CI without a database.
"""
from __future__ import annotations

import ast
import os
import re
import textwrap
from pathlib import Path
from typing import Any

import pytest


# ─────────────────────────────────────────────────────────────────────────────
# Paths + helpers
# ─────────────────────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parents[2]  # tests/migrations/<file>.py → repo root
ALEMBIC_VERSIONS = REPO_ROOT / "alembic" / "versions"

MIGRATION_COLUMN_ADD = "2026_06_16_revenue_metadata.py"
MIGRATION_BACKFILL = "2026_06_16_backfill_txid.py"


def _load_module(filename: str) -> ast.Module:
    """Parse a migration file as an AST module."""
    path = ALEMBIC_VERSIONS / filename
    if not path.exists():
        pytest.skip(f"migration file not found: {path}")
    return ast.parse(path.read_text(), filename=str(path))


def _module_assign(module: ast.Module, target: str) -> Any:
    """Return the value of a top-level ``target = ...`` assignment.

    Raises ``AssertionError`` if not present, or ``pytest.skip`` if the
    file is missing.
    """
    for node in module.body:
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == target:
                    return ast.literal_eval(node.value)
    raise AssertionError(f"module has no top-level `{target} = ...`")


def _op_execute_sql(func: ast.FunctionDef) -> str:
    """Return the SQL string passed to ``op.execute(sa.text("..."))``.

    Returns the FIRST match; the migrations we test each have exactly
    one ``op.execute`` call per direction (upgrade / downgrade).
    """
    for node in ast.walk(func):
        if not isinstance(node, ast.Call):
            continue
        # Look for op.execute(...)
        if not (
            isinstance(node.func, ast.Attribute)
            and node.func.attr == "execute"
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "op"
        ):
            continue
        if not node.args:
            continue
        first = node.args[0]
        # unwrap sa.text("...") → "..."
        if (
            isinstance(first, ast.Call)
            and isinstance(first.func, ast.Attribute)
            and first.func.attr == "text"
        ) and first.args:
            return ast.literal_eval(first.args[0])
    raise AssertionError("no op.execute(sa.text(...)) call found in function")


def _module_func(module: ast.Module, name: str) -> ast.FunctionDef:
    """Return the top-level function with the given name."""
    for node in module.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise AssertionError(f"module has no function `{name}()`")


def _module_const(module: ast.Module, name: str) -> str:
    """Return the value of a module-level constant whose value is a SQL
    string (e.g. ``_BACKFILL_SQL = sa.text("...")``). Unwraps the
    ``sa.text(...)`` call.

    ``ast.literal_eval`` only handles literals, so it can't unwrap a
    Call node. We do the unwrapping manually for the two shapes we
    see in these migrations: a bare string literal, or
    ``sa.text("...")`` / ``sa.text(\"\"\"...\"\"\")``.
    """
    for node in module.body:
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == name:
                    value = node.value
                    if isinstance(value, ast.Constant) and isinstance(value.value, str):
                        return value.value
                    if isinstance(value, ast.Call) and value.args:
                        first = value.args[0]
                        if isinstance(first, ast.Constant) and isinstance(first.value, str):
                            return first.value
                    raise AssertionError(
                        f"constant `{name}` is not a string literal or sa.text(...) call"
                    )
    raise AssertionError(f"module has no constant `{name}`")


# ─────────────────────────────────────────────────────────────────────────────
# (a) Upgrade chain is well-formed
# ─────────────────────────────────────────────────────────────────────────────


def _all_migration_modules() -> dict[str, ast.Module]:
    """Parse every migration file in alembic/versions/ and return
    ``{revision_id: module}`` for each one with a top-level
    ``revision = "..."`` assignment."""
    if not ALEMBIC_VERSIONS.exists():
        pytest.skip(f"alembic versions dir not found: {ALEMBIC_VERSIONS}")
    out: dict[str, ast.Module] = {}
    for path in sorted(ALEMBIC_VERSIONS.glob("*.py")):
        if path.name.startswith("_") or path.name == "env.py":
            continue
        try:
            mod = ast.parse(path.read_text(), filename=str(path))
        except SyntaxError:
            continue
        try:
            rev = _module_assign(mod, "revision")
        except AssertionError:
            continue
        if isinstance(rev, str):
            out[rev] = mod
    return out


class TestUpgradeChainWellFormed:
    def test_backfill_txid_is_a_head_of_the_dag(self):
        """The backfill migration is a head of the alembic DAG — nothing
        in ``alembic/versions/`` lists it as a ``down_revision``.

        NOTE: the DAG may have OTHER heads from unrelated in-progress
        branches (e.g. ``2026_05_29_merge_heads`` left over from an
        earlier merge attempt, or ``g1b2c3d4e5f7`` from a future
        phase). Those are out of scope for this test — the contract
        we're verifying is that the backfill sits at the tip of the
        ``webhook-idempotency-fix`` branch and nothing further depends
        on it yet.
        """
        modules = _all_migration_modules()
        assert modules, "no migration modules found in alembic/versions/"

        # Collect every down_revision (can be str, tuple of str, or None).
        downs: set[str] = set()
        for mod in modules.values():
            try:
                dr = _module_assign(mod, "down_revision")
            except AssertionError:
                continue
            if dr is None:
                continue
            if isinstance(dr, str):
                downs.add(dr)
            else:
                for d in dr:
                    if isinstance(d, str):
                        downs.add(d)

        assert "2026_06_16_backfill_txid" in modules
        assert "2026_06_16_backfill_txid" not in downs, (
            "2026_06_16_backfill_txid should be a head (nothing lists "
            "it as a down_revision)"
        )

    def test_backfill_txid_down_revision_chain_is_well_formed(self):
        """The backfill's direct down_revision chain is well-formed:

            2026_06_16_backfill_txid
              -> 2026_06_16_revenue_metadata
              -> merge_remaining_2026
              -> (2-way merge: 2026_05_29_revenue_txid,
                  2026_05_29_analysis_persistence)

        Two additional branches (66623ae9808f, impression_tracking) were
        stamped directly to the DB without migration files and are NOT
        referenced in merge_remaining_2026's down_revision.
        """
        modules = _all_migration_modules()
        assert "2026_06_16_backfill_txid" in modules
        assert "2026_06_16_revenue_metadata" in modules
        assert "merge_remaining_2026" in modules

        assert (
            _module_assign(modules["2026_06_16_backfill_txid"], "down_revision")
            == "2026_06_16_revenue_metadata"
        )
        assert (
            _module_assign(modules["2026_06_16_revenue_metadata"], "down_revision")
            == "merge_remaining_2026"
        )

        dr = _module_assign(modules["merge_remaining_2026"], "down_revision")
        assert isinstance(dr, tuple), (
            "merge_remaining_2026's down_revision should be a tuple "
            "(it's a 2-way merge migration)"
        )
        assert len(dr) == 2

        # Both parents must be present as files.
        for d in dr:
            assert d in modules, (
                f"merge parent {d} must have a migration file"
            )
            assert _module_assign(modules[d], "revision") == d

        assert "2026_05_29_revenue_txid" in dr
        assert "2026_05_29_analysis_persistence" in dr

    def test_backfill_txid_chains_off_column_add(self):
        """``down_revision`` of the backfill is the column-add migration."""
        mod = _load_module(MIGRATION_BACKFILL)
        assert _module_assign(mod, "down_revision") == "2026_06_16_revenue_metadata"
        assert _module_assign(mod, "revision") == "2026_06_16_backfill_txid"

    def test_column_add_chains_off_merge_remaining_2026(self):
        """``down_revision`` of the column-add is the previous head."""
        mod = _load_module(MIGRATION_COLUMN_ADD)
        assert _module_assign(mod, "down_revision") == "merge_remaining_2026"
        assert _module_assign(mod, "revision") == "2026_06_16_revenue_metadata"

    def test_child_migrations_use_null_branch_label(self):
        """Both child migrations use branch_labels=None to avoid conflicting
        with the parent revision (2026_05_29_revenue_txid) which already owns
        the 'webhook-idempotency-fix' branch label."""
        col_add = _load_module(MIGRATION_COLUMN_ADD)
        backfill = _load_module(MIGRATION_BACKFILL)
        assert _module_assign(col_add, "branch_labels") is None
        assert _module_assign(backfill, "branch_labels") is None


# ─────────────────────────────────────────────────────────────────────────────
# (b) Column-add migration is idempotent
# ─────────────────────────────────────────────────────────────────────────────


class TestColumnAddIdempotency:
    def test_upgrade_uses_information_schema_existence_check(self):
        mod = _load_module(MIGRATION_COLUMN_ADD)
        sql = _op_execute_sql(_module_func(mod, "upgrade"))
        assert "information_schema.columns" in sql
        assert "IF NOT EXISTS" in sql

    def test_upgrade_existence_check_is_schema_qualified(self):
        """The check must include ``table_schema = current_schema()`` to avoid
        matching a same-named column in a different schema (e.g. Dify's
        ``langgenius`` schema lives in the same cluster)."""
        mod = _load_module(MIGRATION_COLUMN_ADD)
        sql = _op_execute_sql(_module_func(mod, "upgrade"))
        assert "table_schema = current_schema()" in sql

    def test_upgrade_alters_only_revenue_logs(self):
        mod = _load_module(MIGRATION_COLUMN_ADD)
        sql = _op_execute_sql(_module_func(mod, "upgrade"))
        assert "table_name = 'revenue_logs'" in sql
        assert "column_name = 'metadata_json'" in sql
        assert "ALTER TABLE revenue_logs" in sql
        assert "ADD COLUMN metadata_json JSON" in sql

    def test_upgrade_alter_is_inside_a_do_block(self):
        """The ALTER is wrapped in ``DO $$ ... END$$;`` so the entire migration
        is a single statement — re-runs are a no-op because the IF check
        short-circuits the ALTER."""
        mod = _load_module(MIGRATION_COLUMN_ADD)
        sql = _op_execute_sql(_module_func(mod, "upgrade"))
        assert "DO $$" in sql
        assert "END$$" in sql

    def test_downgrade_uses_drop_column_if_exists(self):
        """``DROP COLUMN IF EXISTS`` so downgrade is a no-op if the column
        is already gone (idempotent in both directions)."""
        mod = _load_module(MIGRATION_COLUMN_ADD)
        sql = _op_execute_sql(_module_func(mod, "downgrade"))
        assert "DROP COLUMN IF EXISTS metadata_json" in sql

    def test_downgrade_warns_in_docstring_that_dispatcher_will_break(self):
        """The docstring must warn operators that the dispatcher will start
        failing with 'column does not exist' immediately after downgrade."""
        mod = _load_module(MIGRATION_COLUMN_ADD)
        doc = ast.get_docstring(_module_func(mod, "downgrade")) or ""
        assert "column does not exist" in doc


# ─────────────────────────────────────────────────────────────────────────────
# (c) Backfill migration: structure + 7-fixture behavior
# ─────────────────────────────────────────────────────────────────────────────


class TestBackfillStructure:
    def test_backfill_sql_uses_two_step_cte(self):
        """The MVCC gotcha requires a two-step CTE so winners are
        materialized BEFORE the UPDATE writes. Verify the structure
        directly so a future 'simplification' doesn't re-introduce the
        bug.

        Whitespace is normalized before matching because the migration
        uses a multi-line string with newlines between the CTEs
        (``),\n    ranked AS (``), so a naive substring search would
        miss the second CTE."""
        mod = _load_module(MIGRATION_BACKFILL)
        sql = _module_const(mod, "_BACKFILL_SQL")
        sql_n = " ".join(sql.split())  # collapse all whitespace
        assert "WITH candidates AS" in sql_n
        assert "ranked AS" in sql_n
        # The UPDATE must join against the pre-computed `ranked` set.
        assert "FROM ranked" in sql_n
        assert "ranked.rn = 1" in sql_n

    def test_candidates_filter_is_json_portable(self):
        """The existence check must use ``COALESCE(... ->> ..., '') <> ''``
        (works on both JSON and JSONB) — NOT the JSONB-only ``?`` operator."""
        mod = _load_module(MIGRATION_BACKFILL)
        sql = _module_const(mod, "_BACKFILL_SQL")
        assert "COALESCE(metadata_json->>'transaction_id', '')" in sql
        assert "<> ''" in sql
        assert "metadata_json ?" not in sql  # JSONB-only, must not be used

    def test_candidates_filter_excludes_already_backfilled_rows(self):
        """A second run is a no-op because the WHERE clause restricts to
        rows with ``transaction_id IS NULL``."""
        mod = _load_module(MIGRATION_BACKFILL)
        sql = _module_const(mod, "_BACKFILL_SQL")
        assert "transaction_id IS NULL" in sql
        assert "metadata_json IS NOT NULL" in sql

    def test_ranking_uses_oldest_date_with_id_tiebreak(self):
        """The deterministic winner is the row with the oldest ``date``;
        ``id`` is the tiebreak (UUIDs are random, so ``ORDER BY id``
        alone would be non-deterministic for human review)."""
        mod = _load_module(MIGRATION_BACKFILL)
        sql = _module_const(mod, "_BACKFILL_SQL")
        assert "ROW_NUMBER() OVER" in sql
        assert "PARTITION BY platform, txid" in sql
        assert "ORDER BY date, id" in sql

    def test_candidates_includes_date_so_ranked_does_not_need_to_join(self):
        """The simplified form pulls ``date`` into the ``candidates`` CTE
        so the ``ranked`` CTE does NOT have to JOIN back to revenue_logs.
        This is a structural property — if someone re-introduces the
        JOIN, the test catches it.

        We match the CTE bodies with regex (not string splitting) because
        the migration uses a multi-line string with arbitrary whitespace."""
        mod = _load_module(MIGRATION_BACKFILL)
        sql = _module_const(mod, "_BACKFILL_SQL")
        sql_n = " ".join(sql.split())
        candidates_match = re.search(
            r"candidates AS\s*\((.*?)\)\s*,\s*ranked AS",
            sql_n,
            re.DOTALL,
        )
        assert candidates_match, "could not find candidates CTE in _BACKFILL_SQL"
        assert "date" in candidates_match.group(1), (
            "candidates CTE must select `date` so ranked can ORDER BY date "
            "without JOINing back to revenue_logs"
        )
        ranked_match = re.search(
            r"ranked AS\s*\((.*?)\)\s*UPDATE",
            sql_n,
            re.DOTALL,
        )
        assert ranked_match, "could not find ranked CTE in _BACKFILL_SQL"
        assert "JOIN" not in ranked_match.group(1).upper(), (
            "ranked CTE must not JOIN back to revenue_logs (it should "
            "derive from candidates only, which already includes `date`)"
        )

    def test_loser_row_query_in_docstring_is_json_portable(self):
        """The docstring suggests a query for identifying loser rows. It
        must use the COALESCE form (JSON-portable), NOT the ``?`` operator."""
        path = ALEMBIC_VERSIONS / MIGRATION_BACKFILL
        docstring = ast.get_docstring(ast.parse(path.read_text())) or ""
        assert "COALESCE(metadata_json->>'transaction_id', '')" in docstring
        # The docstring's example query should NOT use `?` (JSONB-only).
        assert "metadata_json ? 'transaction_id'" not in docstring

    def test_upgrade_prints_rowcount(self):
        """The migration prints a rowcount line so operators see what ran
        (alembic surfaces print() to the operator running
        ``alembic upgrade head``)."""
        mod = _load_module(MIGRATION_BACKFILL)
        upgrade_func = _module_func(mod, "upgrade")
        src = ast.unparse(upgrade_func)
        assert "print(" in src
        assert "result.rowcount" in src
        assert "[backfill_txid]" in src

    def test_downgrade_is_intentional_noop(self):
        """``downgrade()`` is a ``pass`` — un-setting transaction_id would
        lose information. Verify the docstring explains this.

        Note: a function's ``body`` includes the leading docstring as an
        ``ast.Expr`` node, so we filter that out before checking the
        remaining executable statements.
        """
        mod = _load_module(MIGRATION_BACKFILL)
        down = _module_func(mod, "downgrade")
        executable = [
            n
            for n in down.body
            if not (
                isinstance(n, ast.Expr)
                and isinstance(n.value, ast.Constant)
                and isinstance(n.value.value, str)
            )
        ]
        assert len(executable) == 1 and isinstance(executable[0], ast.Pass)
        doc = ast.get_docstring(down) or ""
        assert "lose information" in doc


# ─────────────────────────────────────────────────────────────────────────────
# (c.2) Backfill: 7 fixtures — runs against a real Postgres
# ─────────────────────────────────────────────────────────────────────────────
#
# These tests require a running Postgres. They are skipped automatically
# if DATABASE_URL is not set, so the file is safe to run in CI without a
# database. To run them locally:
#
#   DATABASE_URL=postgresql://ettametta:<password>@<host>:5432/ettametta \
#     pytest tests/migrations/test_revenue_txid_migrations.py -v
#
# The tests use a temporary schema so they don't touch any existing data
# in the target database. The schema is dropped at the end of the session.


@pytest.fixture(scope="module")
def pg_db_url() -> str:
    """Return DATABASE_URL or skip the test."""
    url = os.environ.get("DATABASE_URL")
    if not url:
        pytest.skip("DATABASE_URL not set; skipping Postgres-backed tests")
    return url


@pytest.fixture(scope="module")
def pg_schema(pg_db_url: str):
    """Create a temporary schema, yield its name, drop it on teardown."""
    import psycopg2  # local import so non-DB tests don't require it

    conn = psycopg2.connect(pg_db_url)
    conn.autocommit = True
    cur = conn.cursor()
    schema = "test_revenue_txid_migrations"
    cur.execute(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE')
    cur.execute(f'CREATE SCHEMA "{schema}"')
    cur.execute(f'SET search_path TO "{schema}"')
    cur.close()
    conn.close()
    yield schema
    conn = psycopg2.connect(pg_db_url)
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE')
    cur.close()
    conn.close()


# The 7 fixtures from the docker test on 2026-06-16:
#   a-001, a-002: duplicate (platform, transaction_id) — a-001 is older
#   b-001:        normal backfill candidate
#   c-001:        NULL metadata_json
#   d-001:        metadata_json without the 'transaction_id' key
#   e-001:        metadata_json with empty-string transaction_id
#   f-001:        already-set transaction_id (new code path)
_FIXTURES: list[tuple[str, str, str, str, str]] = [
    # (id, platform, date, transaction_id_or_empty, metadata_json_or_empty)
    ("a-001", "affiliate_impact",  "2026-01-01", "", '{"transaction_id": "tx-abc-001"}'),
    ("a-002", "affiliate_impact",  "2026-01-02", "", '{"transaction_id": "tx-abc-001"}'),
    ("b-001", "affiliate_sharesale", "2026-01-03", "", '{"transaction_id": "tx-xyz-002"}'),
    ("c-001", "affiliate_impact",  "2026-01-04", "", ""),  # NULL metadata_json
    ("d-001", "affiliate_impact",  "2026-01-05", "", '{"other_key": "value"}'),
    ("e-001", "affiliate_impact",  "2026-01-06", "", '{"transaction_id": ""}'),
    ("f-001", "affiliate_impact",  "2026-01-07", "tx-already-set-007", '{"transaction_id": "tx-IGNORED-007"}'),
]


def _setup_revenue_logs(pg_db_url: str, schema: str) -> None:
    """Create the revenue_logs table matching the production schema
    (all columns except metadata_json, which the column-add migration adds).

    The ``pg_schema`` fixture is ``scope="module"`` (created once per
    test module for speed), so the table persists across tests. To
    keep the tests independent, we ``DROP TABLE IF EXISTS`` at the
    start of each call so every test starts from a clean slate.
    """
    import psycopg2

    conn = psycopg2.connect(pg_db_url)
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute(f'SET search_path TO "{schema}"')
    cur.execute("DROP TABLE IF EXISTS revenue_logs CASCADE")
    cur.execute(
        """
        CREATE TABLE revenue_logs (
            id VARCHAR(36) PRIMARY KEY,
            platform VARCHAR NOT NULL,
            niche VARCHAR,
            amount DOUBLE PRECISION DEFAULT 0.0,
            view_count INTEGER DEFAULT 0,
            date TIMESTAMP,
            user_id VARCHAR(36),
            transaction_id VARCHAR(128)
        )
        """
    )
    cur.execute(
        "CREATE UNIQUE INDEX uix_revenue_platform_txid "
        "ON revenue_logs (platform, transaction_id)"
    )
    cur.execute(
        "CREATE INDEX ix_revenue_logs_transaction_id ON revenue_logs (transaction_id)"
    )
    cur.close()
    conn.close()


def _insert_fixtures(pg_db_url: str, schema: str) -> None:
    import psycopg2

    conn = psycopg2.connect(pg_db_url)
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute(f'SET search_path TO "{schema}"')
    for fid, platform, date, txid, md in _FIXTURES:
        # Fully parameterized insert — empty string means NULL. The
        # metadata_json column is cast via `::json` so the JSON literal
        # is parsed by Postgres (not by Python's str()). The niche
        # value is derived from the row id and passed as a plain
        # string parameter (no SQL string interpolation; safe).
        cur.execute(
            "INSERT INTO revenue_logs (id, platform, niche, amount, view_count, "
            "date, user_id, transaction_id, metadata_json) VALUES "
            "(%s, %s, %s, 10.0, 1, %s, 'u1', %s, %s::json)",
            (
                fid,
                platform,
                f"niche-{fid}",
                date,
                None if txid == "" else txid,
                None if md == "" else md,
            ),
        )
    cur.close()
    conn.close()


def _run_migration_sql(pg_db_url: str, schema: str, migration_filename: str, direction: str) -> None:
    """Execute the upgrade() or downgrade() of the given migration against
    the temp schema. Uses the raw SQL extracted from the migration file
    (no alembic context required)."""
    import psycopg2

    mod = _load_module(migration_filename)
    sql = _op_execute_sql(_module_func(mod, direction))
    conn = psycopg2.connect(pg_db_url)
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute(f'SET search_path TO "{schema}"')
    cur.execute(sql)
    cur.close()
    conn.close()


def _run_backfill(pg_db_url: str, schema: str) -> int:
    """Execute the backfill UPDATE (not wrapped in alembic) and return
    the number of rows updated."""
    import psycopg2

    mod = _load_module(MIGRATION_BACKFILL)
    sql = _module_const(mod, "_BACKFILL_SQL")
    conn = psycopg2.connect(pg_db_url)
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute(f'SET search_path TO "{schema}"')
    cur.execute(sql)
    rowcount = cur.rowcount
    cur.close()
    conn.close()
    return rowcount


def _query(pg_db_url: str, schema: str, sql: str) -> list[tuple]:
    import psycopg2

    conn = psycopg2.connect(pg_db_url)
    cur = conn.cursor()
    cur.execute(f'SET search_path TO "{schema}"')
    cur.execute(sql)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


class TestBackfillFixturesOnPostgres:
    def test_column_add_makes_metadata_json_column(self, pg_db_url, pg_schema):
        _setup_revenue_logs(pg_db_url, pg_schema)
        _run_migration_sql(pg_db_url, pg_schema, MIGRATION_COLUMN_ADD, "upgrade")

        rows = _query(
            pg_db_url,
            pg_schema,
            "SELECT column_name, data_type FROM information_schema.columns "
            "WHERE table_name = 'revenue_logs' AND column_name = 'metadata_json'",
        )
        assert rows == [("metadata_json", "json")]

    def test_column_add_is_idempotent_running_twice(self, pg_db_url, pg_schema):
        """Running the column-add upgrade a second time is a no-op."""
        _setup_revenue_logs(pg_db_url, pg_schema)
        _run_migration_sql(pg_db_url, pg_schema, MIGRATION_COLUMN_ADD, "upgrade")
        # Second run must not raise — the IF NOT EXISTS check short-circuits.
        _run_migration_sql(pg_db_url, pg_schema, MIGRATION_COLUMN_ADD, "upgrade")
        # Column still present, still JSON.
        rows = _query(
            pg_db_url,
            pg_schema,
            "SELECT data_type FROM information_schema.columns "
            "WHERE table_name = 'revenue_logs' AND column_name = 'metadata_json'",
        )
        assert rows == [("json",)]

    def test_column_add_downgrade_is_idempotent_on_empty_db(
        self, pg_db_url, pg_schema
    ):
        """``DROP COLUMN IF EXISTS`` makes downgrade a no-op on a DB that
        never had the column (matches the ``revenue_logs`` state on a
        fresh init where the column-add migration was never run)."""
        _setup_revenue_logs(pg_db_url, pg_schema)
        # Column does NOT exist yet — downgrade must not raise.
        _run_migration_sql(pg_db_url, pg_schema, MIGRATION_COLUMN_ADD, "downgrade")
        rows = _query(
            pg_db_url,
            pg_schema,
            "SELECT count(*) FROM information_schema.columns "
            "WHERE table_name = 'revenue_logs' AND column_name = 'metadata_json'",
        )
        assert rows == [(0,)]

    def test_backfill_oldest_wins_for_duplicate_pair(self, pg_db_url, pg_schema):
        """a-001 (date=2026-01-01) is older than a-002 (date=2026-01-02),
        both share the same (platform, transaction_id) → a-001 should
        get the backfilled txid, a-002 should stay NULL."""
        _setup_revenue_logs(pg_db_url, pg_schema)
        _run_migration_sql(pg_db_url, pg_schema, MIGRATION_COLUMN_ADD, "upgrade")
        _insert_fixtures(pg_db_url, pg_schema)

        rowcount = _run_backfill(pg_db_url, pg_schema)
        # a-001 (winner) + b-001 + f-001 (already set) = 3 non-null rows.
        # But f-001 is already set so it isn't in the candidates. The
        # UPDATE only writes winners that had NULL — that's a-001 + b-001.
        assert rowcount == 2

        rows = _query(
            pg_db_url,
            pg_schema,
            "SELECT id, transaction_id FROM revenue_logs ORDER BY id",
        )
        by_id = dict(rows)
        assert by_id["a-001"] == "tx-abc-001"  # winner (oldest)
        assert by_id["a-002"] is None  # loser (duplicate, stays NULL)
        assert by_id["b-001"] == "tx-xyz-002"  # normal backfill
        assert by_id["c-001"] is None  # NULL metadata
        assert by_id["d-001"] is None  # metadata without txid key
        assert by_id["e-001"] is None  # empty-string txid
        assert by_id["f-001"] == "tx-already-set-007"  # untouched

    def test_backfill_is_idempotent_on_rerun(self, pg_db_url, pg_schema):
        """Re-running the backfill should be a true no-op — 0 rows updated.

        The candidates CTE excludes groups that already have a non-NULL
        transaction_id (via a NOT IN subquery), so the loser row (a-002)
        is skipped on the second run."""
        _setup_revenue_logs(pg_db_url, pg_schema)
        _run_migration_sql(pg_db_url, pg_schema, MIGRATION_COLUMN_ADD, "upgrade")
        _insert_fixtures(pg_db_url, pg_schema)

        first = _run_backfill(pg_db_url, pg_schema)
        second = _run_backfill(pg_db_url, pg_schema)

        # With the fix, both runs should write the same 2 rows (a-001, b-001).
        # a-002 is the loser and must stay NULL on the second run.
        assert first == 2
        assert second == 0, (
            f"second run should be a no-op (0 rows updated), got {second}. "
            f"The migration's candidates CTE needs to exclude groups that "
            f"already have a non-NULL transaction_id."
        )

        # Final state: a-002 stays NULL (the loser, untouched on re-run).
        rows = _query(
            pg_db_url,
            pg_schema,
            "SELECT id, transaction_id FROM revenue_logs ORDER BY id",
        )
        by_id = dict(rows)
        assert by_id["a-001"] == "tx-abc-001"
        assert by_id["a-002"] is None  # LOSER: must stay NULL on re-run
        assert by_id["b-001"] == "tx-xyz-002"

    def test_json_portable_existence_check_skips_null_and_empty(
        self, pg_db_url, pg_schema
    ):
        """The COALESCE(... ->> ..., '') <> '' check (works on JSON, not
        just JSONB) correctly skips rows with NULL metadata_json, rows
        with metadata_json missing the key, and rows with empty-string
        txid. c-001, d-001, e-001 all stay NULL after the backfill."""
        _setup_revenue_logs(pg_db_url, pg_schema)
        _run_migration_sql(pg_db_url, pg_schema, MIGRATION_COLUMN_ADD, "upgrade")
        _insert_fixtures(pg_db_url, pg_schema)
        _run_backfill(pg_db_url, pg_schema)

        rows = _query(
            pg_db_url,
            pg_schema,
            "SELECT id, transaction_id FROM revenue_logs "
            "WHERE id IN ('c-001', 'd-001', 'e-001') ORDER BY id",
        )
        assert rows == [
            ("c-001", None),
            ("d-001", None),
            ("e-001", None),
        ]

    def test_loser_row_query_matches_docstring(self, pg_db_url, pg_schema):
        """The docstring's example query for identifying loser rows must
        return the same rows that the backfill left as NULL."""
        _setup_revenue_logs(pg_db_url, pg_schema)
        _run_migration_sql(pg_db_url, pg_schema, MIGRATION_COLUMN_ADD, "upgrade")
        _insert_fixtures(pg_db_url, pg_schema)
        _run_backfill(pg_db_url, pg_schema)

        # The exact query from the backfill migration's docstring.
        loser_query = textwrap.dedent(
            """
            SELECT id, platform, metadata_json->>'transaction_id' AS md_txid
            FROM revenue_logs
            WHERE transaction_id IS NULL
              AND metadata_json IS NOT NULL
              AND COALESCE(metadata_json->>'transaction_id', '') <> ''
            """
        )
        losers = _query(pg_db_url, pg_schema, loser_query)
        # After the first backfill, a-002 is the only loser
        # (NULL txid but has the metadata_json key with a non-empty value).
        # c-001/d-001/e-001 are NULL for different reasons
        # (NULL metadata, missing key, empty value) — they don't match
        # the loser query.
        assert losers == [("a-002", "affiliate_impact", "tx-abc-001")]

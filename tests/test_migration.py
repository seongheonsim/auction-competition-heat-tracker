import os
import subprocess
import sys


def test_alembic_upgrade_head_creates_tables(tmp_path):
    db_file = tmp_path / "mig.db"
    full_env = {**os.environ, "DATABASE_URL": f"sqlite:///{db_file}"}
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        capture_output=True,
        text=True,
        env=full_env,
    )
    assert result.returncode == 0, result.stderr

    from sqlalchemy import create_engine, inspect

    engine = create_engine(f"sqlite:///{db_file}")
    tables = set(inspect(engine).get_table_names())
    assert {
        "watchlist_items",
        "source_links",
        "daily_snapshots",
        "auction_results",
        "comparable_cases",
        "comp_links",
    }.issubset(tables)

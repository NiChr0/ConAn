"""Generate a TPC-H DuckDB database at scale factor 0.1 (~100MB)."""
import duckdb
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "tpch.duckdb"

conn = duckdb.connect(str(DB_PATH))
conn.execute("INSTALL tpch")
conn.execute("LOAD tpch")
conn.execute("CALL dbgen(sf=0.1)")

tables = conn.execute("SHOW TABLES").fetchall()
print(f"Created {DB_PATH}")
for (name,) in tables:
    count = conn.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
    print(f"  {name}: {count:,} rows")
conn.close()

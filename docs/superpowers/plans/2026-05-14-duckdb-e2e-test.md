# DuckDB + TPC-H End-to-End Test Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add DuckDB support to Schemalytics and ConAn so both tools can run end-to-end against a local TPC-H DuckDB database with no external infrastructure.

**Architecture:** Create a DuckDB schema extractor for Schemalytics (mirroring `postgres.py`), dispatch to it when the connection string starts with `duckdb://`, add `duckdb-engine` to both tools, and verify with a full bootstrap → chat run against TPC-H data.

**Tech Stack:** DuckDB 1.x, duckdb-engine (SQLAlchemy dialect), TPC-H built-in generator (`CALL dbgen(sf=0.1)`), Schemalytics 1.0.1, ConAn 0.1.0.

---

## File Map

**Schemalytics repo** (`/Users/nchronaios/Documents/Github/schemalytics/`):
- Create: `schemalytics/extractors/duckdb.py` — DuckDB extractor, same interface as `postgres.py`
- Modify: `schemalytics/cli.py:7` — import DuckDB extractor, dispatch on `duckdb://` prefix
- Modify: `schemalytics/pyproject.toml` — add `duckdb>=0.10` and `duckdb-engine>=0.10`

**ConAn repo** (`/Users/nchronaios/Documents/Github/conan/`):
- Modify: `pyproject.toml` — add `duckdb>=0.10` and `duckdb-engine>=0.10`
- Create: `scripts/setup_tpch.py` — generate `tpch.duckdb` with TPC-H scale factor 0.1

---

## Task 1: Create TPC-H DuckDB database

**Files:**
- Create: `scripts/setup_tpch.py` (in ConAn repo)

- [ ] **Step 1: Write setup_tpch.py**

```python
# scripts/setup_tpch.py
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
```

- [ ] **Step 2: Install duckdb and run the script**

```bash
cd /Users/nchronaios/Documents/Github/conan
.venv/bin/pip install duckdb duckdb-engine
.venv/bin/python scripts/setup_tpch.py
```

Expected output:
```
Created .../conan/tpch.duckdb
  customer: 15,000 rows
  lineitem: 600,572 rows
  nation: 25 rows
  orders: 150,000 rows
  part: 20,000 rows
  partsupp: 80,000 rows
  region: 5 rows
  supplier: 1,000 rows
```

- [ ] **Step 3: Verify DuckDB file exists**

```bash
ls -lh /Users/nchronaios/Documents/Github/conan/tpch.duckdb
```

Expected: file exists, ~50-150MB.

- [ ] **Step 4: Add tpch.duckdb to .gitignore**

```bash
echo "tpch.duckdb" >> /Users/nchronaios/Documents/Github/conan/.gitignore
```

- [ ] **Step 5: Commit**

```bash
cd /Users/nchronaios/Documents/Github/conan
git add scripts/setup_tpch.py .gitignore
git commit -m "feat: TPC-H setup script + duckdb in gitignore"
```

---

## Task 2: DuckDB extractor for Schemalytics

**Files:**
- Create: `schemalytics/extractors/duckdb.py`

- [ ] **Step 1: Write the failing test**

```python
# In /Users/nchronaios/Documents/Github/schemalytics/tests/test_duckdb_extractor.py
import pytest
import duckdb
from pathlib import Path
from schemalytics.extractors.duckdb import extract_schema


@pytest.fixture
def duckdb_path(tmp_path):
    db = tmp_path / "test.duckdb"
    conn = duckdb.connect(str(db))
    conn.execute("""
        CREATE TABLE orders (
            order_id INTEGER PRIMARY KEY,
            customer_id INTEGER NOT NULL,
            amount DECIMAL(10,2),
            order_date DATE
        )
    """)
    conn.execute("""
        CREATE TABLE customers (
            customer_id INTEGER PRIMARY KEY,
            name VARCHAR NOT NULL
        )
    """)
    conn.execute("INSERT INTO customers VALUES (1, 'Alice'), (2, 'Bob')")
    conn.execute("INSERT INTO orders VALUES (1, 1, 100.00, '2026-01-01'), (2, 2, 200.00, '2026-01-02')")
    conn.close()
    return db


def test_duckdb_extractor_returns_schema(duckdb_path):
    schema = extract_schema(f"duckdb:///{duckdb_path}")
    assert len(schema.tables) == 2


def test_duckdb_extractor_reads_columns(duckdb_path):
    schema = extract_schema(f"duckdb:///{duckdb_path}")
    orders = next(t for t in schema.tables if t.name == "orders")
    col_names = [c.name for c in orders.columns]
    assert "order_id" in col_names
    assert "amount" in col_names


def test_duckdb_extractor_reads_row_counts(duckdb_path):
    schema = extract_schema(f"duckdb:///{duckdb_path}")
    orders = next(t for t in schema.tables if t.name == "orders")
    assert orders.row_count == 2


def test_duckdb_extractor_excludes_system_schemas(duckdb_path):
    schema = extract_schema(f"duckdb:///{duckdb_path}")
    table_names = {t.name for t in schema.tables}
    assert "orders" in table_names
    assert "customers" in table_names
    # No system tables
    assert not any(n.startswith("duckdb_") for n in table_names)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /Users/nchronaios/Documents/Github/schemalytics
.venv/bin/pip install duckdb duckdb-engine 2>/dev/null || pip install duckdb duckdb-engine
.venv/bin/pytest tests/test_duckdb_extractor.py -v 2>/dev/null || pytest tests/test_duckdb_extractor.py -v
```

Expected: `ModuleNotFoundError: No module named 'schemalytics.extractors.duckdb'`

- [ ] **Step 3: Write duckdb.py extractor**

```python
# schemalytics/extractors/duckdb.py
"""Extract schema from DuckDB using SQLAlchemy."""
from sqlalchemy import create_engine, inspect
from schemalytics.models import Schema, Table, Column, ForeignKey

_SYSTEM_SCHEMAS = {"information_schema", "pg_catalog"}


def extract_schema(connection_string: str) -> Schema:
    """Extract full schema from all user tables in a DuckDB database."""
    engine = create_engine(connection_string)
    inspector = inspect(engine)

    user_schemas = [
        s for s in inspector.get_schema_names()
        if s not in _SYSTEM_SCHEMAS
    ]

    row_counts: dict[str, int] = {}
    try:
        with engine.connect() as conn:
            from sqlalchemy import text
            rows = conn.execute(text(
                "SELECT table_name, estimated_size FROM duckdb_tables() WHERE schema_name = 'main'"
            ))
            for row in rows:
                row_counts[row.table_name] = int(row.estimated_size or 0)
    except Exception:
        pass

    tables = []
    for schema_name in user_schemas:
        for table_name in inspector.get_table_names(schema=schema_name):
            raw_cols = inspector.get_columns(table_name, schema=schema_name)
            columns = [
                Column(
                    name=col["name"],
                    data_type=str(col["type"]),
                    nullable=col.get("nullable", True),
                )
                for col in raw_cols
                if str(col["type"]).upper() != "NULLTYPE"
            ]

            pk = inspector.get_pk_constraint(table_name, schema=schema_name)
            primary_key = pk["constrained_columns"] if pk else None

            foreign_keys = []
            for fk in inspector.get_foreign_keys(table_name, schema=schema_name):
                if not fk["constrained_columns"]:
                    continue
                foreign_keys.append(ForeignKey(
                    column=fk["constrained_columns"][0],
                    references_table=fk["referred_table"],
                    references_column=fk["referred_columns"][0],
                ))

            rc = row_counts.get(table_name)
            if rc == 0:
                # estimated_size=0 means fallback to COUNT(*)
                try:
                    with engine.connect() as conn:
                        from sqlalchemy import text
                        result = conn.execute(text(f'SELECT COUNT(*) FROM "{table_name}"'))
                        rc = result.scalar()
                except Exception:
                    rc = None

            tables.append(Table(
                name=table_name,
                schema_name=schema_name,
                columns=columns,
                primary_key=primary_key,
                foreign_keys=foreign_keys,
                is_partition_child=False,
                partition_parent=None,
                row_count=rc,
            ))

    return Schema(tables=tables)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd /Users/nchronaios/Documents/Github/schemalytics
.venv/bin/pytest tests/test_duckdb_extractor.py -v 2>/dev/null || pytest tests/test_duckdb_extractor.py -v
```

Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
cd /Users/nchronaios/Documents/Github/schemalytics
git add schemalytics/extractors/duckdb.py tests/test_duckdb_extractor.py
git commit -m "feat: DuckDB schema extractor"
```

---

## Task 3: Wire DuckDB extractor into Schemalytics CLI + add deps

**Files:**
- Modify: `schemalytics/cli.py`
- Modify: `schemalytics/pyproject.toml`

- [ ] **Step 1: Write the failing test**

```python
# In /Users/nchronaios/Documents/Github/schemalytics/tests/test_cli_duckdb.py
import pytest
import duckdb
from click.testing import CliRunner
from schemalytics.cli import cli


@pytest.fixture
def minimal_duckdb(tmp_path):
    db = tmp_path / "mini.duckdb"
    conn = duckdb.connect(str(db))
    conn.execute("CREATE TABLE sales (id INTEGER PRIMARY KEY, amount DECIMAL(10,2), sale_date DATE)")
    conn.execute("INSERT INTO sales VALUES (1, 100.00, '2026-01-01')")
    conn.close()
    return db


def test_extract_command_works_with_duckdb(minimal_duckdb, tmp_path):
    runner = CliRunner()
    out = tmp_path / "schema.json"
    result = runner.invoke(cli, [
        "extract",
        "-c", f"duckdb:///{minimal_duckdb}",
        "-o", str(out),
    ])
    assert result.exit_code == 0, result.output
    assert out.exists()
    assert "sales" in out.read_text()
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /Users/nchronaios/Documents/Github/schemalytics
.venv/bin/pytest tests/test_cli_duckdb.py -v 2>/dev/null || pytest tests/test_cli_duckdb.py -v
```

Expected: FAIL — `extract_schema` attempts PostgreSQL connection with DuckDB string, crashes or wrong output.

- [ ] **Step 3: Update cli.py to dispatch on connection string prefix**

Replace lines 7-8 in `schemalytics/cli.py`:

```python
# schemalytics/cli.py
"""CLI entry point for Schemalytics."""
import click
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

console = Console()


def _extract_schema(connection: str):
    if connection.startswith("duckdb://"):
        from schemalytics.extractors.duckdb import extract_schema
    else:
        from schemalytics.extractors.postgres import extract_schema
    return extract_schema(connection)


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """Schemalytics - Automated dbt project generation with an agentic pipeline."""


@click.command()
@click.option("--connection", "-c", required=True, help="Database connection string")
@click.option("--output", "-o", default="./dbt_project", help="Output directory")
@click.option("--name", "-n", default="schemalytics_project", help="Project name")
def generate(connection: str, output: str, name: str):
    """Extract schema, run the agent pipeline, and generate a dbt project."""
    from schemalytics.generators.dbt import generate_dbt_project
    from schemalytics.planner import run_pipeline

    console.print()
    console.rule("[bold cyan]SCHEMALYTICS — AGENTIC DATA MODEL GENERATION[/]")
    console.print()

    with console.status("[bold]Extracting database schema...[/]"):
        schema = _extract_schema(connection)
    console.print(f"  [green]✓[/] Found [bold]{len(schema.tables)}[/] tables")

    result = run_pipeline(schema)

    if not result:
        console.print("\n[yellow]Generation cancelled.[/]")
        return

    modeling_plan, pipeline_ctx = result

    with console.status("[bold]Generating dbt project...[/]"):
        project_path = generate_dbt_project(
            schema,
            modeling_plan,
            output,
            name,
            business_type=pipeline_ctx.business_type,
            context=pipeline_ctx,
        )

    console.print(Panel(
        f"[bold]Project created at:[/] {project_path}\n\n"
        f"  [cyan]•[/] {len(modeling_plan.bronze)} bronze models\n"
        f"  [cyan]•[/] {len(modeling_plan.dimensions)} silver dimensions\n"
        f"  [cyan]•[/] {len(modeling_plan.facts)} silver facts\n"
        f"  [cyan]•[/] {len(modeling_plan.gold)} gold aggregates\n\n"
        "[bold]Next steps:[/]\n"
        f"  [dim]cd {project_path}[/]\n"
        "  [dim]dbt deps[/]\n"
        "  [dim]dbt run[/]",
        title="[bold green]SUCCESS[/]",
        border_style="green",
    ))


@click.command()
@click.option("--connection", "-c", required=True, help="Database connection string")
@click.option("--output", "-o", default="schema.json", help="Output file")
def extract(connection: str, output: str):
    """Extract schema from a database (standalone)."""
    click.echo("Extracting schema...")
    schema = _extract_schema(connection)
    Path(output).write_text(schema.model_dump_json(indent=2))
    click.echo(f"Saved {len(schema.tables)} tables to {output}")


cli.add_command(extract)
cli.add_command(generate)


if __name__ == "__main__":
    cli()
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd /Users/nchronaios/Documents/Github/schemalytics
.venv/bin/pytest tests/test_cli_duckdb.py tests/test_duckdb_extractor.py -v 2>/dev/null || pytest tests/test_cli_duckdb.py tests/test_duckdb_extractor.py -v
```

Expected: 5 passed total.

- [ ] **Step 5: Add duckdb deps to schemalytics/pyproject.toml**

Add to the `dependencies` list in `/Users/nchronaios/Documents/Github/schemalytics/pyproject.toml`:

```toml
dependencies = [
    "click>=8.0",
    "pydantic>=2.0",
    "sqlalchemy>=2.0",
    "psycopg2-binary>=2.9",
    "duckdb>=0.10",
    "duckdb-engine>=0.10",
    "httpx>=0.24",
    "jinja2>=3.0",
    "pyyaml>=6.0",
    "instructor[anthropic]>=1.0.0,<1.15.0",
    "openai>=1.0.0",
    "rich>=13.0",
]
```

- [ ] **Step 6: Commit**

```bash
cd /Users/nchronaios/Documents/Github/schemalytics
git add schemalytics/cli.py pyproject.toml tests/test_cli_duckdb.py
git commit -m "feat: DuckDB connection support — dispatch on duckdb:// prefix"
```

---

## Task 4: Add DuckDB deps to ConAn

**Files:**
- Modify: `conan/pyproject.toml`

- [ ] **Step 1: Add duckdb deps to ConAn pyproject.toml**

Edit `/Users/nchronaios/Documents/Github/conan/pyproject.toml` dependencies:

```toml
dependencies = [
    "click>=8.0",
    "instructor>=1.0",
    "openai>=1.0",
    "anthropic>=0.40",
    "sqlalchemy>=2.0",
    "psycopg2-binary>=2.9",
    "duckdb>=0.10",
    "duckdb-engine>=0.10",
    "pydantic>=2.0",
    "pyyaml>=6.0",
    "rich>=13.0",
]
```

- [ ] **Step 2: Reinstall ConAn**

```bash
cd /Users/nchronaios/Documents/Github/conan
.venv/bin/pip install -e . -q
```

- [ ] **Step 3: Verify executor works with DuckDB connection string**

```bash
cd /Users/nchronaios/Documents/Github/conan
.venv/bin/python -c "
from conan.executor import Executor
ex = Executor('duckdb:///tpch.duckdb')
rows = ex.execute('SELECT COUNT(*) AS n FROM orders')
print('orders count:', rows[0]['n'])
"
```

Expected: `orders count: 150000`

- [ ] **Step 4: Run full test suite to confirm no regressions**

```bash
cd /Users/nchronaios/Documents/Github/conan
.venv/bin/pytest tests/ -q
```

Expected: 48 passed.

- [ ] **Step 5: Commit**

```bash
cd /Users/nchronaios/Documents/Github/conan
git add pyproject.toml
git commit -m "feat: add DuckDB support to executor dependencies"
```

---

## Task 5: End-to-end test

This task is manual verification — no code to write. Run each step and confirm outputs.

- [ ] **Step 1: Run Schemalytics against TPC-H**

```bash
cd /Users/nchronaios/Documents/Github/conan
schemalytics generate \
  -c "duckdb:///tpch.duckdb" \
  -o ./tpch_dbt \
  -n tpch
```

Expected: Schemalytics runs its 5-agent pipeline, prints a SUCCESS panel showing bronze/silver/gold model counts. `tpch_dbt/` directory created with `semantic_layer.yml` inside.

Verify:
```bash
ls tpch_dbt/
cat tpch_dbt/semantic_layer.yml | head -40
```

- [ ] **Step 2: Bootstrap ConAn KB from Schemalytics output**

```bash
cd /Users/nchronaios/Documents/Github/conan
conan bootstrap \
  -p ./tpch_dbt \
  -c "duckdb:///tpch.duckdb" \
  -o ./tpch_kb
```

Expected:
- LLM enrichment pass runs, shows proposed maturity/tier changes
- Prompts "Apply these changes?" — confirm with `y`
- `tpch_kb/` written: `kpis-index.md`, domain files, `source_priority.md`, `schema/tables.md`

Verify:
```bash
cat tpch_kb/kpis-index.md
```

- [ ] **Step 3: Start ConAn chat**

```bash
cd /Users/nchronaios/Documents/Github/conan
conan chat \
  -p ./tpch_kb \
  -c "duckdb:///tpch.duckdb"
```

- [ ] **Step 4: Ask test questions**

At the `You:` prompt, ask these questions one by one and confirm each returns an answer with confidence score:

```
what is the total revenue?
which customer segment has the highest order value?
what are the top 5 nations by number of orders?
why might revenue vary across regions?
```

Expected for each: a formatted answer block with `── Answer`, source table, and `Confidence: XX%`.

- [ ] **Step 5: Commit tpch_dbt to document the Schemalytics output (optional)**

```bash
cd /Users/nchronaios/Documents/Github/conan
echo "tpch_kb/" >> .gitignore
git add .gitignore tpch_dbt/
git commit -m "chore: TPC-H dbt output from Schemalytics (e2e reference)"
```

# conan/cli.py
import click
from pathlib import Path
from conan.bootstrap.mapper import map_from_project
from conan.bootstrap.enricher import enrich_kb
from conan.kb.writer import write_kb, log_session
from conan.orchestrator import Orchestrator


@click.group()
def main():
    """ConAn — AI analytics partner for your Schemalytics project."""
    pass


@main.command()
@click.option("-p", "--project", required=True, type=click.Path(exists=True),
              help="Path to Schemalytics dbt project")
@click.option("-c", "--connection", required=True, help="PostgreSQL connection string")
@click.option("-o", "--output", required=True, type=click.Path(),
              help="Output path for ConAn knowledge base")
@click.option("--name", default=None, help="Project name (defaults to output directory name)")
def bootstrap(project, connection, output, name):
    """Bootstrap ConAn knowledge base from a Schemalytics dbt project."""
    project_path = Path(project)
    output_path = Path(output)
    project_name = name or output_path.name

    click.echo(f"Reading Schemalytics output from {project_path}...")
    kb = map_from_project(project_path, project_name)
    click.echo(f"Mapped {len(kb.kpis)} metrics, {len(kb.sources)} tables.")

    click.echo("Running LLM enrichment pass...")
    kb = enrich_kb(kb, project_path)

    output_path.mkdir(parents=True, exist_ok=True)
    write_kb(kb, output_path)
    click.echo(f"Knowledge base written to {output_path}")


@main.command()
@click.option("-p", "--kb-path", required=True, type=click.Path(exists=True),
              help="Path to ConAn knowledge base")
@click.option("-c", "--connection", required=True, help="PostgreSQL connection string")
def chat(kb_path, connection):
    """Start an interactive chat session with your data."""
    orch = Orchestrator(kb_path, connection)
    click.echo("ConAn ready. Type your question (Ctrl+C to exit).\n")

    while True:
        try:
            question = click.prompt("You")
            if not question.strip():
                continue
            answer = orch.run(question)
            click.echo(answer)
            log_session(kb_path, question, answer)
        except (KeyboardInterrupt, click.exceptions.Abort):
            click.echo("\nBye.")
            break

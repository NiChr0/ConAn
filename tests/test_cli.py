# tests/test_cli.py
import pytest
from unittest.mock import patch, MagicMock
from click.testing import CliRunner
from conan.cli import main


def test_bootstrap_command_exits_zero(tmp_path):
    runner = CliRunner()
    mock_kb = MagicMock()
    mock_kb.kpis = []
    mock_kb.sources = []

    with patch("conan.cli.map_from_project", return_value=mock_kb), \
         patch("conan.cli.enrich_kb", return_value=mock_kb), \
         patch("conan.cli.write_kb"):
        result = runner.invoke(main, [
            "bootstrap",
            "-p", str(tmp_path),
            "-c", "postgresql://localhost/test",
            "-o", str(tmp_path / "conan_kb"),
        ])

    assert result.exit_code == 0


def test_bootstrap_command_requires_project_path():
    runner = CliRunner()
    result = runner.invoke(main, ["bootstrap", "-c", "postgresql://localhost/test", "-o", "/tmp/kb"])
    assert result.exit_code != 0
    assert "Missing option" in result.output


def test_chat_command_runs_one_question_and_exits(tmp_path, kb_path):
    runner = CliRunner()
    mock_orch = MagicMock()
    mock_orch.run.return_value = "\n── Answer ─\nRevenue was $100k\nConfidence: 80%\n"

    with patch("conan.cli.Orchestrator", return_value=mock_orch), \
         patch("conan.cli.log_session"):
        result = runner.invoke(
            main,
            ["chat", "-p", str(kb_path), "-c", "postgresql://localhost/test"],
            input="what was revenue?\n\x03",  # question then Ctrl+C
        )

    assert mock_orch.run.called
    assert result.exit_code == 0

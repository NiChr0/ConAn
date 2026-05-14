import pytest
from unittest.mock import patch, MagicMock
from conan.executor import Executor, ExecutorError


def test_executor_returns_list_of_dicts():
    mock_row = MagicMock()
    mock_row._mapping = {"value": 1}
    mock_conn = MagicMock()
    mock_conn.__enter__ = MagicMock(return_value=mock_conn)
    mock_conn.__exit__ = MagicMock(return_value=False)
    mock_conn.execute.return_value = [mock_row]

    mock_engine = MagicMock()
    mock_engine.connect.return_value = mock_conn

    with patch("conan.executor.create_engine", return_value=mock_engine):
        executor = Executor("postgresql://localhost/test")
        result = executor.execute("SELECT 1 AS value")

    assert result == [{"value": 1}]


def test_executor_raises_executor_error_on_failure():
    from sqlalchemy.exc import SQLAlchemyError
    mock_conn = MagicMock()
    mock_conn.__enter__ = MagicMock(return_value=mock_conn)
    mock_conn.__exit__ = MagicMock(return_value=False)
    mock_conn.execute.side_effect = SQLAlchemyError("table not found")

    mock_engine = MagicMock()
    mock_engine.connect.return_value = mock_conn

    with patch("conan.executor.create_engine", return_value=mock_engine):
        executor = Executor("postgresql://localhost/test")
        with pytest.raises(ExecutorError, match="table not found"):
            executor.execute("SELECT * FROM nonexistent")

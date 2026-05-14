from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError


class ExecutorError(Exception):
    pass


class Executor:
    def __init__(self, db_url: str):
        self.engine = create_engine(db_url)

    def execute(self, sql: str) -> list[dict]:
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(sql))
                return [dict(row._mapping) for row in result]
        except SQLAlchemyError as e:
            raise ExecutorError(str(e)) from e

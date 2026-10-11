import sqlite3

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine


def create_db_engine(url: str) -> Engine:
    engine = create_engine(url, connect_args={"check_same_thread": False})

    @event.listens_for(engine, "connect")
    def configure(connection: sqlite3.Connection, record: object) -> None:
        cursor = connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA busy_timeout=5000")
        cursor.close()
        # Disable sqlite3 legacy transaction control; SQLAlchemy owns BEGIN.
        connection.isolation_level = None

    @event.listens_for(engine, "begin")
    def begin(connection: object) -> None:
        from sqlalchemy.engine import Connection

        assert isinstance(connection, Connection)
        connection.exec_driver_sql(
            "BEGIN IMMEDIATE"
            if connection.get_execution_options().get("sqlite_immediate")
            else "BEGIN"
        )

    return engine

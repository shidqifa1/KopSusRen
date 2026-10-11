from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect
from sqlalchemy.engine import Engine

from app.db.base import Base
from app.db.session import create_db_engine


def test_BR_1_migration_upgrade_downgrade_upgrade(tmp_path: Path) -> None:
    config = Config("alembic.ini")
    url = f"sqlite:///{tmp_path / 'roundtrip.db'}"
    config.set_main_option("sqlalchemy.url", url)
    engine = create_db_engine(url)
    for target in ("head", "base", "head"):
        if target == "base":
            command.downgrade(config, target)
        else:
            command.upgrade(config, target)
        tables = set(inspect(engine).get_table_names()) - {"alembic_version"}
        assert tables == (set() if target == "base" else set(Base.metadata.tables))
    engine.dispose()


def test_BR_1_connection_pragmas_on_every_connection(db: Engine) -> None:
    with db.connect() as first, db.connect() as second:
        for connection in (first, second):
            assert connection.exec_driver_sql("PRAGMA foreign_keys").scalar() == 1
            assert connection.exec_driver_sql("PRAGMA journal_mode").scalar() == "wal"
            assert connection.exec_driver_sql("PRAGMA busy_timeout").scalar() == 5000

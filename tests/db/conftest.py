from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy.engine import Engine

from app.db.session import create_db_engine


@pytest.fixture
def db(tmp_path: Path) -> Iterator[Engine]:
    url = f"sqlite:///{tmp_path / 'test.db'}"
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", url)
    command.upgrade(config, "head")
    engine = create_db_engine(url)
    yield engine
    engine.dispose()

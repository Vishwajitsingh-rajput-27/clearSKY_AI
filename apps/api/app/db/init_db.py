import logging

from sqlalchemy import inspect, text

from app.core.config import settings
from app.db.base import Base
from app.db.session import engine

logger = logging.getLogger(__name__)


def init_db() -> None:
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    settings.inference_dir.mkdir(parents=True, exist_ok=True)

    if settings.auto_create_tables:
        logger.info("Creating database tables using SQLAlchemy metadata")
        Base.metadata.create_all(bind=engine)
        sync_sqlite_schema()


def sync_sqlite_schema() -> None:
    if not settings.is_sqlite:
        return

    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())

    with engine.begin() as connection:
        for table in Base.metadata.sorted_tables:
            if table.name not in existing_tables:
                continue

            existing_columns = {column["name"] for column in inspector.get_columns(table.name)}

            for column in table.columns:
                if column.name in existing_columns:
                    continue

                column_type = column.type.compile(dialect=engine.dialect)
                logger.info("Adding missing SQLite column %s.%s", table.name, column.name)
                connection.execute(
                    text(f'ALTER TABLE "{table.name}" ADD COLUMN "{column.name}" {column_type}')
                )

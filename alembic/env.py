from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.core.config import settings
from app.database import Base
from app.models.payment import Payment

config = context.config


def escape_configparser_value(value: str) -> str:
    """Escape percent signs before writing dynamic values into Alembic config.

    ConfigParser treats percent signs as interpolation markers, while Azure
    MySQL URLs can contain percent-encoded values such as %2F.
    """
    return value.replace("%", "%%")


config.set_main_option("sqlalchemy.url", escape_configparser_value(settings.database_url))

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata
SERVICE_VERSION_TABLE = "payment_alembic_version"


def run_migrations_offline():
    context.configure(
        url=settings.database_url,
        target_metadata=target_metadata,
        version_table=SERVICE_VERSION_TABLE,
        literal_binds=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, version_table=SERVICE_VERSION_TABLE)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

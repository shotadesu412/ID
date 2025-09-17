import os
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# this is the Alembic Config object, which provides access to the values within the .ini file
config = context.config
fileConfig(config.config_file_name)

# Import Flask app to get metadata & DB URL
from app import create_app, db
app = create_app()
with app.app_context():
    target_metadata = db.metadata
    # Override DB URL from Flask config (DATABASE_URL / normalized)
    config.set_main_option("sqlalchemy.url", app.config["SQLALCHEMY_DATABASE_URI"])

def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section), prefix="sqlalchemy.", poolclass=pool.NullPool
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

from sqlalchemy import create_engine, text

from app.core.config import settings


def main() -> None:
    engine = create_engine(settings.admin_database_uri, isolation_level="AUTOCOMMIT")
    query = text("SELECT 1 FROM pg_database WHERE datname = :database_name")

    with engine.connect() as connection:
        exists = connection.execute(query, {"database_name": settings.db_name}).scalar()
        if exists:
            print(f"Database {settings.db_name} already exists.")
            return
        connection.execute(text(f'CREATE DATABASE "{settings.db_name}"'))
        print(f"Database {settings.db_name} created successfully.")


if __name__ == "__main__":
    main()

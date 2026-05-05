from urllib.parse import quote_plus, unquote_plus

from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

from app.core.config import settings
from app.db.base import Base
from app.db.session import engine


# SQL Server connection helpers
def _split_odbc_connect(odbc_connect: str) -> dict[str, str]:
    parts = {}
    for item in unquote_plus(odbc_connect).split(";"):
        if not item or "=" not in item:
            continue
        key, value = item.split("=", 1)
        parts[key.strip().lower()] = value.strip()
    return parts


def _build_odbc_url(parts: dict[str, str], database_name: str) -> str:
    values = {
        "Driver": parts.get("driver", "{ODBC Driver 18 for SQL Server}"),
        "Server": parts["server"],
        "Database": database_name,
        "Trusted_Connection": parts.get("trusted_connection", "yes"),
        "TrustServerCertificate": parts.get("trustservercertificate", "yes"),
    }

    if "uid" in parts:
        values["UID"] = parts["uid"]
    if "pwd" in parts:
        values["PWD"] = parts["pwd"]

    connection_string = ";".join(f"{key}={value}" for key, value in values.items())
    return f"mssql+pyodbc:///?odbc_connect={quote_plus(connection_string)}"


def _database_name_and_master_url() -> tuple[str | None, str]:
    database_url = make_url(settings.database_url)
    odbc_connect = database_url.query.get("odbc_connect")

    if odbc_connect:
        parts = _split_odbc_connect(odbc_connect)
        database_name = parts.get("database")
        return database_name, _build_odbc_url(parts, "master")

    database_name = database_url.database
    return database_name, str(database_url.set(database="master"))


# Database creation
def ensure_database_exists() -> None:
    database_name, master_url = _database_name_and_master_url()

    if not database_name:
        return

    master_engine = create_engine(master_url, isolation_level="AUTOCOMMIT", pool_pre_ping=True)

    with master_engine.connect() as connection:
        exists = connection.execute(
            text("SELECT DB_ID(:database_name)"),
            {"database_name": database_name},
        ).scalar()

        if not exists:
            safe_database_name = database_name.replace("]", "]]")
            connection.execute(text(f"CREATE DATABASE [{safe_database_name}]"))

    master_engine.dispose()


# Startup database initialization
def init_db() -> None:
    if settings.auto_create_database:
        ensure_database_exists()
    Base.metadata.create_all(bind=engine)
    ensure_user_role_column_supports_superuser()
    ensure_user_shift_column()
    ensure_user_active_column()
    ensure_deviation_columns()
    ensure_notification_columns()
    ensure_deviation_type_kind_column_removed()
    ensure_qc_vessel_relation_removed()


# User table compatibility migrations
def ensure_user_role_column_supports_superuser() -> None:
    with engine.begin() as connection:
        users_table_exists = connection.execute(text("SELECT OBJECT_ID('users', 'U')")).scalar()
        if users_table_exists:
            connection.execute(text("ALTER TABLE users ALTER COLUMN role VARCHAR(20) NOT NULL"))


def ensure_user_shift_column() -> None:
    with engine.begin() as connection:
        users_table_exists = connection.execute(text("SELECT OBJECT_ID('users', 'U')")).scalar()
        if not users_table_exists:
            return

        shift_exists = connection.execute(text("SELECT COL_LENGTH('users', 'shift')")).scalar()
        if shift_exists is None:
            connection.execute(text("ALTER TABLE users ADD shift VARCHAR(80) NULL"))


def ensure_user_active_column() -> None:
    with engine.begin() as connection:
        users_table_exists = connection.execute(text("SELECT OBJECT_ID('users', 'U')")).scalar()
        if not users_table_exists:
            return

        active_exists = connection.execute(text("SELECT COL_LENGTH('users', 'active')")).scalar()
        if active_exists is None:
            connection.execute(text("ALTER TABLE users ADD active BIT NOT NULL CONSTRAINT DF_users_active DEFAULT 1"))


# Deviation table compatibility migrations
def ensure_deviation_columns() -> None:
    with engine.begin() as connection:
        deviations_table_exists = connection.execute(text("SELECT OBJECT_ID('deviations', 'U')")).scalar()
        if not deviations_table_exists:
            return

        status_exists = connection.execute(text("SELECT COL_LENGTH('deviations', 'status')")).scalar()
        if status_exists is None:
            connection.execute(text("ALTER TABLE deviations ADD status VARCHAR(80) NOT NULL CONSTRAINT DF_deviations_status DEFAULT 'Not Yet'"))

        description_exists = connection.execute(text("SELECT COL_LENGTH('deviations', 'description')")).scalar()
        if description_exists is None:
            connection.execute(text("ALTER TABLE deviations ADD description VARCHAR(MAX) NULL"))

        area_exists = connection.execute(text("SELECT COL_LENGTH('deviations', 'area')")).scalar()
        if area_exists is None:
            connection.execute(text("ALTER TABLE deviations ADD area VARCHAR(80) NOT NULL CONSTRAINT DF_deviations_area DEFAULT 'Yard'"))


# Notification table compatibility migrations
def ensure_notification_columns() -> None:
    with engine.begin() as connection:
        notifications_table_exists = connection.execute(text("SELECT OBJECT_ID('notifications', 'U')")).scalar()
        if not notifications_table_exists:
            return

        read_exists = connection.execute(text("SELECT COL_LENGTH('notifications', 'read')")).scalar()
        is_read_exists = connection.execute(text("SELECT COL_LENGTH('notifications', 'is_read')")).scalar()

        if read_exists is not None and is_read_exists is None:
            connection.execute(text("EXEC sp_rename 'notifications.read', 'is_read', 'COLUMN'"))
        elif read_exists is None and is_read_exists is None:
            connection.execute(text("ALTER TABLE notifications ADD is_read BIT NOT NULL CONSTRAINT DF_notifications_is_read DEFAULT 0"))

        deviation_id_nullable = connection.execute(text("""
            SELECT is_nullable
            FROM sys.columns
            WHERE object_id = OBJECT_ID('notifications') AND name = 'deviation_id'
        """)).scalar()
        if deviation_id_nullable == 0:
            connection.execute(text("ALTER TABLE notifications ALTER COLUMN deviation_id INT NULL"))


# Legacy column cleanup
def ensure_deviation_type_kind_column_removed() -> None:
    with engine.begin() as connection:
        deviations_table_exists = connection.execute(text("SELECT OBJECT_ID('deviations', 'U')")).scalar()
        if not deviations_table_exists:
            return

        type_exists = connection.execute(text("SELECT COL_LENGTH('deviations', 'type')")).scalar()
        if type_exists is None:
            return

        connection.execute(text("""
            DECLARE @sql NVARCHAR(MAX) = N'';
            SELECT @sql = @sql + N'ALTER TABLE deviations DROP CONSTRAINT [' + dc.name + N'];'
            FROM sys.default_constraints dc
            JOIN sys.columns c ON c.object_id = dc.parent_object_id AND c.column_id = dc.parent_column_id
            WHERE dc.parent_object_id = OBJECT_ID('deviations') AND c.name = 'type';

            SELECT @sql = @sql + N'ALTER TABLE deviations DROP CONSTRAINT [' + cc.name + N'];'
            FROM sys.check_constraints cc
            WHERE cc.parent_object_id = OBJECT_ID('deviations') AND cc.definition LIKE '%[[]type[]]%';

            IF @sql <> N'' EXEC sp_executesql @sql;
        """))
        connection.execute(text("ALTER TABLE deviations DROP COLUMN type"))


def ensure_qc_vessel_relation_removed() -> None:
    with engine.begin() as connection:
        qcs_table_exists = connection.execute(text("SELECT OBJECT_ID('qcs', 'U')")).scalar()
        if not qcs_table_exists:
            return

        vessel_id_exists = connection.execute(text("SELECT COL_LENGTH('qcs', 'vessel_id')")).scalar()
        if vessel_id_exists is None:
            return

        connection.execute(text("""
            DECLARE @sql NVARCHAR(MAX) = N'';
            SELECT @sql = @sql + N'ALTER TABLE qcs DROP CONSTRAINT [' + fk.name + N'];'
            FROM sys.foreign_keys fk
            JOIN sys.foreign_key_columns fkc ON fk.object_id = fkc.constraint_object_id
            JOIN sys.columns c ON c.object_id = fkc.parent_object_id AND c.column_id = fkc.parent_column_id
            WHERE fk.parent_object_id = OBJECT_ID('qcs') AND c.name = 'vessel_id';
            IF @sql <> N'' EXEC sp_executesql @sql;
        """))
        connection.execute(text("ALTER TABLE qcs DROP COLUMN vessel_id"))

import os
import re
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# Load environment variables from .env
load_dotenv()

# ---------------------------------------------------------------------------
# Database URL Resolution:
# Supports Supabase PostgreSQL (via direct URI or pooled URI), standard PostgreSQL,
# MySQL, and local SQLite for development/testing.
# ---------------------------------------------------------------------------

raw_database_url = (
    os.getenv("DATABASE_URL")
    or os.getenv("SUPABASE_DB_URL")
    or os.getenv("SUPABASE_POSTGRES_URL")
    or ""
).strip()

DB_USER = (os.getenv("DB_USER") or "").strip()
DB_PASSWORD = (os.getenv("DB_PASSWORD") or "").strip()
DB_HOST = (os.getenv("DB_HOST") or "").strip()
DB_PORT = (os.getenv("DB_PORT") or "").strip()
DB_NAME = (os.getenv("DB_NAME") or "").strip()
DB_TYPE = (os.getenv("DB_TYPE") or "").lower().strip()

# Check if environment points to PostgreSQL / Supabase
is_postgres_hint = (
    "supabase" in DB_HOST.lower()
    or "pooler" in DB_HOST.lower()
    or DB_PORT in ("5432", "6543")
    or DB_TYPE in ("postgres", "postgresql", "supabase")
)

engine_kwargs = {
    "pool_pre_ping": True,  # Verifies connection viability before using from pool
}

if raw_database_url:
    # Normalize postgres:// to postgresql+psycopg2:// for SQLAlchemy 1.4/2.0+
    if raw_database_url.startswith("postgres://"):
        raw_database_url = raw_database_url.replace("postgres://", "postgresql+psycopg2://", 1)
    elif raw_database_url.startswith("postgresql://") and not raw_database_url.startswith("postgresql+"):
        raw_database_url = raw_database_url.replace("postgresql://", "postgresql+psycopg2://", 1)

    # Supabase connections require SSL
    if ("supabase.co" in raw_database_url or "pooler.supabase.com" in raw_database_url) and "sslmode=" not in raw_database_url:
        separator = "&" if "?" in raw_database_url else "?"
        raw_database_url = f"{raw_database_url}{separator}sslmode=require"

    URL_DATABASE = raw_database_url

    if "postgresql" in URL_DATABASE:
        # Supavisor transaction pooler recycles idle connections; 300s recycle is recommended
        engine_kwargs["pool_recycle"] = int(os.getenv("DB_POOL_RECYCLE", "300"))
        engine_kwargs["pool_size"] = int(os.getenv("DB_POOL_SIZE", "10"))
        engine_kwargs["max_overflow"] = int(os.getenv("DB_MAX_OVERFLOW", "20"))
    elif "mysql" in URL_DATABASE:
        engine_kwargs["pool_recycle"] = 3600
        engine_kwargs["connect_args"] = {"ssl": {}}
    elif "sqlite" in URL_DATABASE:
        engine_kwargs["connect_args"] = {"check_same_thread": False}

elif is_postgres_hint or DB_PORT in ("5432", "6543"):
    # Assembling PostgreSQL / Supabase connection from individual variables
    host = DB_HOST or "localhost"
    port = DB_PORT or "5432"
    dbname = DB_NAME or "postgres"
    auth = f"{DB_USER}:{DB_PASSWORD}@" if DB_PASSWORD else f"{DB_USER}@" if DB_USER else ""
    URL_DATABASE = f"postgresql+psycopg2://{auth}{host}:{port}/{dbname}?sslmode=require"
    engine_kwargs["pool_recycle"] = 300
    engine_kwargs["pool_size"] = 10
    engine_kwargs["max_overflow"] = 20

elif DB_HOST or DB_USER:
    # MySQL fallback (legacy support)
    host = DB_HOST or "localhost"
    port = DB_PORT or "3306"
    dbname = DB_NAME or "syllabus_feedback"
    auth = f"{DB_USER}:{DB_PASSWORD}@" if DB_PASSWORD else f"{DB_USER}@" if DB_USER else ""
    URL_DATABASE = f"mysql+pymysql://{auth}{host}:{port}/{dbname}"
    engine_kwargs["pool_recycle"] = 3600
    engine_kwargs["connect_args"] = {"ssl": {}}

else:
    # Local fallback for tests/development if no DB configured
    URL_DATABASE = "sqlite:///./syllabus_feedback.db"
    engine_kwargs = {"connect_args": {"check_same_thread": False}}

# Create SQLAlchemy Engine
try:
    engine = create_engine(URL_DATABASE, **engine_kwargs)
except Exception as e:
    # Provide helpful diagnostic error if driver is missing
    if "psycopg2" in str(e).lower() or "no module named 'psycopg2'" in str(e).lower():
        raise RuntimeError(
            "psycopg2 is required to connect to Supabase/PostgreSQL. "
            "Please run: pip install psycopg2-binary"
        ) from e
    raise

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

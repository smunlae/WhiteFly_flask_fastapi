from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = None
SessionLocal = None


def init_db(database_url: str):
    global engine, SessionLocal
    database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    engine = create_engine(database_url, pool_pre_ping=True)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db_session():
    if SessionLocal is None:
        raise RuntimeError("Database is not initialized")
    return SessionLocal()


def ensure_submission_fp_columns():
    if engine is None:
        raise RuntimeError("Database is not initialized")
    ddl_statements = [
        "ALTER TABLE submissions ADD COLUMN IF NOT EXISTS fp_visitor_id VARCHAR(255)",
        "ALTER TABLE submissions ADD COLUMN IF NOT EXISTS fp_request_id VARCHAR(255)",
        "ALTER TABLE submissions ADD COLUMN IF NOT EXISTS fp_confidence_score DOUBLE PRECISION",
        "ALTER TABLE submissions ADD COLUMN IF NOT EXISTS fp_is_suspect BOOLEAN NOT NULL DEFAULT FALSE",
        "ALTER TABLE submissions ADD COLUMN IF NOT EXISTS fp_verification_error TEXT",
    ]
    with engine.begin() as connection:
        for ddl in ddl_statements:
            connection.exec_driver_sql(ddl)

# db.py

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from typing import Generator

# Read the database URL from env, fallback to a local SQLite file
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./resume_evaluator.db"
)

# For SQLite, we need this flag
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

# 1) Create the SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    echo=True,        # you can turn this off in prod
)

# 2) Create a configured "Session" class
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# 3) Base class for your models
Base = declarative_base()

def init_db() -> None:
    """
    Create all tables and seed subscription plans if missing.
    """
    # import models so metadata is populated
    import models   # noqa: F401
    Base.metadata.create_all(bind=engine)

    # seed default subscription plans
    from models import SubscriptionPlan
    db = SessionLocal()
    try:
        count = db.query(SubscriptionPlan).count()
        if count == 0:
            db.add_all([
                SubscriptionPlan(
                    name="free",
                    description="Free, no signup required",
                    price_usd=0.0,
                    max_runs=None
                ),
                SubscriptionPlan(
                    name="personal",
                    description="Job seeker pro features",
                    price_usd=9.99,
                    max_runs=None
                ),
                SubscriptionPlan(
                    name="business",
                    description="HR team suite",
                    price_usd=49.99,
                    max_runs=None
                ),
            ])
            db.commit()
    finally:
        db.close()

def get_db() -> Generator:
    """
    Dependency you can use with FastAPI endpoints:

        def some_endpoint(db: Session = Depends(get_db)):
            ...

    It will yield a SQLAlchemy Session and close it when done.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

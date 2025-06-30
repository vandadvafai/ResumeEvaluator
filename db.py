# db.py

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from typing import Generator

# fallback to local SQLite
DATABASE_URL = os.getenv(
    "DATABASE_URL", "sqlite:///./resume_evaluator.db"
)
connect_args = {"check_same_thread": False} \
    if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args, echo=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

def init_db() -> None:
    # register models
    import models  # noqa: F401
    Base.metadata.create_all(bind=engine)

    # seed subscription plans
    from models import SubscriptionPlan
    db = SessionLocal()
    try:
        if db.query(SubscriptionPlan).count() == 0:
            db.add_all([
                SubscriptionPlan(
                    name="free",
                    description="Free, no signup required",
                    price_usd=0.0,
                    max_runs=2,
                ),
                SubscriptionPlan(
                    name="personal",
                    description="Job seeker pro features",
                    price_usd=9.99,
                    max_runs=100
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
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

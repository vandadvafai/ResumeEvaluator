# models.py

from sqlalchemy import (
    Column, Integer, String, Float, DateTime,
    ForeignKey
)
from sqlalchemy.orm import relationship
from datetime import datetime
from db import Base

class User(Base):
    __tablename__ = "users"
    id        = Column(Integer, primary_key=True, index=True)
    email     = Column(String, unique=True, index=True, nullable=False)
    hashed_pw = Column(String, nullable=False)

    subscription = relationship(
        "UserSubscription",
        uselist=False,
        back_populates="user",
        cascade="all, delete-orphan"
    )

class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"
    id          = Column(Integer, primary_key=True, index=True)
    name        = Column(String, unique=True, nullable=False)
    description = Column(String, nullable=False)
    price_usd   = Column(Float, nullable=False)
    max_runs    = Column(Integer, nullable=True)

class UserSubscription(Base):
    __tablename__ = "user_subscriptions"
    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("users.id"), nullable=False)
    plan_id    = Column(Integer, ForeignKey("subscription_plans.id"), nullable=False)
    starts_at  = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="subscription")
    plan = relationship("SubscriptionPlan")

class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"
    id        = Column(Integer, primary_key=True, index=True)
    user_id   = Column(Integer, ForeignKey("users.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")

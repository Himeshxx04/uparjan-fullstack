# backend/models.py

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Date, DateTime
from sqlalchemy.sql import func

from .database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String, index=True, nullable=False)       # "Income" / "Expense"
    category = Column(String, index=True, nullable=False)   # "Food", "Rent", etc.
    amount = Column(Float, nullable=False)
    date = Column(Date, nullable=False)                     # Python date object


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),      # DB sets current timestamp
        nullable=False,
    )

# backend/schemas.py

from pydantic import BaseModel
from datetime import datetime
from typing import List

# 1. What fields does a transaction have (from the client's POV)?
class TransactionBase(BaseModel):
    type: str          # "Income" or "Expense"
    category: str      # e.g., "Food", "Rent"
    amount: float
    date: datetime     # we'll send this from frontend as ISO datetime

# 2. For creating a transaction: same as base
class TransactionCreate(TransactionBase):
    pass

# 3. What we send back to the client (includes ID)
class TransactionOut(TransactionBase):
    id: int

    class Config:
        orm_mode = True

from typing import Optional

# ---------- User Schemas ----------

class UserBase(BaseModel):
    email: str

class UserCreate(UserBase):
    password: str   # plain password from the client (will be hashed)

class User(UserBase):
    id: int

    class Config:
        from_attributes = True


# ---------- Token Schemas ----------

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

# backend/main.py

import yfinance as yf
from typing import List

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from . import models, schemas
from .database import SessionLocal, engine
from .auth import (
    get_password_hash,
    verify_password,
    create_access_token,
)

# Create DB tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI()


# ------------ DB DEPENDENCY ------------

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ------------ HEALTHCHECK ------------

@app.get("/health")
def health_check():
    return {"status": "ok"}


# ------------ AUTH ENDPOINTS ------------

@app.post("/auth/register", response_model=schemas.User)
def register_user(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    # Check if email already exists
    existing = db.query(models.User).filter(models.User.email == user_in.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Hash password and create user
    hashed_pw = get_password_hash(user_in.password)
    db_user = models.User(email=user_in.email, hashed_password=hashed_pw)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


# This model matches what Streamlit likely sends: JSON {email, password}
class LoginRequest(BaseModel):
    email: EmailStr
    password: str


@app.post("/auth/login", response_model=schemas.Token)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """
    Login with JSON body: {"email": "...", "password": "..."}
    """
    user = db.query(models.User).filter(models.User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password",
        )

    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}


# ------------ DEBUG ENDPOINTS ------------

@app.get("/db-test")
def db_test(db: Session = Depends(get_db)):
    return {"message": "DB session created successfully"}


@app.get("/transactions-debug")
def get_transactions_debug(db: Session = Depends(get_db)):
    txs = db.query(models.Transaction).all()
    return {"count": len(txs)}


# ------------ TRANSACTIONS API ------------

@app.post(
    "/transactions",
    response_model=schemas.TransactionOut,
    status_code=status.HTTP_201_CREATED,
)
def create_transaction(
    tx: schemas.TransactionCreate,
    db: Session = Depends(get_db),
):
    db_tx = models.Transaction(
        type=tx.type,
        category=tx.category,
        amount=tx.amount,
        date=tx.date,
    )
    db.add(db_tx)
    db.commit()
    db.refresh(db_tx)
    return db_tx


@app.get("/transactions", response_model=List[schemas.TransactionOut])
def list_transactions(db: Session = Depends(get_db)):
    txs = db.query(models.Transaction).order_by(models.Transaction.date.desc()).all()
    return txs


@app.delete("/transactions/{tx_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(tx_id: int, db: Session = Depends(get_db)):
    tx = db.query(models.Transaction).filter(models.Transaction.id == tx_id).first()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")

    db.delete(tx)
    db.commit()
    return


# ------------ STOCK PRICE ------------

class StockPriceResponse(BaseModel):
    symbol: str
    price: float | None


@app.get("/stock-price", response_model=StockPriceResponse)
def get_stock_price(symbol: str):
    """
    Get live stock price for a given symbol using yfinance.
    Example: /stock-price?symbol=RELIANCE.NS
    """
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        current_price = info.get("currentPrice")

        if current_price is None:
            raise HTTPException(
                status_code=404,
                detail=f"Could not find price for symbol '{symbol}'",
            )

        return StockPriceResponse(symbol=symbol.upper(), price=current_price)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching stock price: {e}",
        )

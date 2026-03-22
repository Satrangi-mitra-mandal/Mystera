from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models import User
from app.schemas import RegisterRequest, LoginRequest, TokenResponse, UserPublic
from app.utils.auth import hash_password, verify_password, create_token, get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    if db.query(User).filter(User.username == data.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")

    user = User(
        email=data.email,
        username=data.username,
        password_hash=hash_password(data.password),
        avatar=data.avatar or "🕵️",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_token({"sub": user.id})
    return TokenResponse(
        access_token=token,
        user=UserPublic.model_validate(user)
    )


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_token({"sub": user.id})
    return TokenResponse(
        access_token=token,
        user=UserPublic.model_validate(user)
    )


@router.get("/me", response_model=UserPublic)
def me(current_user: User = Depends(get_current_user)):
    return UserPublic.model_validate(current_user)


@router.patch("/me", response_model=UserPublic)
def update_me(
    data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    allowed = {"avatar", "username"}
    for k, v in data.items():
        if k in allowed:
            setattr(current_user, k, v)
    db.commit()
    db.refresh(current_user)
    return UserPublic.model_validate(current_user)
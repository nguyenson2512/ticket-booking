from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from daos.user import UserDAO
from services.auth_service import hash_password, verify_password, create_access_token
from schemas.user import UserCreate, UserLogin, UserRead
from models.user import User
from core.config import settings
from fastapi.security import OAuth2PasswordBearer
from core.database import get_db

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

@router.post("/sign-up", response_model=UserRead)
def sign_up(user_data: UserCreate, db: Session = Depends(get_db)):
    dao = UserDAO(db)
    if dao.get_by_email(user_data.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_pw = hash_password(user_data.password)
    user_create = UserCreate(
        email=user_data.email,
        password=hashed_pw,
        name=user_data.name
    )
    user = dao.create(user_create)
    return user

@router.post("/login")
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    dao = UserDAO(db)
    user = dao.get_by_email(login_data.email)
    if not user or not verify_password(login_data.password, str(user.hashed_password)):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token(data={"sub": user.email})
    return {"access_token": token, "token_type": "bearer"}

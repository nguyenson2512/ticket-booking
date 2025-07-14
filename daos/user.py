from sqlalchemy.orm import Session
from models.user import User
from schemas.user import UserCreate

class UserDAO:
    def __init__(self, db: Session):
        self.db = db

    def get_by_email(self, email: str):
        return self.db.query(User).filter(User.email == email).first()

    def create(self, user: UserCreate):
        db_user = User(email=user.email, name=user.name, hashed_password=user.password)
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user

    def get_multi(self, skip: int = 0, limit: int = 10):
        return self.db.query(User).offset(skip).limit(limit).all()
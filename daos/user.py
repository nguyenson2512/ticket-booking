from sqlalchemy.orm import Session
from models.user import User, Role
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

    def assign_role(self, user_id: int, role_id: int):
        """Assign a role to a user"""
        user = self.db.query(User).filter(User.id == user_id).first()
        role = self.db.query(Role).filter(Role.id == role_id).first()
        
        if user and role:
            if role not in user.roles:
                user.roles.append(role)
                self.db.commit()
                return True
        return False

    def remove_role(self, user_id: int, role_id: int):
        """Remove a role from a user"""
        user = self.db.query(User).filter(User.id == user_id).first()
        role = self.db.query(Role).filter(Role.id == role_id).first()
        
        if user and role:
            if role in user.roles:
                user.roles.remove(role)
                self.db.commit()
                return True
        return False

    def get_user_with_roles(self, user_id: int):
        """Get a user with their roles loaded"""
        return self.db.query(User).filter(User.id == user_id).first()

    def get_users_with_roles(self, skip: int = 0, limit: int = 10):
        """Get users with their roles loaded"""
        return self.db.query(User).offset(skip).limit(limit).all()

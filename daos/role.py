from sqlalchemy.orm import Session
from models.user import Role
from schemas.user import RoleCreate

class RoleDAO:
    def __init__(self, db: Session):
        self.db = db

    def get_by_name(self, name: str):
        return self.db.query(Role).filter(Role.name == name).first()

    def get_by_id(self, role_id: int):
        return self.db.query(Role).filter(Role.id == role_id).first()

    def create(self, role: RoleCreate):
        db_role = Role(name=role.name)
        self.db.add(db_role)
        self.db.commit()
        self.db.refresh(db_role)
        return db_role

    def get_all(self):
        return self.db.query(Role).all()

    def get_multi(self, skip: int = 0, limit: int = 10):
        return self.db.query(Role).offset(skip).limit(limit).all()

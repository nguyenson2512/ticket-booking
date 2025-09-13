from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from daos.user import UserDAO
from daos.role import RoleDAO
from services.auth_service import hash_password, verify_password, create_access_token, get_current_user
from schemas.user import UserCreate, UserLogin, UserRead, RoleRead, RoleCreate
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

@router.get("/users", response_model=list[UserRead])
def get_users(skip: int = 0, limit: int = 10, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    dao = UserDAO(db)
    users = dao.get_users_with_roles(skip=skip, limit=limit)
    return users

@router.get("/roles", response_model=list[RoleRead])
def get_roles(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Get all available roles"""
    dao = RoleDAO(db)
    roles = dao.get_all()
    return roles

@router.post("/roles", response_model=RoleRead)
def create_role(role_data: RoleCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Create a new role (admin only)"""
    # Check if current user has admin role
    if not any(role.name == "admin" for role in current_user.roles):
        raise HTTPException(status_code=403, detail="Only admins can create roles")
    
    dao = RoleDAO(db)
    if dao.get_by_name(role_data.name):
        raise HTTPException(status_code=400, detail="Role already exists")
    
    role = dao.create(role_data)
    return role

@router.post("/users/{user_id}/roles/{role_id}")
def assign_role_to_user(user_id: int, role_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Assign a role to a user (admin only)"""
    # Check if current user has admin role
    if not any(role.name == "admin" for role in current_user.roles):
        raise HTTPException(status_code=403, detail="Only admins can assign roles")
    
    dao = UserDAO(db)
    success = dao.assign_role(user_id, role_id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to assign role")
    
    return {"message": "Role assigned successfully"}

@router.delete("/users/{user_id}/roles/{role_id}")
def remove_role_from_user(user_id: int, role_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Remove a role from a user (admin only)"""
    # Check if current user has admin role
    if not any(role.name == "admin" for role in current_user.roles):
        raise HTTPException(status_code=403, detail="Only admins can remove roles")
    
    dao = UserDAO(db)
    success = dao.remove_role(user_id, role_id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to remove role")
    
    return {"message": "Role removed successfully"}

@router.get("/me", response_model=UserRead)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information with roles"""
    return current_user

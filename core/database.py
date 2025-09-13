from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from core.config import settings
from sqlalchemy.orm import declarative_base

DATABASE_URL = settings.DATABASE_URL

engine = create_engine(DATABASE_URL, echo=True, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
def seed_roles():
    """Seed the roles table with default data (admin, client)"""
    from models.user import Role
    
    db = SessionLocal()
    try:
        # Check if roles already exist
        existing_roles = db.query(Role).all()
        if existing_roles:
            print("Roles already exist, skipping seeding")
            return
        
        # Create default roles
        admin_role = Role(name="admin")
        client_role = Role(name="client")
        
        db.add(admin_role)
        db.add(client_role)
        db.commit()
        
        print("Successfully seeded roles table with admin and client roles")
    except Exception as e:
        print(f"Error seeding roles: {e}")
        db.rollback()
    finally:
        db.close()

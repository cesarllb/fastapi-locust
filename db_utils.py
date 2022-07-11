from sqlalchemy.orm import Session
from models import User

def add_new_user(db: Session, user: User):
    db.add(user)
    db.commit()

def flush_users_table(db: Session):
    db.query(User).delete()
    db.commit()
    
def get_all_users(db: Session):
    return db.query(User).all()

def get_users_db_size(db: Session):
    return len(get_all_users(db))
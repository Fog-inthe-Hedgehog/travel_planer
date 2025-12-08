from typing import Optional
from sqlalchemy.orm import Session
from app.database.models import User


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: int) -> Optional[User]:
        return self.db.query(User).filter(User.user_id == user_id).first()

    def ensure_user(self, user_id: int, username: Optional[str], first_name: Optional[str]) -> User:
        user = self.get_by_id(user_id)
        if user:
            return user
        user = User(user_id=user_id, username=username, first_name=first_name)
        self.db.add(user)
        self.db.commit()
        return user

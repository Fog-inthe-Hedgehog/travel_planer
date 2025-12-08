from typing import List
from sqlalchemy.orm import Session
from app.database.models import Task


class TaskRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, trip_id: int, description: str) -> Task:
        task = Task(trip_id=trip_id, description=description)
        self.db.add(task)
        self.db.commit()
        return task

    def list_for_trip(self, trip_id: int) -> List[Task]:
        return self.db.query(Task).filter(Task.trip_id == trip_id).all()

    def toggle_complete(self, task_id: int) -> bool:
        task = self.db.query(Task).filter(Task.task_id == task_id).first()
        if not task:
            return False
        task.is_completed = not task.is_completed
        self.db.commit()
        return True

    def delete(self, task_id: int) -> bool:
        task = self.db.query(Task).filter(Task.task_id == task_id).first()
        if not task:
            return False
        self.db.delete(task)
        self.db.commit()
        return True
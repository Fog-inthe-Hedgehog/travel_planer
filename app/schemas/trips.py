from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class TripBase(BaseModel):
    destination: str
    start_date: datetime
    end_date: datetime
    notes: Optional[str] = None

class TripCreate(TripBase):
    pass

class TripResponse(TripBase):
    trip_id: int
    user_id: int

    class Config:
        from_attributes = True

class TaskBase(BaseModel):
    description: str
    is_completed: bool = False

class TaskCreate(TaskBase):
    trip_id: int

class TaskResponse(TaskBase):
    task_id: int
    trip_id: int

    class Config:
        from_attributes = True
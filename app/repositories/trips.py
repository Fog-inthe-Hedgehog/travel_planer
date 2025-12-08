from typing import List, Optional
from sqlalchemy.orm import Session
from app.database.models import Trip


class TripRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, user_id: int, destination: str, start_date, end_date, notes: Optional[str]) -> Trip:
        trip = Trip(
            user_id=user_id,
            destination=destination,
            start_date=start_date,
            end_date=end_date,
            notes=notes,
        )
        self.db.add(trip)
        self.db.commit()
        return trip

    def list_for_user(self, user_id: int) -> List[Trip]:
        return self.db.query(Trip).filter(Trip.user_id == user_id).order_by(Trip.start_date.desc()).all()

    def get(self, trip_id: int) -> Optional[Trip]:
        return self.db.query(Trip).filter(Trip.trip_id == trip_id).first()

    def delete(self, trip_id: int) -> bool:
        trip = self.get(trip_id)
        if not trip:
            return False
        self.db.delete(trip)
        self.db.commit()
        return True

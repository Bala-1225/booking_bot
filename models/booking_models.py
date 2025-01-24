# booking_models.py
from pydantic import BaseModel
from datetime import datetime

class BookingCreate(BaseModel):
    from_date: datetime
    to_date: datetime

class BookingRead(BaseModel):
    booking_id: int
    from_date: datetime
    to_date: datetime

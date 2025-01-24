# booking_routes.py
from fastapi import APIRouter, HTTPException
from models.booking_models import BookingCreate, BookingRead
from datetime import datetime
from typing import List

# Router
booking_router = APIRouter()

# In-memory storage
bookings = []
booking_counter = 1

@booking_router.post("/booking", response_model=BookingRead)
def create_booking(booking: BookingCreate):
    global booking_counter
    if booking.from_date >= booking.to_date:
        raise HTTPException(status_code=400, detail="from_date must be earlier than to_date")

    new_booking = {
        "booking_id": booking_counter,
        "from_date": booking.from_date,
        "to_date": booking.to_date,
    }
    bookings.append(new_booking)
    booking_counter += 1
    return new_booking

@booking_router.post("/booking/quarter/", response_model=List[BookingCreate])
def get_bookings_for_quarter():
    now = datetime.now()
    quarter_start_month = (now.month - 1) // 3 * 3 + 1
    quarter_end_month = quarter_start_month + 2
    quarter_start = datetime(now.year, quarter_start_month, 1)

    if quarter_end_month == 12:
        quarter_end = datetime(now.year + 1, 1, 1)
    else:
        quarter_end = datetime(now.year, quarter_end_month + 1, 1)

    return [
        booking for booking in bookings
        if booking["from_date"] >= quarter_start and booking["to_date"] < quarter_end
    ]

@booking_router.get("/booking/{booking_id}", response_model=BookingRead)
def get_booking(booking_id: int):
    for booking in bookings:
        if booking["booking_id"] == booking_id:
            return booking
    raise HTTPException(status_code=404, detail="Booking not found")

@booking_router.delete("/booking/{booking_id}")
def delete_booking(booking_id: int):
    global bookings
    bookings = [record for record in bookings if record["booking_id"] != booking_id]
    return {"detail": "Booking deleted successfully"}

@booking_router.get("/booking-on-date/{date}", response_model=List[BookingRead])
def get_booking_on_date(date: datetime):
    bookings_on_date = [
        booking for booking in bookings
        if booking["from_date"] <= date <= booking["to_date"]
    ]
    if not bookings_on_date:
        raise HTTPException(status_code=404, detail="No bookings found on the given date")
    return bookings_on_date

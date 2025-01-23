from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
import openai
import requests

import os

# Retrieve the OpenAI API key from an environment variable
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError("OpenAI API Key is not set. Please set it in the environment variables.")

# FastAPI instance
app = FastAPI()

# Data models
class BookingCreate(BaseModel):
    from_date: datetime
    to_date: datetime

class BookingRead(BaseModel):
    booking_id: int
    from_date: datetime
    to_date: datetime

# In-memory booking storage
bookings = []
booking_counter = 1

# FastAPI endpoint URL for booking API (could be used for external integration)
FASTAPI_URL = "http://127.0.0.1:8000/booking"

# Function to interact with OpenAI API
def ask_gpt(prompt):
    """Uses GPT to generate a conversational response."""
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
    )
    return response["choices"][0]["message"]["content"]

class BookingBot:
    def __init__(self):
        self.conversation_log = []
        self.booking_data = {"from_date": None, "to_date": None}

    def validate_date(self, date_str):
        """Validates the date format."""
        try:
            return datetime.fromisoformat(date_str)
        except ValueError:
            return None

    def collect_information(self):
        """Collects booking information from the user interactively."""
        # Greeting and asking for start date
        prompt = "Bot: Hi! I'll assist you in making a booking. First, please provide the start date (format: YYYY-MM-DDTHH:MM:SS)."
        print(prompt)
        self.conversation_log.append({"role": "assistant", "content": prompt})

        while not self.booking_data["from_date"]:
            user_input = input("User: ")
            self.conversation_log.append({"role": "user", "content": user_input})

            bot_reply = ask_gpt("Can you confirm the start date for the booking?")
            print(f"Bot: {bot_reply}")

            # Validate the start date
            date = self.validate_date(user_input)
            if date:
                self.booking_data["from_date"] = date.isoformat()
            else:
                prompt = "Bot: I couldn’t understand that date. Please use the format: YYYY-MM-DDTHH:MM:SS (e.g., 2025-01-25T10:00:00)."
                print(prompt)
                self.conversation_log.append({"role": "assistant", "content": prompt})

        # Asking for the end date
        while not self.booking_data["to_date"]:
            user_input = input("User: ")
            self.conversation_log.append({"role": "user", "content": user_input})

            bot_reply = ask_gpt("Can you confirm the end date for the booking?")
            print(f"Bot: {bot_reply}")

            # Validate the end date
            date = self.validate_date(user_input)
            if date:
                self.booking_data["to_date"] = date.isoformat()
            else:
                prompt = "Bot: That doesn’t seem like a valid date. Please provide it in the correct format: YYYY-MM-DDTHH:MM:SS."
                print(prompt)
                self.conversation_log.append({"role": "assistant", "content": prompt})

        # Ensure from_date is earlier than to_date
        from_date = datetime.fromisoformat(self.booking_data["from_date"])
        to_date = datetime.fromisoformat(self.booking_data["to_date"])
        if from_date >= to_date:
            correction_prompt = "Bot: Oops! The start date must be earlier than the end date. Let's try again!"
            print(correction_prompt)
            self.conversation_log.append({"role": "assistant", "content": correction_prompt})
            self.booking_data = {"from_date": None, "to_date": None}
            return self.collect_information()

        confirmation_prompt = f"Bot: Your booking is from {self.booking_data['from_date']} to {self.booking_data['to_date']}. Is that correct?"
        print(confirmation_prompt)
        self.conversation_log.append({"role": "assistant", "content": confirmation_prompt})

    def call_api(self):
        """Call the FastAPI endpoint to create the booking."""
        try:
            response = requests.post(FASTAPI_URL, json=self.booking_data)
            if response.status_code == 200:
                booking = response.json()
                success_prompt = f"Bot: Your booking has been confirmed! Booking ID: {booking['booking_id']}"
                print(success_prompt)
                self.conversation_log.append({"role": "assistant", "content": success_prompt})
            else:
                error_message = f"Bot: Oops! Something went wrong. Server says: {response.json().get('detail')}"
                print(error_message)
                self.conversation_log.append({"role": "assistant", "content": error_message})
        except Exception as e:
            error_message = f"Bot: There was an error calling the API: {e}"
            print(error_message)
            self.conversation_log.append({"role": "assistant", "content": error_message})

# FastAPI endpoint to create bookings
@app.post("/booking", response_model=BookingRead)
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

@app.post("/booking/quarter/", response_model=List[BookingCreate])
def get_bookings_for_quarter():
    now = datetime.now()
    quarter_start_month = (now.month - 1) // 3 * 3 + 1
    quarter_end_month = quarter_start_month + 2
    quarter_start = datetime(now.year, quarter_start_month, 1)

    if quarter_end_month == 12:
        quarter_end = datetime(now.year + 1, 1, 1)
    else:
        quarter_end = datetime(now.year, quarter_end_month + 1, 1)

    return [booking for booking in bookings if booking["from_date"] >= quarter_start and booking["to_date"] < quarter_end]

@app.get("/booking/{booking_id}", response_model=BookingRead)
def get_booking(booking_id: int):
    for booking in bookings:
        if booking["booking_id"] == booking_id:
            return booking
    raise HTTPException(status_code=404, detail="Booking not found")

@app.delete("/booking/{booking_id}")
def delete_booking(booking_id: int):
    global bookings
    bookings = [record for record in bookings if record["booking_id"] != booking_id]
    return {"detail": "Booking deleted successfully"}

@app.get("/booking-on-date/{date}", response_model=List[BookingRead])
def get_booking_on_date(date: datetime):
    bookings_on_date = [
        booking for booking in bookings
        if booking["from_date"] <= date <= booking["to_date"]
    ]
    if not bookings_on_date:
        raise HTTPException(status_code=404, detail="No bookings found on the given date")
    return bookings_on_date

@app.get("/get-my-booking/", response_model=List[BookingRead])
def get_my_booking():
    now = datetime.date()
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

@app.delete("/unbook/{date}", response_model=List[BookingRead])
def unbook_specific_date(date: datetime):
    global bookings
    updated_bookings = []
    for booking in bookings:
        if booking["from_date"] <= date <= booking["to_date"]:
            if booking["from_date"] == date:
                continue  # Remove this booking if the date matches
        updated_bookings.append(booking)

    if len(updated_bookings) == len(bookings):
        raise HTTPException(status_code=404, detail="No booking found on the given date")

    bookings = updated_bookings
    return bookings

# Main bot execution for testing
if __name__ == "__main__":
    bot = BookingBot()
    bot.collect_information()
    bot.call_api()

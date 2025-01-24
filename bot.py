# bot.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
from typing import List
import openai
import requests

# --- OpenAI API Key Configuration ---
OPENAI_API_KEY = "openai_api_key" 
if not OPENAI_API_KEY:
    raise ValueError("OpenAI API Key is not set. Please provide it in the code.")

openai.api_key = OPENAI_API_KEY  # Initialize OpenAI with the API key

# --- Initialize FastAPI ---
app = FastAPI()

# --- Data Models ---
class BookingCreate(BaseModel):
    """Model for creating a booking."""
    from_date: datetime
    to_date: datetime

class BookingRead(BaseModel):
    """Model for reading booking details."""
    booking_id: int
    from_date: datetime
    to_date: datetime

bookings = [] 
booking_counter = 1  # Tracks unique booking IDs

# Hardcoded public FastAPI URL
PUBLIC_API_URL = "http://0.0.0.0:8000/booking"

def ask_gpt(prompt, conversation_log):
    """
    Interacts with GPT to generate responses.
    - `prompt`: The instruction or message for GPT.
    - `conversation_log`: The previous conversation history for context.
    Returns the generated response as text.
    """
    messages = conversation_log + [{"role": "user", "content": prompt}]
    response = openai.chat.completions.create(
        model="gpt-4",  # Replace with your desired GPT model
        messages=messages,
    )
    return response["choices"][0]["message"]["content"]


# --- Booking Bot ---
class BookingBot:
    """
    The BookingBot collects user input interactively and validates it.
    It dynamically generates responses using OpenAI GPT.
    """
    def __init__(self):
        self.conversation_log = []  # Stores the history of the conversation
        self.booking_data = {"from_date": None, "to_date": None}  # Booking details

    def validate_date(self, date_str):
        """Validates if a string is a valid ISO 8601 date."""
        try:
            return datetime.fromisoformat(date_str)
        except ValueError:
            return None

    def collect_information(self):
        """Interactively collects booking information using GPT."""
        # Greet the user and ask for the start date
        greeting_prompt = "You are a helpful booking assistant bot. Start by greeting the user and asking for the start date in ISO format (YYYY-MM-DDTHH:MM:SS)."
        bot_reply = (greeting_prompt, self.conversation_log)
        print(f"Bot: {bot_reply}")
        self.conversation_log.append({"role": "assistant", "content": bot_reply})

        # Collect 'from_date'
        while not self.booking_data["from_date"]:
            user_input = input("User: ")
            self.conversation_log.append({"role": "user", "content": user_input})
            
            bot_reply = (
                f"Validate if '{user_input}' is a valid start date. If invalid, ask the user to provide it in ISO format.", 
                self.conversation_log
            )
            print(f"Bot: {bot_reply}")
            date = self.validate_date(user_input)
            if date:
                self.booking_data["from_date"] = date.isoformat()
            else:
                self.conversation_log.append({"role": "assistant", "content": bot_reply})

        # Collect 'to_date'
        while not self.booking_data["to_date"]:
            bot_reply = ("Ask the user to provide the end date of the booking in ISO format.", self.conversation_log)
            print(f"Bot: {bot_reply}")
            
            user_input = input("User: ")
            self.conversation_log.append({"role": "user", "content": user_input})

            bot_reply = (
                f"Validate if '{user_input}' is a valid end date. If invalid, ask the user to provide it in ISO format.", 
                self.conversation_log
            )
            print(f"Bot: {bot_reply}")
            date = self.validate_date(user_input)
            if date:
                self.booking_data["to_date"] = date.isoformat()
            else:
                self.conversation_log.append({"role": "assistant", "content": bot_reply})

        # Validate the date range
        from_date = datetime.fromisoformat(self.booking_data["from_date"])
        to_date = datetime.fromisoformat(self.booking_data["to_date"])
        if from_date >= to_date:
            error_prompt = "The start date must be earlier than the end date. Ask the user to re-enter both dates."
            bot_reply = (error_prompt, self.conversation_log)
            print(f"Bot: {bot_reply}")
            self.conversation_log.append({"role": "assistant", "content": bot_reply})
            self.booking_data = {"from_date": None, "to_date": None}
            return self.collect_information()

        # Confirm the booking details
        confirmation_prompt = f"The booking is from {self.booking_data['from_date']} to {self.booking_data['to_date']}. Ask for confirmation."
        bot_reply = (confirmation_prompt, self.conversation_log)
        print(f"Bot: {bot_reply}")
        self.conversation_log.append({"role": "assistant", "content": bot_reply})

    def call_api(self):
        """Calls the FastAPI endpoint to create a booking."""
        try:
            response = requests.post(self.PUBLIC_API_URL, json=self.booking_data)
            if response.status_code == 200:
                booking = response.json()
                bot_reply = f"Your booking has been confirmed! Booking ID: {booking['booking_id']}."
            else:
                bot_reply = f"Failed to create booking. Server response: {response.json().get('detail', 'Unknown error')}."
        except Exception as e:
            bot_reply = f"There was an error calling the API: {e}."
        
        self.conversation_log.append({"role": "assistant", "content": bot_reply})
        return bot_reply



# --- FastAPI Endpoints ---
@app.post("/booking", response_model=BookingRead)
def create_booking(booking: BookingCreate):
    """Endpoint to create a new booking."""
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


@app.get("/booking/{booking_id}", response_model=BookingRead)
def get_booking(booking_id: int):
    """Endpoint to retrieve a booking by ID."""
    for booking in bookings:
        if booking["booking_id"] == booking_id:
            return booking
    raise HTTPException(status_code=404, detail="Booking not found")


@app.delete("/booking/{booking_id}")
def delete_booking(booking_id: int):
    """Endpoint to delete a booking."""
    global bookings
    bookings = [record for record in bookings if record["booking_id"] != booking_id]
    return {"detail": "Booking deleted successfully"}


# --- Main Execution ---
if __name__ == "__main__":
    import uvicorn
    bot = BookingBot()
    bot.collect_information()
    bot.call_api()
    # Run the FastAPI app on a public IP address
    uvicorn.run(app, host="0.0.0.0", port=8000)

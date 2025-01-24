#main.py
from fastapi import FastAPI
from routes.booking_routes import booking_router
from routes.bot_routes import bot_router

# Initialize FastAPI application
app = FastAPI(
    title="Booking API with Chatbot",
    description="API for managing bookings and interacting with a chatbot assistant.",
    version="1.1.0",
)

# Include routers
app.include_router(booking_router)
app.include_router(bot_router)

# Root endpoint
@app.get("/")
def read_root():
    return {"message": "Welcome to the Booking API and Chatbot Assistant!"}

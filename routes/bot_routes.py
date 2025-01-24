from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from bot import BookingBot  # Importing the BookingBot class
from bot import ask_gpt

# Router
bot_router = APIRouter()

# Initialize the bot instance
bot = BookingBot()

# Chatbot response endpoint
@bot_router.post("/chatbot")
def chatbot_interaction(user_query: dict):
    """
    Handles user interactions via the chatbot.
    Expects input in the format:
    {
        "query": "User's input string"
    }
    """
    user_input = user_query.get("query")
    if not user_input:
        raise HTTPException(status_code=400, detail="Query input is required.")

    # Add the user's query to the conversation log
    bot.conversation_log.append({"role": "user", "content": user_input})

    # Ask the bot to generate a response
    bot_reply = bot.ask_gpt(
        prompt=user_input,
        conversation_log=bot.conversation_log,
    )
    bot.conversation_log.append({"role": "assistant", "content": bot_reply})

    return JSONResponse(content={"response": bot_reply})

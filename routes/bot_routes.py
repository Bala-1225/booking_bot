from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Router
bot_router = APIRouter()

# GPT-4o-mini LLM simulation (replace with actual LLM integration in production)
def gpt4o_mini_conversation(user_input: str) -> str:
    if "booking" in user_input.lower():
        return "Sure, I can help you with booking slots. Would you like to book for the current quarter or a specific date?"
    elif "cancel" in user_input.lower():
        return "Alright, please provide the booking ID or date you'd like to cancel."
    else:
        return "I’m here to assist you with booking or canceling office slots. How can I help you today?"

# Chatbot request model
class UserQuery(BaseModel):
    query: str

# Chatbot response endpoint
@bot_router.post("/chatbot")
def chatbot_interaction(user_query: UserQuery):
    user_input = user_query.query
    response = gpt4o_mini_conversation(user_input)
    return JSONResponse(content={"response": response})

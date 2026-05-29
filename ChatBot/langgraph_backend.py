from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated

from langchain_groq import ChatGroq
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

from langgraph.prebuilt import ToolNode, tools_condition

from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import tool

from langgraph.checkpoint.sqlite import SqliteSaver

from dotenv import load_dotenv

import sqlite3
import requests
import os


# =========================================================
# LOAD ENV VARIABLES
# =========================================================
load_dotenv()

WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")


# =========================================================
# CHAT STATE
# =========================================================
class ChatState(TypedDict):

    # Store all conversation messages
    messages: Annotated[
        list[BaseMessage],
        add_messages
    ]


# =========================================================
# INITIALIZE LLM
# =========================================================
llm = ChatGroq(
    model="llama-3.1-8b-instant"
)


# =========================================================
# SEARCH TOOL
# =========================================================
search_tool = DuckDuckGoSearchRun(
    region="us-en"
)


# =========================================================
# CALCULATOR TOOL
# =========================================================
@tool
def calculator(
    first_number: float,
    second_number: float,
    operation: str
) -> dict:
    """
    Perform basic arithmetic operations.
    """

    if operation == "add":
        result = first_number + second_number

    elif operation == "subtract":
        result = first_number - second_number

    elif operation == "multiply":
        result = first_number * second_number

    elif operation == "divide":

        if second_number == 0:
            return {
                "error": "Cannot divide by zero."
            }

        result = first_number / second_number

    else:
        return {
            "error": (
                "Invalid operation. "
                "Use add, subtract, multiply, or divide."
            )
        }

    return {
        "result": result
    }


# =========================================================
# WEATHER TOOL
# =========================================================
@tool
def weather_search(city: str) -> dict:
    """
    Get current weather for a city
    using OpenWeatherMap API.
    """

    # -----------------------------------------------------
    # GEOCODING API
    # Convert city name -> latitude/longitude
    # -----------------------------------------------------
    geo_url = (
        "http://api.openweathermap.org/geo/1.0/direct"
    )

    geo_params = {
        "q": city,
        "limit": 1,
        "appid": WEATHER_API_KEY
    }

    geo_response = requests.get(
        geo_url,
        params=geo_params
    )

    geo_data = geo_response.json()

    # -----------------------------------------------------
    # HANDLE INVALID CITY
    # -----------------------------------------------------
    if not geo_data:
        return {
            "error": "City not found."
        }

    # Extract coordinates
    lat = geo_data[0]["lat"]
    lon = geo_data[0]["lon"]

    # -----------------------------------------------------
    # WEATHER API
    # -----------------------------------------------------
    weather_url = (
        "https://api.openweathermap.org/data/2.5/weather"
    )

    weather_params = {
        "lat": lat,
        "lon": lon,
        "appid": WEATHER_API_KEY,
        "units": "metric"
    }

    weather_response = requests.get(
        weather_url,
        params=weather_params
    )

    weather_data = weather_response.json()

    # -----------------------------------------------------
    # RETURN CLEAN RESPONSE
    # -----------------------------------------------------
    return {
        "city": city,
        "temperature": weather_data["main"]["temp"],
        "humidity": weather_data["main"]["humidity"],
        "weather": weather_data["weather"][0]["description"],
        "wind_speed": weather_data["wind"]["speed"]
    }


# =========================================================
# LIST OF TOOLS
# =========================================================
tools = [
    search_tool,
    calculator,
    weather_search
]


# =========================================================
# BIND TOOLS WITH LLM
# =========================================================
llm_with_tools = llm.bind_tools(tools)


# =========================================================
# SQLITE CONNECTION
# =========================================================
conn = sqlite3.connect(
    database="chatbot_memory.db",
    check_same_thread=False
)


# =========================================================
# SQLITE CHECKPOINTER
# =========================================================
checkpointer = SqliteSaver(conn)


# =========================================================
# CHAT NODE
# =========================================================
def chat_node(state: ChatState):

    # Get conversation history
    messages = state["messages"]

    # Generate AI response
    response = llm_with_tools.invoke(messages)

    # Return updated messages
    return {
        "messages": [response]
    }


# =========================================================
# TOOL NODE
# =========================================================
tool_node = ToolNode(tools)


# =========================================================
# CREATE GRAPH
# =========================================================
graph = StateGraph(ChatState)


# =========================================================
# ADD NODES
# =========================================================
graph.add_node(
    "chat_node",
    chat_node
)

graph.add_node(
    "tools",
    tool_node
)


# =========================================================
# ADD EDGES
# =========================================================
graph.add_edge(
    START,
    "chat_node"
)

graph.add_conditional_edges(
    "chat_node",
    tools_condition
)

graph.add_edge(
    "tools",
    "chat_node"
)


# =========================================================
# COMPILE GRAPH
# =========================================================
chat_bot = graph.compile(
    checkpointer=checkpointer
)


# =========================================================
# GET ALL THREADS
# =========================================================
def get_all_threads():

    all_threads = set()

    # Iterate through checkpoints
    for checkpoint in checkpointer.list(None):

        thread_id = checkpoint.config[
            "configurable"
        ]["thread_id"]

        all_threads.add(thread_id)

    return list(all_threads)
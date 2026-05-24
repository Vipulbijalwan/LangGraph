from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated

from langchain_groq import ChatGroq
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

from langgraph.checkpoint.sqlite import SqliteSaver

from dotenv import load_dotenv

import sqlite3


# =========================================================
# LOAD ENV VARIABLES
# =========================================================
load_dotenv()


# =========================================================
# CHAT STATE
# =========================================================
class ChatState(TypedDict):

    # Store conversation messages
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
# CHAT NODE
# =========================================================
def chat_node(state: ChatState):

    # Get conversation messages
    messages = state["messages"]

    # Generate AI response
    response = llm.invoke(messages)

    # Return updated state
    return {
        "messages": [response]
    }


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


# =========================================================
# ADD EDGES
# =========================================================
graph.add_edge(START, "chat_node")
graph.add_edge("chat_node", END)


# =========================================================
# COMPILE GRAPH
# =========================================================
chat_bot = graph.compile(
    checkpointer=checkpointer
)


# =========================================================
# GET ALL THREADS
# =========================================================
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
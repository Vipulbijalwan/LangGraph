from typing import TypedDict, Annotated
import asyncio

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import BaseMessage
from langchain_core.tools import tool

from langgraph.graph import StateGraph, START
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

# Load environment variables
load_dotenv()

# Create LLM
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0
)

# Create Tool
@tool
def calculator(
    first_number: float,
    second_number: float,
    operation: str
) -> str:
    """Perform basic calculations."""

    if operation == "add":
        return str(first_number + second_number)

    elif operation == "subtract":
        return str(first_number - second_number)

    elif operation == "multiply":
        return str(first_number * second_number)

    elif operation == "divide":

        if second_number == 0:
            return "Cannot divide by zero"

        return str(first_number / second_number)

    return "Invalid operation"

# Tools list
tools = [calculator]

# Bind tools with LLM
llm_with_tools = llm.bind_tools(tools)

# Create State
class ChatState(TypedDict):

    messages: Annotated[
        list[BaseMessage],
        add_messages
    ]

# Chat Node
async def chat_node(state: ChatState):

    response = await llm_with_tools.ainvoke(
        state["messages"]
    )

    return {
        "messages": [response]
    }

# Build Graph
def build_graph():

    graph = StateGraph(ChatState)

    graph.add_node("chat_node", chat_node)

    tool_node = ToolNode(tools)

    graph.add_node("tools", tool_node)

    graph.add_edge(START, "chat_node")

    graph.add_conditional_edges(
        "chat_node",
        tools_condition
    )

    graph.add_edge("tools", "chat_node")

    chatbot = graph.compile()

    return chatbot

# Main Function
async def main():

    chatbot = build_graph()

    result = await chatbot.ainvoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "Add 10 and 20"
                }
            ]
        }
    )

    print("\n=========== RESULT ===========\n")

    print(result["messages"][-1].content)

    print("\n==============================\n")

# Run Program
if __name__ == "__main__":

    asyncio.run(main())
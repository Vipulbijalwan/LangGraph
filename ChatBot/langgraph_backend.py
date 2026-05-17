from langgraph.graph import StateGraph, START, END
from typing import TypedDict,Annotated
from langchain_groq import ChatGroq
from dotenv import load_dotenv
from pydantic import BaseModel,Field
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage,BaseMessage

load_dotenv()

class ChatState(TypedDict):
    message: Annotated[list[BaseMessage], add_messages]

llm = ChatGroq(
    model="llama-3.3-70b-versatile"   # You can change model here
)

def chat_node(state:ChatState):
    messages = state['message']
    response = llm.invoke(messages)
    return {"messages": [response]}

checkpointer =InMemorySaver()

graph = StateGraph(ChatState)
graph.add_node('chat_node',chat_node)


graph.add_edge(START, 'chat_node')
graph.add_edge('chat_node', END)

chat_bot=graph.compile(checkpointer=checkpointer)
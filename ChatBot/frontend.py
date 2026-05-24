import streamlit as st
import uuid

# =========================================================
# IMPORTS
# =========================================================
from langgraph_backend import chat_bot, get_all_threads
from langchain_core.messages import HumanMessage


# =========================================================
# PAGE CONFIGURATION
# =========================================================
st.set_page_config(
    page_title="LangGraph Chatbot",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 LangGraph Chatbot")


# =========================================================
# GENERATE UNIQUE THREAD ID
# =========================================================
def generate_thread_id():
    """
    Generate unique conversation ID.
    """
    return str(uuid.uuid4())


# =========================================================
# ADD THREAD TO SIDEBAR
# =========================================================
def add_thread(thread_id):
    """
    Add thread to session state.
    """
    if thread_id not in st.session_state["chat_threads"]:
        st.session_state["chat_threads"].append(thread_id)


# =========================================================
# RESET CHAT
# =========================================================
def reset_chat():
    """
    Create new chat session.
    """

    # Save current thread
    add_thread(st.session_state["thread_id"])

    # Clear messages
    st.session_state["message_history"] = []

    # Create new thread
    st.session_state["thread_id"] = generate_thread_id()


# =========================================================
# LOAD CONVERSATION
# =========================================================
def load_conversation(thread_id):
    """
    Load conversation from LangGraph memory.
    """

    try:
        state = chat_bot.get_state(
            config={
                "configurable": {
                    "thread_id": thread_id
                }
            }
        )

        # Safely return messages
        return state.values.get("messages", [])

    except Exception as e:
        st.error(f"Error loading conversation: {e}")
        return []


# =========================================================
# SESSION STATE INITIALIZATION
# =========================================================

# Current visible messages
if "message_history" not in st.session_state:
    st.session_state["message_history"] = []

# Current thread
if "thread_id" not in st.session_state:
    st.session_state["thread_id"] = generate_thread_id()

# All threads
if "chat_threads" not in st.session_state:
    st.session_state["chat_threads"] = get_all_threads()

# Add current thread
add_thread(st.session_state["thread_id"])


# =========================================================
# SIDEBAR
# =========================================================
with st.sidebar:

    st.header("💬 Conversations")

    # New chat button
    if st.button("➕ New Chat"):
        reset_chat()

    st.markdown("---")

    # Show all saved threads
    for index, thread_id in enumerate(
        st.session_state["chat_threads"]
    ):

        # Short display name
        display_name = f"Chat {index + 1}"

        if st.button(display_name):

            # Set current thread
            st.session_state["thread_id"] = thread_id

            # Load messages
            messages = load_conversation(thread_id)

            temp_messages = []

            # Convert LangChain format
            for message in messages:

                if isinstance(message, HumanMessage):

                    temp_messages.append({
                        "role": "user",
                        "content": message.content
                    })

                else:

                    temp_messages.append({
                        "role": "assistant",
                        "content": message.content
                    })

            # Update UI history
            st.session_state["message_history"] = temp_messages


# =========================================================
# DISPLAY OLD MESSAGES
# =========================================================
for message in st.session_state["message_history"]:

    with st.chat_message(message["role"]):

        st.markdown(message["content"])


# =========================================================
# USER INPUT
# =========================================================
user_input = st.chat_input(
    "Type your message..."
)


# =========================================================
# HANDLE CHAT
# =========================================================
if user_input:

    # -----------------------------------------------------
    # SAVE USER MESSAGE
    # -----------------------------------------------------
    st.session_state["message_history"].append({
        "role": "user",
        "content": user_input
    })

    # -----------------------------------------------------
    # DISPLAY USER MESSAGE
    # -----------------------------------------------------
    with st.chat_message("user"):

        st.markdown(user_input)

    # -----------------------------------------------------
    # ASSISTANT RESPONSE
    # -----------------------------------------------------
    with st.chat_message("assistant"):

        response_container = st.empty()

        full_response = ""

        try:

            # Stream response
            for chunk, metadata in chat_bot.stream(

                {
                    "messages": [
                        HumanMessage(content=user_input)
                    ]
                },

                config={
                    "configurable": {
                        "thread_id":
                        st.session_state["thread_id"]
                    }
                },

                stream_mode="messages"
            ):

                # Safely append streamed chunks
                if hasattr(chunk, "content"):

                    full_response += chunk.content

                    response_container.markdown(
                        full_response
                    )

        except Exception as e:

            full_response = f"Error: {e}"

            response_container.error(full_response)

        # -------------------------------------------------
        # SAVE ASSISTANT MESSAGE
        # -------------------------------------------------
        st.session_state["message_history"].append({
            "role": "assistant",
            "content": full_response
        })
import streamlit as st
import requests
from datetime import datetime

messages_history = []

for message in messages_history:
    with st.chat_message(message['role']):
        st.text(message['content'])

user_input= st.chat_input("Type your message here...")

if user_input:

    messages_history.append({'role':'user','content':user_input})

    with st.chat_message("user"):
        st.text(user_input)

    messages_history.append({'role':'assistant','content':user_input})

    with st.chat_message("assistant"):
        st.text(user_input)

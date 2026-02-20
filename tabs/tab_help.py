"""
NERO-Time - HELP TAB
"""

import streamlit as st
from openai import OpenAI
from nero_logic import NeroTimeLogic

#OpenAI Config for the chatbot
MODEL = "gpt-4.1-mini"

SYSTEM_PROMPT = """
You are the AI assistant for the NERO-Time productivity app.

Your goals:
- Help users understand how to use the app
- Answer questions clearly
- Be friendly and concise
- Give practical guidance
- Refuse to answer anything other than time management/app related stuff
- 
"""

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

#The singular code for the expander box but I can change the text size simply because I wanted the UI to look slightly nicer

def large_expander(label, expanded=False, size=22):
    st.markdown(f"""
    <style>
    div[data-testid="stExpander"] > details > summary p {{
        font-size: {size}px !important;
        font-weight: 600;
    }}
    </style>
    """, unsafe_allow_html=True)
    return st.expander(label, expanded=expanded)
    
#Main Help Tab
def ui_help_tab():
    """Render Help Tab"""
    st.header("🔎 Help/Q&A")

    _render_FAQ()
    st.divider()
    _render_chatbot()

#The FAQ

def _render_FAQ():
    st.markdown("## ❓F&Q❓")

    with large_expander("Insert Question Here?", expanded=False, size=26):
        st.text("Hi. Insert answer here.")

#=============
#Chatbot here!!!!!
#=============

def render_chatbot():
    st.markdown("## 🤖 AI Assistant")

    # Initialize session chat
    if "nero_chat_messages" not in st.session_state:
        st.session_state.nero_chat_messages = []

    # -------------------
    # CLEAR CHAT BUTTON
    # -------------------
    col1, col2 = st.columns([6, 1])
    with col2:
        if st.button("🗑️ Clear Chat"):
            st.session_state.nero_chat_messages = []
            st.rerun()


    #chat fee(t) (get it bc its like chat feed)
    # Use a container so messages stay above input
    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.nero_chat_messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    #input box 
    prompt = st.chat_input("Ask me anything about NERO-Time...")

    if prompt:
        # Save user message
        st.session_state.nero_chat_messages.append({
            "role": "user",
            "content": prompt
        })

        # Display user message immediately
        with chat_container:
            with st.chat_message("user"):
                st.markdown(prompt)

        # Build messages with system prompt
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            *st.session_state.nero_chat_messages
        ]

        # Generate AI response
        with chat_container:
            with st.chat_message("assistant"):
                placeholder = st.empty()
                full_response = ""

                stream = client.chat.completions.create(
                    model=MODEL,
                    messages=messages,
                    stream=True
                )

                for chunk in stream:
                    delta = chunk.choices[0].delta.content or ""
                    full_response += delta
                    placeholder.markdown(full_response)

        # Save assistant message
        st.session_state.nero_chat_messages.append({
            "role": "assistant",
            "content": full_response
        })

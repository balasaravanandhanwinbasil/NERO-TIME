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

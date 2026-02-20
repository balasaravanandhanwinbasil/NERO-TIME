"""
NERO-Time - HELP TAB
"""

import streamlit as st
from nero_logic import NeroTimeLogic

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

def ui_help_tab():
  """Render the Verification tab — a TODO list of finished sessions."""
  st.header("🔎 Help/Q&A")
  _render_FAQ()

def _render_FAQ():
  st.markdown("## ❓F&Q❓")
  with st.expander("Insert Question Here?", expanded=False):
    st.text("Hi. Insert answer here.")
  

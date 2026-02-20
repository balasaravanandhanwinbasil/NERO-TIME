"""
NERO-Time - HELP TAB
"""

import streamlit as st
from nero_logic import NeroTimeLogic


def ui_help_tab():
  """Render the Verification tab — a TODO list of finished sessions."""
  st.header("🔎 Help/Q&A")
  st.caption("Find frequently asked questions for your problems. Ask the AI assistant for help when needed.")
  _render_FAQ()

def _render_FAQ():
  st.markdown("### F&Q❓")

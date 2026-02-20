"""
NERO-Time - HELP TAB
"""

import streamlit as st
from nero_logic import NeroTimeLogic


def ui_help_tab():
  """Render the Verification tab — a TODO list of finished sessions."""
  st.header("🔎 Help/Q&A")
  _render_FAQ()

def _render_FAQ():
  st.markdown("## ❓F&Q❓")
  st.markdown("###         Penis?")
  st.text("Testes")

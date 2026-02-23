"""
NERO-Time - HELP TAB
"""

import streamlit as st

#The singular code for the expander box but I can change the text size simply because I wanted the UI to look slightly nicer

def large_expander(label, expanded=False, size=24):
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

#The FAQ

def _render_FAQ():
    st.markdown("## ❓F&Q❓")

    with large_expander("## How do I begin using the app??", expanded=False, size=20):
        st.text("All you have to do is head down to 'activities' and 'events' and schedule your tasks that you need to do in activities, and compulsory events in events! Then just hit generate, and watch the magic happen.")
    with large_expander("## How do I contact the developers?", expanded=False, size=20):
        st.text("Our customer support hotline is lau_kai_rui_gavin@s2023.ssts.edu.sg")
    with large_expander("## Is my personal information safe?", expanded=False, size=20):
        st.text("Yes, your personal information is secure and unaccessable to anyone except for you. We can assure full, unexploitable safety of information data.")


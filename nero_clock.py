"""
Its called nero clock. its the clock update function. its really not as easy as you think it is. 
the entire point of having a seperate file for the clock is because by using a timer to update streamlit, it force reloads the entire page.
it makes the entire app basically unusable. This file is the code to allow the app to run and cock to tick simultaneously
"""

import streamlit as st
from datetime import datetime
import pytz
import asyncio
import nest_asyncio
from streamlit_autorefresh import st_autorefresh

def show_live_clock(timezone_str="Asia/Singapore"):
    """
    Display a live updating clock in Streamlit.
    Call this function in your main app where you want the clock to appear.
    """
    # Auto-refresh the page every 1 second
    st_autorefresh(interval=1000, limit=None, key="nero_live_clock")

    # Timezone setup
    tz = pytz.timezone(timezone_str)
    now = datetime.now(tz)

    # Display clock
    st.markdown(f"""
    <div class='live-clock'>
        <div class='clock-time'>{now.strftime('%H:%M:%S')}</div>
        <div class='clock-date'>{now.strftime('%A, %B %d, %Y')}</div>
    </div>
    """, unsafe_allow_html=True)

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
nest_asyncio.apply()

def create_clock_placeholder():
    """Returns a Streamlit placeholder for the live clock"""
    return st.empty()

async def _update_clock(clock_placeholder, timezone_str="Asia/Singapore"):
    tz = pytz.timezone(timezone_str)
    while True:
        now = datetime.now(tz)
        clock_placeholder.markdown(f"""
        <div class='live-clock'>
            <div class='clock-time'>{now.strftime('%H:%M:%S')}</div>
            <div class='clock-date'>{now.strftime('%A, %B %d, %Y')}</div>
        </div>
        """, unsafe_allow_html=True)
        await asyncio.sleep(1)

def start_live_clock(clock_placeholder, timezone_str="Asia/Singapore"):
    """Starts the live clock asynchronously"""
    try:
        asyncio.run(_update_clock(clock_placeholder, timezone_str))
    except RuntimeError:
        # Handles "asyncio.run() cannot be called from a running event loop" because without these lines my code decides to not work. 
        asyncio.get_event_loop().run_until_complete(
            _update_clock(clock_placeholder, timezone_str)
        )

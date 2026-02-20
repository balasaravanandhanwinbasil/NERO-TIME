"""
NERO-Time - HELP TAB
"""

import streamlit as st
from nero_logic import NeroTimeLogic


def ui_verification_tab():
  """Render the Verification tab — a TODO list of finished sessions."""
  st.header("🔎 Help/Q&A")
  st.caption("Find frequently asked questions for your problems. Ask the AI assistant for help when needed.")
  
  
def _render_session_group(sessions: list):
    """Render a list of finished-session rows, grouped by activity name."""
    by_activity: dict = {}
    for s in sessions:
        act = s.get('activity_name', 'Unknown')
        by_activity.setdefault(act, []).append(s)

    for activity_name, act_sessions in by_activity.items():
        st.markdown(f"**{activity_name}**")

        for s in act_sessions:
            session_id       = s.get('session_id')
            session_num      = s.get('session_num', '?')
            scheduled_date   = s.get('scheduled_date', '')
            scheduled_time   = s.get('scheduled_time', '')
            duration_minutes = s.get('duration_minutes', 0)
            is_completed     = s.get('is_completed', False)
            is_skipped       = s.get('is_skipped', False)
            is_verified      = is_completed or is_skipped

            # Status icon
            if not is_verified:
                left_icon = "⬜"
            elif is_completed:
                left_icon = "✅"
            else:
                left_icon = "❌"

            col_icon, col_info, col_done, col_skip = st.columns([0.08, 0.60, 0.16, 0.16])

            with col_icon:
                st.markdown(
                    f"<div style='font-size:22px; padding-top:8px'>{left_icon}</div>",
                    unsafe_allow_html=True
                )

            with col_info:
                st.markdown(f"Session {session_num}")
                st.caption(f"📅 {scheduled_date}  🕐 {scheduled_time}  ⏱ {duration_minutes} min")

            with col_done:
                done_type = "primary" if is_completed else "secondary"
                if st.button(
                    "✅ Done",
                    key=f"done_{session_id}",
                    use_container_width=True,
                    type=done_type,
                    help="Mark as completed"
                ):
                    result = NeroTimeLogic.verify_finished_session(session_id, True)
                    if result["success"]:
                        st.rerun()
                    else:
                        st.error(result.get("message", "Error"))

            with col_skip:
                skip_type = "primary" if is_skipped else "secondary"
                if st.button(
                    "❌ Skip",
                    key=f"skip_{session_id}",
                    use_container_width=True,
                    type=skip_type,
                    help="Mark as not done — will be rescheduled on next generation"
                ):
                    result = NeroTimeLogic.verify_finished_session(session_id, False)
                    if result["success"]:
                        st.rerun()
                    else:
                        st.error(result.get("message", "Error"))

        st.divider()

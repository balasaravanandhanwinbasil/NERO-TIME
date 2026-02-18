"""
NERO-Time - VERIFICATION TAB

A TODO-list of finished sessions.
  ✅  = done         → hours count as completed, not rescheduled
  ❌  = not done     → hours are added back and rescheduled on next generation
  ⬜  = not reviewed → awaiting user action
"""
import streamlit as st
from nero_logic import NeroTimeLogic


def ui_verification_tab():
    """Render the Verification tab — a TODO list of finished sessions."""
    st.header("✅ Session Verification")
    st.caption(
        "Mark each finished session as **done** or **not done**. "
        "Sessions marked ❌ will be rescheduled next time you generate the timetable."
    )

    finished_sessions = st.session_state.get('finished_sessions', [])

    if not finished_sessions:
        st.info("No finished sessions yet. Sessions appear here once their scheduled time has passed.")
        return

    pending  = [fs for fs in finished_sessions if not fs.get('is_verified', False)]
    reviewed = [fs for fs in finished_sessions if fs.get('is_verified', False)]

    # ── Pending (needs action) ────────────────────────────────────────────────
    if pending:
        st.markdown("### 🕐 Needs Review")
        _render_session_group(pending)
    else:
        st.success("✓ All finished sessions have been reviewed!")

    # ── Already reviewed (collapsible) ───────────────────────────────────────
    if reviewed:
        with st.expander(f"📋 Reviewed ({len(reviewed)})", expanded=False):
            _render_session_group(reviewed)


def _render_session_group(sessions: list):
    """Render a list of finished-session rows, grouped by activity name."""

    # Group by activity
    by_activity: dict = {}
    for fs in sessions:
        act = fs.get('activity', 'Unknown')
        by_activity.setdefault(act, []).append(fs)

    for activity_name, act_sessions in by_activity.items():
        st.markdown(f"**{activity_name}**")

        for fs in act_sessions:
            session_id      = fs.get('session_id')
            session_num     = fs.get('session_num', '?')
            scheduled_date  = fs.get('scheduled_date', '')
            scheduled_time  = fs.get('scheduled_time', '')
            duration_minutes = fs.get('duration_minutes', 0)
            is_verified     = fs.get('is_verified', False)
            was_completed   = fs.get('completed', False)

            # Status icon on the left
            if not is_verified:
                left_icon = "⬜"
            elif was_completed:
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
                # Highlight the active choice with primary style
                done_type = "primary" if (is_verified and was_completed) else "secondary"
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
                skip_type = "primary" if (is_verified and not was_completed) else "secondary"
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
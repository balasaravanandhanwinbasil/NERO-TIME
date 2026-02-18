"""
NERO-Time - ACTIVITIES TAB
"""
import streamlit as st
from datetime import datetime
from nero_logic import NeroTimeLogic
from Timetable_Generation import WEEKDAY_NAMES


def ui_activities_tab():
    """Render the Activities tab content."""
    st.header("Activities")

    _render_add_activity_form()

    st.divider()

    activities_data = NeroTimeLogic.get_activities_data()

    if activities_data['activities']:
        for idx, act in enumerate(activities_data['activities']):
            mode_badge = "🤖 Auto" if act.get('session_mode') == 'automatic' else "✋ Manual"
            with st.expander(
                f"{idx+1}. {act['activity']} "
                f"({act['progress']['completed']:.1f}h/{act['timing']:.1f}h) - {mode_badge}"
            ):
                st.progress(act['progress']['percentage'] / 100)
                st.caption(f"Deadline: {act['deadline']} days")

                if act.get('session_mode') == 'manual':
                    _render_manual_session_form(act, idx)
                    st.divider()

                _render_sessions_list(act)

                st.markdown("---")
                _render_activity_action_buttons(act, idx)
    else:
        st.info("No activities")


def _render_add_activity_form():
    """Render the Add Activity expander form."""
    with st.expander("➕ Add Activity", expanded=False):
        name = st.text_input("Name", key="activity_name")

        session_mode = st.radio(
            "Session Mode",
            ["Automatic", "Manual"],
            help="Automatic: AI schedules sessions. Manual: You add sessions yourself",
            horizontal=True,
            key="session_mode"
        )

        col1, col2 = st.columns(2)
        with col1:
            deadline = st.date_input("Deadline", min_value=datetime.now().date(), key="activity_deadline")
        with col2:
            hours = st.number_input("Hours", 1, 100, 1, key="activity_hours")

        if session_mode == "Automatic":
            col3, col4 = st.columns(2)
            with col3:
                min_s = st.number_input("Min Session (min)", 15, 180, 30, 15, key="min_s")
                min_s = int(((min_s + 7) // 15) * 15)
            with col4:
                max_s = st.number_input("Max Session (min)", 30, 240, 120, 15, key="max_s")
                max_s = int(((max_s + 7) // 15) * 15)
                if max_s < min_s:
                    max_s = min_s

            days = st.multiselect("Days", WEEKDAY_NAMES, WEEKDAY_NAMES, key="activity_days")
        else:
            min_s, max_s, days = 30, 120, None

        if st.button("Add", type="primary", use_container_width=True, key="btn_add_activity"):
            if name:
                result = NeroTimeLogic.add_activity(
                    name, 3, deadline.isoformat(), hours, min_s, max_s, days,
                    session_mode="manual" if session_mode == "Manual" else "automatic"
                )
                if result["success"]:
                    st.success("✓ Added")
                    st.rerun()
                else:
                    st.error(result["message"])


def _render_manual_session_form(act, idx):
    """Render the Add Manual Session form for manual-mode activities."""
    with st.form(key=f"add_manual_session_{idx}"):
        st.markdown("**➕ Add Manual Session**")
        col_dur, col_day = st.columns(2)
        with col_dur:
            manual_duration = st.number_input("Duration (min)", 15, 240, 60, 15, key=f"manual_dur_{idx}")
            manual_duration = int(((manual_duration + 7) // 15) * 15)
        with col_day:
            preferred_day = st.selectbox("Preferred Day (optional)", ["Any"] + WEEKDAY_NAMES, key=f"manual_day_{idx}")

        if st.form_submit_button("Add Session", use_container_width=True):
            result = NeroTimeLogic.add_manual_session(
                act['activity'],
                int(manual_duration),
                None if preferred_day == "Any" else preferred_day
            )
            if result["success"]:
                st.success("✓ Session added!")
                st.rerun()
            else:
                st.error(result["message"])


def _render_sessions_list(act):
    """Render the sessions list for an activity."""
    st.markdown("#### 📋 Sessions")
    sessions_data = act.get('sessions', [])

    if sessions_data:
        for sess_idx, session in enumerate(sessions_data):
            session_id = session.get('session_id', f"session_{sess_idx}")
            is_completed = session.get('is_completed', False)
            duration_hours = session.get('duration_hours', 0)
            duration_minutes = session.get('duration_minutes', 0)
            scheduled_day = session.get('scheduled_day')
            scheduled_time = session.get('scheduled_time')

            with st.container():
                col_s1, col_s2, col_s3 = st.columns([2, 2, 1])

                with col_s1:
                    status = "✅ Completed" if is_completed else "⚫ Pending"
                    st.markdown(f"**Session {sess_idx + 1}** - {status}")
                    st.caption(f"Duration: {duration_hours:.1f}h ({duration_minutes} min)")

                with col_s2:
                    if scheduled_day and scheduled_time:
                        st.caption(f"📅 {scheduled_day} at {scheduled_time}")
                    else:
                        st.caption("📅 Not scheduled yet")

                with col_s3:
                    if not is_completed:
                        edit_key = f"edit_session_{act['activity']}_{session_id}"
                        if st.button("✏️", key=edit_key, use_container_width=True):
                            st.session_state[f"editing_{edit_key}"] = True
                            st.rerun()

                # Edit form
                edit_state_key = f"editing_edit_session_{act['activity']}_{session_id}"
                if st.session_state.get(edit_state_key, False):
                    _render_session_edit_form(act, session_id, scheduled_time, duration_minutes, edit_state_key)

                st.divider()
    else:
        st.info("No sessions generated yet - generate a timetable to create sessions")


def _render_session_edit_form(act, session_id, scheduled_time, duration_minutes, edit_state_key):
    """Render the inline session edit form."""
    with st.form(key=f"form_{act['activity']}_{session_id}"):
        st.markdown("**Edit Session**")

        col_e1, col_e2, col_e3 = st.columns(3)

        with col_e1:
            default_date = datetime.now().date()
            new_date = st.date_input(
                "Date",
                value=default_date,
                min_value=datetime.now().date(),
                key=f"date_{session_id}"
            )

        with col_e2:
            default_time = (
                datetime.strptime(scheduled_time, "%H:%M").time()
                if scheduled_time else datetime.now().time()
            )
            new_time = st.time_input("Start Time", value=default_time, key=f"time_{session_id}")

        with col_e3:
            new_duration = st.number_input(
                "Duration (min)",
                min_value=15,
                max_value=240,
                value=duration_minutes,
                step=15,
                key=f"dur_{session_id}"
            )
            new_duration = ((new_duration + 7) // 15) * 15

        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            submitted = st.form_submit_button("💾 Save", type="primary", use_container_width=True)
        with col_btn2:
            cancelled = st.form_submit_button("❌ Cancel", use_container_width=True)

        if submitted:
            if act['deadline'] < 0:
                st.error("❌ Cannot edit - activity deadline has passed!")
            else:
                actual_day = WEEKDAY_NAMES[new_date.weekday()]
                result = NeroTimeLogic.edit_session(
                    act['activity'],
                    session_id,
                    new_day=actual_day,
                    new_start_time=new_time.strftime("%H:%M"),
                    new_duration=new_duration,
                    new_date=new_date.isoformat()
                )
                if result["success"]:
                    st.session_state[edit_state_key] = False
                    st.success("✓ Session updated!")
                    st.rerun()
                else:
                    st.error(result["message"])

        if cancelled:
            st.session_state[edit_state_key] = False
            st.rerun()


def _render_activity_action_buttons(act, idx):
    """Render Delete / Reset / Add buttons for an activity."""
    col1, col2, col3 = st.columns(3)

    if col1.button("Delete", key=f"del_activity_{idx}_{act['activity']}"):
        result = NeroTimeLogic.delete_activity(idx)
        if result["success"]:
            st.rerun()

    if col2.button("Reset", key=f"reset_activity_{idx}_{act['activity']}"):
        result = NeroTimeLogic.reset_activity_progress(act['activity'])
        if result["success"]:
            st.rerun()

    if col3.button("Add", key=f"add_activity_{idx}_{act['activity']}"):
        result = NeroTimeLogic.add_activity_progress(act['activity'])
        if result["success"]:
            st.rerun()
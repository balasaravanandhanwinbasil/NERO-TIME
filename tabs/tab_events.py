"""
NERO-Time - EVENTS + SCHEDULE TAB
"""
import streamlit as st
from datetime import datetime
from nero_logic import NeroTimeLogic
from Timetable_Generation import WEEKDAY_NAMES


def ui_events_tab():
    """Render the Events & Recurring Schedule tab content."""
    st.header("Events & Recurring Schedule")

    _render_add_event_form()

    st.divider()

    _render_recurring_schedules()

    st.divider()

    _render_one_time_events()


def _render_add_event_form():
    """Render the Add Event/Schedule expander form."""
    with st.expander("➕ Add Event/Schedule", expanded=False):
        event_name = st.text_input("Name", key="event_name")

        recurrence_type = st.radio(
            "Type",
            ["One-time Event", "Weekly", "Bi-weekly", "Monthly"],
            horizontal=True,
            key="recurrence_type"
        )

        col1, col2 = st.columns(2)
        with col1:
            start_t = st.time_input("Start", key="event_start_time")
        with col2:
            end_t = st.time_input("End", key="event_end_time")

        if recurrence_type in ["Weekly", "Bi-weekly"]:
            selected_days = st.multiselect("Days", WEEKDAY_NAMES, key="event_days")
            event_date = None
        else:
            selected_days = None
            event_date = st.date_input("Date", min_value=datetime.now().date(), key="event_date")

        if st.button("Add", type="primary", use_container_width=True, key="btn_add_event"):
            if event_name:
                if recurrence_type == "One-time Event":
                    result = NeroTimeLogic.add_event(
                        event_name,
                        event_date.isoformat(),
                        start_t.strftime("%H:%M"),
                        end_t.strftime("%H:%M")
                    )
                else:
                    recurrence_map = {
                        "Weekly": "weekly",
                        "Bi-weekly": "bi-weekly",
                        "Monthly": "monthly"
                    }
                    result = NeroTimeLogic.add_recurring_event(
                        event_name,
                        start_t.strftime("%H:%M"),
                        end_t.strftime("%H:%M"),
                        recurrence_map[recurrence_type],
                        selected_days,
                        event_date.isoformat() if event_date else None
                    )

                if result["success"]:
                    st.success("✓ Added")
                    st.rerun()
                else:
                    st.error(result["message"])


def _render_recurring_schedules():
    """Render the Recurring Schedules section."""
    st.markdown("### 📅 Recurring Schedules")
    school_data = NeroTimeLogic.get_school_schedule()

    if school_data['schedule']:
        for day in WEEKDAY_NAMES:
            if day in school_data['schedule']:
                with st.expander(f"{day} ({len(school_data['schedule'][day])} slots)"):
                    for idx, cls in enumerate(school_data['schedule'][day]):
                        col1, col2 = st.columns([4, 1])
                        with col1:
                            recurrence_badge = cls.get('recurrence', 'weekly').title()
                            st.write(f"**{cls['subject']}** ({recurrence_badge})")
                            st.caption(f"{cls['start_time']} - {cls['end_time']}")
                        with col2:
                            if st.button("×", key=f"del_school_{day}_{idx}"):
                                result = NeroTimeLogic.delete_school_schedule(day, idx)
                                if result["success"]:
                                    st.rerun()
    else:
        st.info("No recurring schedules")


def _render_one_time_events():
    """Render the One-time Events section."""
    st.markdown("### 📌 One-time Events")
    events_data = NeroTimeLogic.get_events_data()

    if events_data['events']:
        for idx, evt in enumerate(events_data['events']):
            with st.expander(f"{idx+1}. {evt['event']} - {evt['day']}"):
                st.write(f"{evt['start_time']} - {evt['end_time']}")
                if st.button("Delete", key=f"del_event_{idx}_{evt['event']}"):
                    result = NeroTimeLogic.delete_event(idx)
                    if result["success"]:
                        st.rerun()
    else:
        st.info("No one-time events")
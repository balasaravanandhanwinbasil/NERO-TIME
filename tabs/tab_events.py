"""
NERO-Time - EVENTS + SCHEDULE TAB
"""

import streamlit as st
from datetime import datetime
from nero_logic import NeroTimeLogic
from Timetable_Generation import WEEKDAY_NAMES, time_str_to_minutes


def _times_overlap(start1: str, end1: str, start2: str, end2: str) -> bool:
    """Return True if two time ranges overlap."""
    s1, e1 = time_str_to_minutes(start1), time_str_to_minutes(end1)
    s2, e2 = time_str_to_minutes(start2), time_str_to_minutes(end2)
    return not (e1 <= s2 or s1 >= e2)


def _get_clashes() -> list:
    """
    Check all recurring schedules and one-time events for time clashes
    on the same day. Returns a list of human-readable clash descriptions.
    """
    clashes = []

    # ── Clashes within recurring schedules (same weekday) ──────────────────────
    schedule = st.session_state.school_schedule
    for day_name, events in schedule.items():
        for i in range(len(events)):
            for j in range(i + 1, len(events)):
                a, b = events[i], events[j]
                if _times_overlap(a['start_time'], a['end_time'],
                                  b['start_time'], b['end_time']):
                    clashes.append(
                        f"**{day_name}** — "
                        f"'{a['subject']}' ({a['start_time']}–{a['end_time']}) "
                        f"clashes with "
                        f"'{b['subject']}' ({b['start_time']}–{b['end_time']})"
                    )

    # ── Clashes within one-time events (same day display) ──────────────────────
    one_time = st.session_state.list_of_compulsory_events
    for i in range(len(one_time)):
        for j in range(i + 1, len(one_time)):
            a, b = one_time[i], one_time[j]
            if a['day'] == b['day'] and _times_overlap(
                a['start_time'], a['end_time'],
                b['start_time'], b['end_time']
            ):
                clashes.append(
                    f"**{a['day']}** — "
                    f"'{a['event']}' ({a['start_time']}–{a['end_time']}) "
                    f"clashes with "
                    f"'{b['event']}' ({b['start_time']}–{b['end_time']})"
                )

    # ── Clashes between recurring schedules and one-time events ────────────────
    for evt in one_time:
        day_name = evt['day'].split()[0]
        if day_name in schedule:
            for recurring in schedule[day_name]:
                if _times_overlap(evt['start_time'], evt['end_time'],
                                  recurring['start_time'], recurring['end_time']):
                    clashes.append(
                        f"**{evt['day']}** — "
                        f"One-time '{evt['event']}' ({evt['start_time']}–{evt['end_time']}) "
                        f"clashes with recurring "
                        f"'{recurring['subject']}' ({recurring['start_time']}–{recurring['end_time']})"
                    )

    return clashes


def ui_events_tab():
    """UI for events and schedule tab"""

    st.header("Events & Recurring Schedules",
              help="Manage your compulsory one-time events or recurring schedules. "
                   "Add new events/schedules, view existing ones, and delete them as needed!")

    _render_add_event_form()

    st.divider()

    clashes = _get_clashes()
    if clashes:
        with st.expander(
            f"⚠️ {len(clashes)} scheduling clash{'es' if len(clashes) != 1 else ''} detected",
            expanded=True
        ):
            st.warning(
                "The following events overlap. Timetable will still be generated correctly,"
                "but you can't attend two events at once!"
            )
            for clash in clashes:
                st.markdown(f"- {clash}")

    _render_recurring_schedules()

    st.divider()

    _render_one_time_events()


def _render_add_event_form():
    """Add Event/Schedule expander form."""

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
            start_t = st.time_input("Start", key="event_start_time", help="Account for travel time as well!")
        with col2:
            end_t = st.time_input("End", key="event_end_time", help="Account for travel time as well!")

        if recurrence_type == "Weekly":
            selected_days = st.multiselect("Days", WEEKDAY_NAMES, key="event_days")
            event_date    = None

        elif recurrence_type == "Bi-weekly":
            selected_days = st.multiselect("Days", WEEKDAY_NAMES, key="event_days")
            event_date    = st.date_input(
                "Starting from",
                min_value=datetime.now().date(),
                key="event_date",
                help="The first week these events occur. They will then repeat every other week."
            )

        elif recurrence_type == "Monthly":
            selected_days = st.multiselect("Days", WEEKDAY_NAMES, key="event_days")
            event_date    = st.date_input(
                "Starting from",
                min_value=datetime.now().date(),
                key="event_date",
                help="The first month these events occur."
            )

        else:  # One-time Event
            selected_days = None
            event_date    = st.date_input(
                "Date",
                min_value=datetime.now().date(),
                key="event_date"
            )

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
                    result = NeroTimeLogic.add_recurring_event(
                        event_name,
                        start_t.strftime("%H:%M"),
                        end_t.strftime("%H:%M"),
                        recurrence_type.lower(),
                        selected_days,
                        event_date.isoformat() if event_date else None
                    )

                if result["success"]:
                    st.success("✓ Added")
                    st.rerun()
                else:
                    st.error(result["message"])
            else:
                st.error("Please enter an event name")


def _render_recurring_schedules():
    """Recurring schedules section."""

    st.markdown("### 📅 Recurring Schedules")
    school_data = NeroTimeLogic.get_school_schedule()
    schedule    = school_data['schedule']

    if schedule:
        for day in WEEKDAY_NAMES:
            if day not in schedule:
                continue
            events = schedule[day]
            count  = len(events)

            day_has_clash = any(
                _times_overlap(events[i]['start_time'], events[i]['end_time'],
                               events[j]['start_time'], events[j]['end_time'])
                for i in range(count) for j in range(i + 1, count)
            )
            label = f"{'⚠️ ' if day_has_clash else ''}{day} ({count} event{'s' if count != 1 else ''})"

            with st.expander(label):
                for idx, cls in enumerate(events):
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        recurrence_badge = cls.get('recurrence', 'weekly').title()
                        start_label      = cls.get('start_date', '')
                        caption          = f"{cls['start_time']} — {cls['end_time']}"
                        if start_label:
                            caption += f"  ·  from {start_label}"

                        event_clashes = any(
                            idx != k and _times_overlap(
                                cls['start_time'], cls['end_time'],
                                events[k]['start_time'], events[k]['end_time']
                            )
                            for k in range(count)
                        )
                        prefix = "⚠️ " if event_clashes else ""
                        st.write(f"{prefix}**{cls['subject']}** ({recurrence_badge})")
                        st.caption(caption)
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
    events      = events_data['events']

    if events:
        clashing_indices = set()
        for i in range(len(events)):
            for j in range(i + 1, len(events)):
                a, b = events[i], events[j]
                if a['day'] == b['day'] and _times_overlap(
                    a['start_time'], a['end_time'],
                    b['start_time'], b['end_time']
                ):
                    clashing_indices.add(i)
                    clashing_indices.add(j)

        for idx, evt in enumerate(events):
            clash_prefix = "⚠️ " if idx in clashing_indices else ""
            with st.expander(f"{idx+1}. {clash_prefix}{evt['event']} — {evt['day']}"):
                st.write(f"{evt['start_time']} — {evt['end_time']}")
                if idx in clashing_indices:
                    st.warning("This event clashes with another event on the same day.")
                if st.button("Delete", key=f"del_event_{idx}_{evt['event']}"):
                    result = NeroTimeLogic.delete_event(idx)
                    if result["success"]:
                        st.rerun()
    else:
        st.info("No one-time events")
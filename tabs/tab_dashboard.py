"""
NERO-Time - DASHBOARD / TIMETABLE TAB
"""
import streamlit as st
from datetime import datetime, timedelta
from nero_logic import NeroTimeLogic


def filter_events_by_period(month_days, filter_type):
    """Filter days based on weekly/monthly/yearly view."""
    today = datetime.now().date()

    if filter_type == 'weekly':
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        return [d for d in month_days if start_of_week <= d['date'].date() <= end_of_week]
    elif filter_type == 'monthly':
        return [d for d in month_days if d['date'].month == today.month and d['date'].year == today.year]
    else:  # yearly
        return [d for d in month_days if d['date'].year == today.year]


def ui_dashboard_tab():
    """Render the Dashboard tab content."""

    if 'event_filter' not in st.session_state:
        st.session_state.event_filter = 'weekly'

    dashboard_data = NeroTimeLogic.get_dashboard_data()

    # Month navigation
    col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])

    with col2:
        if st.button("◀ Prev", use_container_width=True, key="btn_prev_month"):
            NeroTimeLogic.navigate_month("prev")
            st.rerun()
    with col3:
        st.markdown(
            f"<div style='text-align:center; padding:8px; font-weight:600; font-size:18px;'>"
            f"{dashboard_data['month_name']} {dashboard_data['year']}</div>",
            unsafe_allow_html=True
        )
    with col4:
        if st.button("Next ▶", use_container_width=True, key="btn_next_month"):
            NeroTimeLogic.navigate_month("next")
            st.rerun()
    with col5:
        if st.button("Today", use_container_width=True, key="btn_today_month"):
            NeroTimeLogic.navigate_month("today")
            st.rerun()

    st.divider()

    # Timetable warnings
    if 'timetable_warnings' in st.session_state and st.session_state.timetable_warnings:
        errors = sum(1 for w in st.session_state.timetable_warnings if w.startswith('❌'))
        warnings_count = sum(1 for w in st.session_state.timetable_warnings if w.startswith('⚠️'))
        success_count = sum(1 for w in st.session_state.timetable_warnings if w.startswith('✓'))

        if errors > 0:
            header = f"⚠️ Timetable Warnings ({errors} error(s), {warnings_count} warning(s))"
            expanded = True
        elif warnings_count > 0:
            header = f"⚠️ Timetable Warnings ({warnings_count} warning(s))"
            expanded = True
        else:
            header = f"✓ Timetable Generation Info ({success_count} activity/activities)"
            expanded = False

        with st.expander(header, expanded=expanded):
            for warning in st.session_state.timetable_warnings:
                if warning.startswith('❌'):
                    st.error(warning)
                elif warning.startswith('⚠️'):
                    st.warning(warning)
                elif warning.startswith('✓'):
                    st.success(warning)
                else:
                    st.info(warning)
        st.divider()

    # Generate button
    if st.button("* GENERATE TIMETABLE *", type="primary", use_container_width=True, key="btn_generate_timetable"):
        if (st.session_state.list_of_activities
                or st.session_state.list_of_compulsory_events
                or st.session_state.school_schedule):
            with st.spinner("Generating your perfect schedule..."):
                result = NeroTimeLogic.generate_timetable()
            if result["success"]:
                st.success("✓ Timetable generated successfully!")
                st.rerun()
            else:
                st.error(result["message"])
        else:
            st.warning("⚠️ Please add activities, events, or school schedule first")

    st.divider()

    # Event filter buttons
    st.markdown("### 📅 Events")

    col_f1, col_f2, col_f3, col_f4 = st.columns([1, 1, 1, 3])

    with col_f1:
        if st.button(
            "📅 Weekly", use_container_width=True,
            type="primary" if st.session_state.event_filter == 'weekly' else "secondary",
            key="filter_weekly"
        ):
            st.session_state.event_filter = 'weekly'
            st.rerun()
    with col_f2:
        if st.button(
            "📆 Monthly", use_container_width=True,
            type="primary" if st.session_state.event_filter == 'monthly' else "secondary",
            key="filter_monthly"
        ):
            st.session_state.event_filter = 'monthly'
            st.rerun()
    with col_f3:
        if st.button(
            "🗓️ Yearly", use_container_width=True,
            type="primary" if st.session_state.event_filter == 'yearly' else "secondary",
            key="filter_yearly"
        ):
            st.session_state.event_filter = 'yearly'
            st.rerun()

    st.divider()

    # Timetable display — BREAK events are filtered out (silent gaps only)
    filtered_days = filter_events_by_period(dashboard_data['month_days'], st.session_state.event_filter)

    if dashboard_data['timetable'] and filtered_days:
        for day_info in filtered_days:
            day_display = day_info['display']
            date_obj = day_info['date']
            formatted_date = date_obj.strftime("%d %B %Y - %A")

            if day_display not in dashboard_data['timetable']:
                continue

            is_current_day = (day_display == dashboard_data['current_day'])

            # BREAK rows are never shown — they exist only to block the slot
            visible_events = [
                e for e in dashboard_data['timetable'][day_display]
                if e.get('type') != 'BREAK'
            ]

            if not visible_events:
                continue

            with st.expander(
                f"{'🟢 ' if is_current_day else ''}📅 {formatted_date}",
                expanded=is_current_day
            ):
                for event in visible_events:
                    _render_event_row(event, is_current_day, dashboard_data)
    else:
        st.info("No events for this period")


def _render_event_row(event, is_current_day, dashboard_data):
    """Dispatch to the correct renderer based on event type."""
    from Timetable_Generation import time_str_to_minutes

    is_current_slot = False
    is_finished = event.get('is_finished', False)

    if is_current_day and dashboard_data['current_time']:
        current_minutes = time_str_to_minutes(dashboard_data['current_time'])
        is_current_slot = (
            time_str_to_minutes(event['start']) <= current_minutes
            < time_str_to_minutes(event['end'])
        )

    event_type = event["type"]

    if event_type == "ACTIVITY":
        _render_activity_event(event, is_current_slot, is_finished)
    elif event_type == "SCHOOL":
        _render_school_event(event, is_current_slot)
    elif event_type == "COMPULSORY":
        _render_compulsory_event(event, is_current_slot)
    # BREAK is intentionally omitted


def _render_activity_event(event, is_current_slot, is_finished):
    """Render an ACTIVITY timetable row."""
    name_parts = event['name'].split(' (Session')
    activity_name = name_parts[0]
    session_part = name_parts[1].rstrip(')') if len(name_parts) > 1 else "1"

    is_completed = event.get('is_completed', False)
    is_user_edited = event.get('is_user_edited', False)
    is_skipped = event.get('is_skipped', False) and is_finished

    css_class = "timetable-row activity"
    if is_skipped:
        css_class += " skipped"
    elif is_finished and not is_completed:
        css_class += " finished"

    status_icon = "✅" if is_completed else "❌" if is_skipped else "⚫"

    badges = ""
    if is_current_slot:
        badges += '<span class="happening-now">● LIVE NOW</span> '
    if is_finished and not is_completed and not is_skipped:
        badges += '<span class="finished-badge">⏰ FINISHED</span> '
    if is_user_edited:
        badges += '<span class="user-edited-badge">EDITED</span> '

    progress_html = ""
    activity_obj = next(
        (a for a in st.session_state.list_of_activities if a['activity'] == activity_name), None
    )
    if activity_obj:
        sessions = activity_obj.get('sessions', [])
        completed_hours = sum(s.get('duration_hours', 0) for s in sessions if s.get('is_completed', False))
        total_hours = activity_obj['timing']
        progress_html = f'📊 {completed_hours:.1f}h / {total_hours:.1f}h completed'

    html = f"""
    <div class="{css_class}">
        <div class="event-info">
            <div style="font-size:22px; margin-top:2px;">{status_icon}</div>
            <div class="event-text-stack">
                <div class="event-title">
                    {badges}<strong>{activity_name}</strong>
                    <span style="opacity:0.6; font-size:0.8em;">Session {session_part}</span>
                </div>
                <div class="event-details">{progress_html}</div>
            </div>
        </div>
        <div class="event-right-section">
            <div class="event-time">{event["start"]} — {event["end"]}</div>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def _render_school_event(event, is_current_slot):
    """Render a SCHOOL timetable row."""
    badge_html = '<span class="happening-now">● LIVE NOW</span> ' if is_current_slot else ""

    html = f"""
    <div class="timetable-row school">
        <div class="event-info">
            <div style="font-size:22px; margin-top:2px;">🏫</div>
            <div class="event-text-stack">
                <div class="event-title">{badge_html}<strong>{event["name"]}</strong></div>
                <div class="event-details">Recurring schedule</div>
            </div>
        </div>
        <div class="event-right-section">
            <div class="event-time">{event["start"]} — {event["end"]}</div>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def _render_compulsory_event(event, is_current_slot):
    """Render a COMPULSORY timetable row."""
    badge_html = '<span class="happening-now">● LIVE NOW</span> ' if is_current_slot else ""

    html = f"""
    <div class="timetable-row compulsory">
        <div class="event-info">
            <div style="font-size:22px; margin-top:2px;">🔴</div>
            <div class="event-text-stack">
                <div class="event-title">{badge_html}<strong>{event["name"]}</strong></div>
                <div class="event-details">Compulsory Event</div>
            </div>
        </div>
        <div class="event-right-section">
            <div class="event-time">{event["start"]} — {event["end"]}</div>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)
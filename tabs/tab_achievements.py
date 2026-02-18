"""
NERO-Time - ACHIEVEMENTS TAB (REFACTORED)
"""
import streamlit as st
from datetime import datetime


def ui_achievements_tab(total_hours_completed: float, total_activities: int):
    """Render the Achievements tab content."""
    Badge = 0
    completed_activities = st.session_state.get('completed_activities', [])
    total_completed_activities = len(completed_activities)

    st.header("Achievements")

    # ── Completed Activities ───────────────────────────────────────────────────
    if completed_activities:
        st.markdown("### 🎓 Completed Activities")
        for record in completed_activities:
            completed_at = record.get('completed_at', '')
            try:
                completed_dt = datetime.fromisoformat(completed_at)
                date_str = completed_dt.strftime("%d %b %Y, %H:%M")
            except Exception:
                date_str = completed_at

            with st.expander(f"✅ {record['activity']} — {date_str}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Total Hours:** {record['timing']:.1f}h")
                    st.write(f"**Sessions:** {record.get('num_sessions', '—')}")
                with col2:
                    st.write(f"**Completed:** {date_str}")
                    st.write(f"**Mode:** {'🤖 Auto' if record.get('session_mode') == 'automatic' else '✋ Manual'}")

        st.divider()

    # ── Badge grid ─────────────────────────────────────────────────────────────
    col1, col2, col3 = st.columns(3)

    with col1:
        Badge = _render_badge(
            condition=total_hours_completed >= 0,
            icon="✅",
            unlock_label="UNLOCKED 🔓",
            locked_msg=f"Please obtain {int(abs(0 - total_hours_completed))}h to obtain this badge.",
            description=f"You Just started. Achieve: {total_hours_completed:.1f}/0 hours to get this badge",
            badge_count=Badge
        )

        Badge = _render_badge(
            condition=total_activities >= 5,
            icon="💼",
            unlock_label="UNLOCKED 🔓",
            locked_msg=f"Please obtain {int(5 - total_activities)} more activities to obtain this badge.",
            description=f"My first assignments! Achieve: {total_activities}/5 activities to get this badge",
            badge_count=Badge
        )

        Badge = _render_badge(
            condition=Badge >= 3,
            icon="🏆",
            unlock_label="UNLOCKED 🔓",
            locked_msg=f"Please obtain {int(3 - Badge)} more badges to obtain this badge.",
            description=f"My first achievements! Achieve: {Badge}/3 Badges to get this badge",
            badge_count=Badge
        )

    with col2:
        Badge = _render_badge(
            condition=total_hours_completed >= 24,
            icon="📅",
            unlock_label="UNLOCKED 🔓",
            locked_msg=f"Please obtain {int(max(0, 24 - total_hours_completed))}h to obtain this badge.",
            description=f"A day of work! Achieve: {total_hours_completed:.1f}/24 hours to get this badge",
            badge_count=Badge
        )

        Badge = _render_badge(
            condition=total_activities >= 20,
            icon="💪",
            unlock_label="UNLOCKED 🔓",
            locked_msg=f"Please obtain {int(20 - total_activities)} more activities to obtain this badge.",
            description=f"Schedule getting tough! Achieve: {total_activities}/20 activities to get this badge",
            badge_count=Badge
        )

        Badge = _render_badge(
            condition=Badge >= 5,
            icon="🎖️",
            unlock_label="UNLOCKED 🔓",
            locked_msg=f"Please obtain {int(5 - Badge)} more badges to obtain this badge.",
            description=f"Wow! Accomplished! Achieve: {Badge}/5 Badges to get this badge",
            badge_count=Badge
        )

    with col3:
        Badge = _render_badge(
            condition=total_hours_completed >= 168,
            icon="👍",
            unlock_label="UNLOCKED 🔓",
            locked_msg=f"Please obtain {int(max(0, 168 - total_hours_completed))}h to obtain this badge.",
            description=f"Commitment! Achieve: {total_hours_completed:.1f}/168 hours to get this badge",
            badge_count=Badge
        )

        Badge = _render_badge(
            condition=total_activities >= 50,
            icon="😓",
            unlock_label="UNLOCKED 🔓",
            locked_msg=f"Please obtain {int(50 - total_activities)} more activities to obtain this badge.",
            description=f"Can you manage? Achieve: {total_activities}/50 activities to get this badge",
            badge_count=Badge
        )

        # Completion-based badge — unlocked by finishing activities
        Badge = _render_badge(
            condition=total_completed_activities >= 1,
            icon="🎓",
            unlock_label="UNLOCKED 🔓",
            locked_msg="Complete your first activity to obtain this badge.",
            description=f"Graduate! Completed: {total_completed_activities}/1 activity",
            badge_count=Badge
        )

        _render_badge(
            condition=Badge >= 8,
            icon="🥳",
            unlock_label="UNLOCKED 🔓",
            locked_msg=f"Please obtain {int(8 - Badge)} more badges to obtain this badge.",
            description=f"Collector, I see! Achieve: {Badge}/8 Badges to get this badge",
            badge_count=Badge
        )


def _render_badge(condition: bool, icon: str, unlock_label: str,
                  locked_msg: str, description: str, badge_count: int) -> int:
    if condition:
        st.markdown(
            f"<h1 style='text-align: center; font-size: 10rem; color: #FFFFFF;'>{icon}",
            unsafe_allow_html=True
        )
        st.markdown(
            f"<h1 style='text-align: center; margin-bottom: 1rem; font-size: 1rem; color: #00FF00;'> {unlock_label}",
            unsafe_allow_html=True
        )
        badge_count += 1
    else:
        st.markdown(
            f"<h1 style='text-align: center; font-size: 10rem; color: #000000;'>❌",
            unsafe_allow_html=True
        )
        st.markdown(
            f"<h1 style='text-align: center; margin-bottom: 1rem; font-size: 1rem; color: #FF0000;'>{locked_msg}</h1>",
            unsafe_allow_html=True
        )

    st.write(description)
    return badge_count
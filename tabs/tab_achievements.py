"""
NERO-Time - ACHIEVEMENTS TAB
"""
import streamlit as st


def ui_achievements_tab(total_hours_completed: float, total_activities: int):
    """Render the Achievements tab content.

    INPUTS:
        total_hours_completed: Total hours completed across all activities.
        total_activities: Total number of activities.
    """
    Badge = 0
    st.header("Achievements")

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
            locked_msg=f"Please obtain {int(5 - total_activities)} more activites to obtain this badge.",
            description=f"My first assignments! Achieve: {total_activities}/5 activites to get this badge",
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
            locked_msg=f"Please obtain {int(20 - total_activities)} more activites to obtain this badge.",
            description=f"Schedule getting tough! Achieve: {total_activities}/20 activites to get this badge",
            badge_count=Badge
        )

        Badge = _render_badge(
            condition=Badge >= 5,
            icon="🎖️",
            unlock_label="UNLOCKED 🔓",
            locked_msg=f"Please obtain {int(5 - Badge)} more badges to obtain this badge.",
            description=f"Wow! Acomplished! Achieve: {Badge}/5 Badges to get this badge",
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
            locked_msg=f"Please obtain {int(50 - total_activities)} more activites to obtain this badge.",
            description=f"Can you manage? Achieve: {total_activities}/50 activites to get this badge",
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
    """Render a single achievement badge and return updated badge count.

    Args:
        condition: Whether the badge has been unlocked.
        icon: Emoji icon to display.
        unlock_label: Label shown when unlocked.
        locked_msg: Message shown when locked.
        description: Progress description shown below the badge.
        badge_count: Current badge count before this badge.

    Returns:
        Updated badge count (incremented by 1 if condition is True).
    """
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
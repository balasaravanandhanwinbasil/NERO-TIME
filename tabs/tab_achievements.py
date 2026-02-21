"""
NERO-Time - ACHIEVEMENTS TAB
"""
import streamlit as st


def ui_achievements_tab(total_hours_completed: float, total_activities: int):
    """UI for achievements tab

    INPUTS:
        total_hours_completed: Total hours completed across all activities.
        total_activities: Total number of activities.
    """
    Badge = 0
    st.header("Achievements")

    col1, col2, col3 = st.columns(3)

    with col1:
        Badge = badge(
            condition=total_hours_completed >= 1,
            icon="⏰",
            unlock_label="Your quest has just begun.",
            locked_msg=f"Complete {1}h of work to obtain this badge.",
            description=f"{min(total_hours_completed, 1):.1f}/1.0 hours completed",
            badge_count=Badge
        )

        Badge = badge(
            condition=total_activities >= 5,
            icon="💼",
            unlock_label="Pawn of Assignments",
            locked_msg=f"To begin timing, one must first take on the task.",
            description=f"{min(total_activities, 5)}/5 activities",
            badge_count=Badge
        )

        Badge = badge(
            condition=Badge >= 3,
            icon="🏆",
            unlock_label="Badge Collector |",
            locked_msg=f"To achieve greater heights, one must start from someething smaller.",
            description=f"{min(Badge, 3)}/3 Badges",
            badge_count=Badge
        )

    with col2:
        Badge = badge(
            condition=total_hours_completed >= 24,
            icon="📅",
            unlock_label="Commitment",
            locked_msg=f"A full day of work.",
            description=f"{min(total_hours_completed, 24):.1f}/24 hours worth of activities",
            badge_count=Badge
        )

        Badge = badge(
            condition=total_activities >= 20,
            icon="💪",
            unlock_label="Assignment Knight",
            locked_msg=f"Are you busy because you have a lot of assignments, or do you have a lot of assignments because you are busy?",
            description=f"{min(total_activities, 20)}/20 activities",
            badge_count=Badge
        )

        Badge = badge(
            condition=Badge >= 5,
            icon="🎖️",
            unlock_label="Badge King",
            locked_msg=f"To achieve the greatest heights, one must start from something medium.",
            description=f"{min(Badge, 5)}/5 Badges",
            badge_count=Badge
        )

    with col3:
        Badge = badge(
            condition=total_hours_completed >= 168,
            icon="👍",
            unlock_label="The Completionist",
            locked_msg=f"A full week of work.",
            description=f"{min(total_hours_completed, 168):.1f}/168 hours",
            badge_count=Badge
        )

        Badge = badge(
            condition=total_activities >= 50,
            icon="😓",
            unlock_label="The Overachiever",
            locked_msg=f"The achiever of all time",
            description=f"{min(total_activities, 50)}/50 activities",
            badge_count=Badge
        )

        badge(
            condition=Badge >= 8,
            icon="🥳",
            unlock_label="Badge Supreme King",
            locked_msg=f"To achieve the top, one must finish them all.",
            description=f"{min(Badge, 8)}/8 Badges",
            badge_count=Badge
        )


def badge(condition: bool, icon: str, unlock_label: str,
                  locked_msg: str, description: str, badge_count: int) -> int:
    """
    NOTE: This also returns the badge count if condition is fulfulled
    """

    icon = icon if condition else "❌"
    color = "#00FF00" if condition else "#FF0000"

    unlock_label = unlock_label if condition else locked_msg

    st.markdown(
            f"<h1 style='text-align: center; font-size: 10rem; color: {color};'>{icon}",
            unsafe_allow_html=True
    )
    st.markdown(
            f"<h1 style='text-align: center; margin-bottom: 1rem; font-size: 1rem; color: {color};'>{unlock_label}",
            unsafe_allow_html=True
    )

    if condition:
        badge_count += 1


    st.write(f"Complete {description} to get this badge.")

    return badge_count
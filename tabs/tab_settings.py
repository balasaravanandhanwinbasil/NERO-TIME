"""
NERO-Time - SETTINGS TAB
"""
import streamlit as st
from datetime import time as dtime
from nero_logic import NeroTimeLogic


# ===== Defaults (must be same as timetable generation) =====

_DEFAULT_WORK_START = 7 * 60        # 07:00 in minutes form
_DEFAULT_WORK_END   = 23 * 60 + 30  # 23:30 in minutes form


def ui_settings_tab():
    """Render the Settings tab content."""
    st.header("Settings")

    _render_account_info()
    st.divider()

    _render_schedule_hours()
    st.divider()

    _render_change_password()
    st.divider()

    _render_data_management()


# === ACOUNT INFO === 

def _render_account_info():
    st.markdown("### 👤 Account Information")
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Username:** {st.session_state.get('username', 'N/A')}")
        st.write(f"**User ID:** {st.session_state.user_id[:8]}...")
    with col2:
        email = st.session_state.get('user_email', '')
        st.write(f"**Email:** {email if email else 'Not set'}")


# === Schedule Hours + Sleep Warnings ===

def _render_schedule_hours():
    """Editable wake/sleep times with real-time sleep-health warnings."""
    st.markdown("### 🕐 Daily Schedule Hours")
    st.caption(
        "These control the window in which the timetable generator can place sessions. "
        "Changes take effect on the next timetable generation."
    )

    # Read current values from session state
    current_start = st.session_state.get('work_start_minutes', _DEFAULT_WORK_START)
    current_end   = st.session_state.get('work_end_minutes',   _DEFAULT_WORK_END)

    start_h, start_m = divmod(current_start, 60) # use divmod to convert minutes to hours and minuts
    end_h,   end_m   = divmod(current_end,   60)

    col1, col2 = st.columns(2)
    with col1:
        wake_time = st.time_input(
            "⏰ Wake-up / Day Start",
            value=dtime(start_h, start_m),
            step=900,          # 15-minute steps
            key="setting_wake_time",
            help="Earliest time the generator will schedule anything"
        )
    with col2:
        sleep_time = st.time_input(
            "🌙 Bedtime / Day End",
            value=dtime(end_h, end_m),
            step=900,
            key="setting_sleep_time",
            help="Latest time a session may end."
        )

    wake_minutes  = wake_time.hour  * 60 + wake_time.minute
    sleep_minutes = sleep_time.hour * 60 + sleep_time.minute

    # === WARNINGS ===
    available_hours = (sleep_minutes - wake_minutes) / 60 if sleep_minutes > wake_minutes else 0
    sleep_hours     = 24 - available_hours  # sleep duration

    warnings_shown = False

    if sleep_time.hour > 23 or (sleep_time.hour == 23 and sleep_time.minute > 30):
        st.warning(
            "⚠️ **Late bedtime detected** — your day ends after 23:30. "
            "Working this late may hurt your focus and sleep quality."
        )
        warnings_shown = True

    if wake_time.hour >= 10:
        st.warning(
            f"⚠️ **Late wake-up detected** — starting at {wake_time.strftime('%H:%M')} "
            "This may impact your day's productivity. Set it atleast before 10:00 for best results!"
        )
        warnings_shown = True

    if sleep_hours < 8 and available_hours > 0:
        st.error(
            f"❌ **Insufficient sleep** — Y our schedule implies only "
            f"**{sleep_hours:.1f} hours** of sleep "
            f"({wake_time.strftime('%H:%M')} wake · {sleep_time.strftime('%H:%M')} bed). "
            "Aim for at least 8 hours of sleep for a healthy lifestyle."
        )
        warnings_shown = True
    elif sleep_hours >= 8 and not warnings_shown:
        st.success(
            f"✓ Implied sleep: **{sleep_hours:.1f}h** — looks healthy! "
            f"({available_hours:.1f}h productive window)"
        )

    if sleep_minutes <= wake_minutes:
        st.error("❌ Bedtime must be later than wake-up time.")
        return 

    # === SAVE BUTTON ===
    if st.button("💾 Save Schedule Hours", type="primary", key="btn_save_hours"):
        st.session_state.work_start_minutes = wake_minutes
        st.session_state.work_end_minutes   = sleep_minutes

        # send to firebase
        if st.session_state.user_id:
            from Firebase_Function import save_to_firebase
            save_to_firebase(st.session_state.user_id, 'work_start_minutes', wake_minutes)
            save_to_firebase(st.session_state.user_id, 'work_end_minutes',   sleep_minutes)

        st.success(
            f"✓ Saved — timetable will run "
            f"{wake_time.strftime('%H:%M')} → {sleep_time.strftime('%H:%M')} "
            f"({available_hours:.1f}h window)"
        )
        st.caption("Regenerate your timetable for changes to apply.")


# === CHANGE PASSWORD ===

def _render_change_password():
    with st.expander("🔐 Change your password", expanded=False):
        with st.form(key="change_password_form"):
            old_password         = st.text_input("Current Password", type="password", key="old_password")
            new_password         = st.text_input("New Password", type="password", key="new_password",
                                                  help="Minimum 6 characters")
            confirm_new_password = st.text_input("Confirm New Password", type="password", key="confirm_new_password")

            col1, col2 = st.columns(2)
            with col1:
                submit = st.form_submit_button("Change Password", type="primary", use_container_width=True)
            with col2:
                st.form_submit_button("Cancel", use_container_width=True)

            if submit:
                if not old_password or not new_password or not confirm_new_password:
                    st.error("All fields are required")
                elif new_password != confirm_new_password:
                    st.error("New passwords do not match")
                elif len(new_password) < 6:
                    st.warning("Password must be at least 6 characters")
                else:
                    with st.spinner("Changing password..."):
                        from Firebase_Function import change_password
                        result = change_password(st.session_state.user_id, old_password, new_password)
                    if result["success"]:
                        st.success("✓ " + result["message"])
                    else:
                        st.error("✗ " + result["message"])


# ===== Data management =====

def _render_data_management():
    st.markdown("### 🗂️ Data Management")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Clear All Data", use_container_width=True, key="btn_clear_data"):
            result = NeroTimeLogic.clear_all_data()
            if result["success"]:
                st.warning("⚠️ All data cleared")
                st.rerun()
    with col2:
        if st.button("Logout", type="primary", use_container_width=True, key="btn_logout"):
            st.session_state.user_id    = None
            st.session_state.username   = None
            st.session_state.user_email = None
            st.session_state.data_loaded = False
            st.rerun()
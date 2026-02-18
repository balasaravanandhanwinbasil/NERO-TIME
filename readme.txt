hi please edit this if changes are made to any of the variables.

# st.session_state.user_id: str | None
Firebase ID (based on username)
Used for FireAuth

# st.session_state.username: str | None
Username of user (without encryption)

# st.session_state.user_email: str | None
optional, doesn't really do anything FOR NOW

# st.session_state.data_loaded: bool
This one ensures that firebase loading in only happens ONCE. Afterwards, it will not reload from firebase everytime.

# st.session_state.login_mode: str
Tracks which tab was last active on the login screen.
states: 'login' or 'register'


# === NAVIGATION IN DASHBOARD ===


# st.session_state.current_month: int
The month (1–12) of the calendar page currently filtered on the main dashboard
Changes when the user clicks the Prev, Next, or Today buttons
Example: 2  

# st.session_state.current_year: int
The year of the calendar page currently shown on the Dashboard tab.
Increments/decrements when navigating past December or January.
Example: 2026

# st.session_state.event_filter: str
Filters the amount of days to display on the dashboard
One of: 'weekly' | 'monthly' | 'yearly'
week is Monday - Sunday btw


# ============================================================================== TIMETABLE (very important) ==============================================================================


# st.session_state.timetable: dictionary of [str, list[dict]]

=== LAYOUT (for COMPULSORY events only) ===
{
  "start": str
       The slot start time in "HH:MM" 24-hour format in a STRING.
       NEEDS to be a multiple of 15 minutes.
       e.g. "23:45" # 11.45pm

   "end": str
       The slot end time in "HH:MM" 24-hour format also in a string.
       Derived from start + duration. Capped at the end time. Must be after start time, on the same day.

   "name": str
       The display name. For SCHOOL: the subject name. For COMPULSORY: the event name.

   "type": str
       "SCHOOL" | "COMPULSORY"
       (ACTIVITY rows are built dynamically — see st.session_state.sessions)

   "is_completed": bool   ← always False for fixed events
   "is_skipped":   bool   ← always False for fixed events
   "is_finished":  bool   ← always False for fixed events
}

=== ACTIVITY ===

{
   "start":          str   — session['scheduled_time']
   "end":            str   — derived from start + duration_minutes
   "name":           str   — "{activity_name} (Session {n})"
   "type":           "ACTIVITY"
   "activity_name":  str   — ONLY the activity name (no session suffix)
   "session_num":    int   — session number
   "session_id":     str   — cross-reference key into st.session_state.sessions
   "is_completed":   bool  — from session dict
   "is_skipped":     bool  — from session dict
   "is_finished":    bool  — derived live (end time <= now)
   "is_user_edited": bool  — from session dict
}

# st.session_state.timetable_warnings: list of str ["", ""]
This shows any warnings if not all activities can be placed.
Displayed on the Dashboard tab.
USE EMOJIS BEFORE LIKE EVERYTHING
   "✓ ..."  — success (ALL sessions for it have been placed.)
   "⚠️ ..." — warning (e.g. could not fit all required hours before deadline)
   "❌ ..."  — error   (e.g. no free days available before an activity's deadline)



# ============================================================================== SESSIONS ==============================================================================

To get finished sessions:     NeroTimeLogic.get_finished_sessions()
To get pending verification:  NeroTimeLogic.get_pending_verification()
To get reviewed sessions:     NeroTimeLogic.get_reviewed_sessions()
All three are just filters on this one, of course.

Sessions are just for each activity..

st.session_state.sessions = dict[dict]

session_id: {session dict}
\
=== Session dict ===
{
   "session_id": str
        Format: "{activity_name_underscored}_session_{n}"
       e.g. "Math_Revision_session_1"
       Used as the dict key AND stored inside the dict for convenience.

   "session_num": int
       The session number for this activity.
       e.g. 1

   "activity_name": str
       The display name of the parent activity (no session suffix).
       Used to look up the activity in list_of_activities.
       e.g. "Math Revision"

   "scheduled_day": str | None
       The day-display key this session is placed on.
       Format: "Weekday DD/MM"  e.g. "Monday 17/02"
       None if the session hasn't been scheduled yet (manual mode, pre-generation).

   "scheduled_date": str | None
       Full ISO date string for the scheduled day.
       Used by check_expired_sessions() to compare against today's date.
       e.g. "2026-02-17"
       None if not yet scheduled.

   "scheduled_time": str | None
       "HH:MM" start time of this session.
       e.g. "14:00"
       None if not yet scheduled.

   "duration_minutes": int
       Length of the session in minutes. Always a multiple of 15.
       e.g. 60

   "duration_hours": float
       duration_minutes / 60, pre-computed for convenience.
       Used when summing completed hours for progress display.
       e.g. 1.0

   "is_completed": bool
       True when the user verified this session as done.
       Completed sessions survive timetable regeneration intact.

   "is_skipped": bool
       True when the user marked this session as not done.
       Skipped sessions are discarded on the next timetable regeneration.

   "is_finished": bool
       True when the real-world clock is past this session's end time.
       Set by check_expired_sessions(). A finished session awaits verification.
       Also derived live in get_timetable_view() for display purposes.

   "is_user_edited": bool
       True when the user has manually edited this session's time/date/duration.
       Causes the "EDITED" badge to appear in the UI.
       The timetable generator leaves user-edited sessions untouched.

   "is_manual": bool
       True for sessions created by the user in manual mode (not by the generator).

   === FOR MANUAL MODE ONLY ===
   "day_of_week": str | None
       Optional scheduling preference provided by the user when adding a manual
       session (e.g. "Tuesday"). The generator attempts to honour this but will
       fall back to other days if no slot is available.
       None if the user selected "Any".
}


# ============================================================================== ACTIVITIES ==============================================================================


# st.session_state.list_of_activities: list of dict -> [{}, {}]

The master list of all user-created activities. From the activities_tab.
Sessions are stored in st.session_state.sessions and filtered by activity_name.

For each activity dict...
{
   "activity": str
       The display name for the activity.
       e.g. "Math Revision"

   "priority": int
       HARDCODED to 3 right now for all activities.
       Can go from (1-5). For future development.

   "deadline": int
       Days remaining from today until this activity must be completed.
       Calculated ONCE when the activity is added.
       Used to determine the last possible day for timetable generation.

   "timing": float
       Total number of hours the activity requires to complete.
       The timetable generator fills sessions until this many hours are covered.
       e.g. 3.0

   "min_session_minutes": int
       Minimum length (in minutes) of a single scheduled session.
       Always a multiple of 15.
       e.g. 30

   "max_session_minutes": int
       Maximum length (in minutes) of a single scheduled session.
       Always a multiple of 15.
       e.g. 120

   "allowed_days": list of str [str]
       Days where the user wants to do the activity.
       The generator skips days not in this list.
       e.g. ["Monday", "Wednesday", "Friday"]

   "session_mode": str
       Controls how sessions are created for this activity by the generator
       "automatic" — timetable generator will CREATE and place sessions.
       "manual"    — user will CREATE sessions individually via the Activities tab;
                     the generator will then place them into free slots.

   "num_sessions": int
       Total number of sessions (completed + pending) after the last generation.
       Updated by generate_timetable_with_sessions().
       e.g. 4
}

To get sessions for an activity, filter st.session_state.sessions:
    [s for s in st.session_state.sessions.values() if s['activity_name'] == name]


# ============================================================================== EVENTS ==============================================================================

# st.session_state.list_of_compulsory_events: list[dict]
Fixed one-time/weekly/bi-weekly/monthly events that block out timetable slots.

=== Event dict ===
{
   "event": str
       The display name for this event.
       Shown directly on the timetable row.
       e.g. "Doctor Appointment"

   "start_time": str
       "HH:MM" start time.
       e.g. "10:00"

   "end_time": str
       "HH:MM" end time. Must be after start time.
       e.g. "11:00"

   "day": str
       Day-display key matching a timetable key.
       Format: "Weekday DD/MM"  e.g. "Wednesday 25/02"

   "date": str
       ISO datetime string for the event date (time component is midnight).
       Used to check whether the event is in the future before placing it.
       e.g. "2026-02-25T00:00:00"

   "recurrence": str   ← monthly recurring events only
       Always "monthly" for events added via add_recurring_event().
       Absent on one-time events added via add_event().
}


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


# st.session_state.timetable: dict[str, list[dict]]
This is basically the timetable that gets displayed.
"Weekday DD/MM" (e.g. "Monday 17/02"). Values are lists of event dicts
Will get sorted by start time.
Re-generated from scratch each time the user clicks GENERATE TIMETABLE,
EXCEPT for already-completed sessions which stay the same.

=== LAYOUT ===
{
  "start": str
       The slot start time in "HH:MM" 24-hour format in a STRING.
       NEEDS to be a multiple of 15 minutes.
       e.g. "23:45" # 11.45pm

   "end": str
       The slot end time in "HH:MM" 24-hour format also in a string.
       Derived from start + duration. Capped at the end time. Must be after start time, on the same day.
       e.g. "03:45" # 3.45am

   "name": str
       There are four different categories for this to be in, depending on the type. This is the NAME of the activity that gets displayed.
         ACTIVITY   -> "{activity_name} (Session {n})"  e.g. "Math (Session 2)"
         COMPULSORY -> The event name from list_of_compulsory_events  e.g. "School"

   "type": str
       Determine what TYPE it is and the UI associated with it.
       e.g. "ACTIVITY" | "SCHOOL" | "COMPULSORY" 

   "is_completed": bool
       True when the user has explicitly verified this session as DONE. Else, False. 
       USE verify_finished_session() or verify_session() TO DO THIS.
       Completed sessions are not changed across timetable regenerations
       A finished COMPLETED session shows the "✅ COMPLETED"

   "is_skipped": bool
       True when the user explicitly marked this session as NOT done. Else, false.
       Skipped sessions are regenerated on the next timetable regeneration
       A finished SKIPPED session shows the "❌ SKIPPED"

   "is_finished": bool
       True when the current time is past this slots end time.
       USE check_expired_sessions() and _is_event_finished() for this. 
       A finished NON-COMPLETED NON-SKIPPED session shows the "⏰ FINISHED" badge in the UI.

   == FOR ACTIVITY ONLY, use these for all the activity related stuff NOT the stuff above pls ==

   "activity_name": str
       ONLY the activity name (no session).
       Used to look up the activity in list_of_activities.
       e.g. "Computing PT" NOT "Computing PT (Session 1)

   "session_num": int
       ONLY the session number
       e.g. 2

   "session_id": str
       Globally unique identifier for this session.
       Format: "{activity_name_underscored}_session_{n}"
       e.g. "Math_Revision_session_2"
       Used to cross-reference the session across timetable, activities, and
       finished_sessions without relying on positional index.

   "is_user_edited": bool
       Causes the "EDITED" badge to appear in the UI.
       This session usually won't be affected by the timetable generator and would leave it untouched.

   "can_verify": bool
       USE get_dashboard_data() / _can_verify_event() to get this
       True when the slot's scheduled time has passed AND the session has not yet been verified (neither completed nor skipped).
       This is to make the UI elements for verification show up.
 }

# st.session_state.timetable_warnings: list of str ["", ""]
This shows any warnings if not all activities can be placed.
Displayed on the Dashboard tab.
USE EMOJIS BEFORE LIKE EVERYTHIGN
   "✅ ..."  — success (ALL sessions for it have been placed.)
   "⚠️ ..." — warning (e.g. could not fit all required hours before deadline)
   "❌ ..."  — error   (e.g. no free days available before an activity's deadline)



# ============================================================================== ACTIVITIES ==============================================================================


# st.session_state.list_of_activities: list of dict [{}, {}]
The master list of all user-created activities. From the activities_tab.

For each activity dict...
{
   "activity": str
       The display name for the activity
       The one given by the user
       e.g. "Math Revision"

   "priority": int
       HARDCODED to 3 right now for all activities
       Can go from (1-5) 
       For future development.

   "deadline": int
       Days remaining from today until this activity must be completed.
       Calculated ONCE.
       Used to determine last possible day for an activity for timetable generation.

   "timing": float
       Total number of hours the activity requires to complete. 
       The timetable generator fills sessions until this many hours are covered.
       e.g. 3.0

   "min_session_minutes": int
       Minimum length (in minutes) of a single scheduled session.
       Always a multiple of 15. The generator will not create sessions shorter
       than this unless fewer minutes remain overall.
       e.g. 30

   "max_session_minutes": int
       Maximum length (in minutes) of a single scheduled session.
       Always a multiple of 15. The generator caps each session at this length. Unless it cannot fit everything.
       e.g. 120

   "allowed_days": list of str [str]
       Days were the user wants to do the activity, from all the days in one week.
       The generator skips days not in this list when looking for free slots.
       e.g. ["Monday", "Wednesday", "Friday"]

   "session_mode": str
      Controls how sessions are created for this activity. (used in activity_tab)
       "automatic" — timetable generator will CREATE and place sessions.
       "manual"    — user will CREATE sessions individually via the Activities tab and timetable will place afterwards.

   "num_sessions": int
       Total number of sessions (completed + pending) after the last generation.
       Set by generate_timetable_with_sessions() after placing all sessions.
       e.g. 4

   "sessions": list[dict]
       The individual work blocks that make up this activity.
       is below for each one
 }

 === Session ===
 {
   "session_id": str
       Format: "{activity_name_spaces_replaced_with_underscores}_session_{n}"
       e.g. "Math_Revision_session_1"

   "session_num": int
       Matches session_num on the corresponding timetable event dict.
       e.g. 1

   "scheduled_day": str
       The day-display key this session is placed on.
       Format: "Weekday DD/MM"  e.g. "Monday 17/02"
       Matches a key in st.session_state.timetable.

   "scheduled_date": str
       Full ISO date string for the scheduled day.
       Used by check_expired_sessions() to compare against today's date.
       e.g. "2026-02-17"

   "scheduled_time": str
       "HH:MM" start time of this session.
        e.g. "14:00"

   "duration_minutes": int
       Length of the session in minutes. Always a multiple of 15.
       e.g. 60

   "duration_hours": float
       duration_minutes / 60, pre-computed and stored for convenience.
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

   === FOR MANUAL MODE ===
  "day_of_week": str | None
       Optional scheduling preference provided by the user when adding a manual
       session (e.g. "Tuesday"). The generator attempts to use this but will
       use other days if no slot is available on the preferred day.
       None if the user selected "Any".
 }


============================================================================== EVENTS ==============================================================================

st.session_state.list_of_compulsory_events: list[dict]
Fixed one-time/weekly/bi-weekly/monthly events that block out timetable slots

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
       "HH:MM" end time. must be after start time.
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


# st.session_state.past_incomplete_sessions: dict[str, list[dict]]
Sessions that were scheduled in the past but have no completion record.
Populated during timetable generation by check_past_activities().
Keys are activity names; values are lists of session dicts using the same
shape as the session dicts inside list_of_activities.
#Shown as warnings in the timetable generation expander.
Example: { "Math Revision": [ { "session_id": "...", ... } ] }

st.session_state.activity_progress: any
# Loaded from Firebase under 'activity_progress'.
# Legacy field from an earlier version of the app where progress was stored
# separately. Progress is now derived live by summing duration_hours across
# completed sessions in list_of_activities, so this field is unused.

st.session_state.session_completion: any
# Loaded from Firebase under 'session_completion'.
# Legacy field from an earlier version where completion state was stored in a
# separate collection. Completion is now stored directly on each session dict
# (is_completed / is_skipped) inside list_of_activities, so this field is unused.

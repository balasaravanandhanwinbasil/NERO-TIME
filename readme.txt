This code is to help understand how each of the global variables are formatted.


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


# ============================================================================== TIMETABLE ==============================================================================


# st.session_state.timetable: dict[str, list[dict]]
This is basically the timetable that gets displayed.
"Weekday DD/MM" (e.g. "Monday 17/02"). Values are lists of event dicts
Will get sorted by start time.
Re-generated from scratch each time the user clicks GENERATE TIMETABLE,
EXCEPT for already-completed sessions which stay the same.

# ── Event dict (all types) ───────────────────────────────────────────────────
# {
#   "start": str
#       The slot start time in "HH:MM" 24-hour format.
#       Always a multiple of 15 minutes (06:00–23:30 range).
#       e.g. "09:00"
#
#   "end": str
#       The slot end time in "HH:MM" 24-hour format.
#       Derived from start + duration. Also capped at 23:30.
#       e.g. "10:30"
#
#   "name": str
#       Human-readable label for the slot. Format varies by type:
#         ACTIVITY   → "{activity_name} (Session {n})"  e.g. "Math (Session 2)"
#         SCHOOL     → The subject field from school_schedule  e.g. "Biology"
#         COMPULSORY → The event name from list_of_compulsory_events  e.g. "Dentist"
#         BREAK      → Always the literal string "Break"
#
#   "type": str
#       Determines how the UI renders this slot and what extra fields exist.
#       One of: "ACTIVITY" | "SCHOOL" | "COMPULSORY" | "BREAK"
#
#   "is_completed": bool
#       True when the user has explicitly verified this session as done.
#       Set via verify_finished_session() or verify_session().
#       Completed sessions are kept across timetable regenerations.
#
#   "is_skipped": bool
#       True when the user explicitly marked this session as not done.
#       Skipped sessions are discarded on the next timetable regeneration
#       (only completed sessions survive regeneration).
#
#   "is_finished": bool
#       True when the current real-world clock time is past this slot's end time.
#       Injected/updated by check_expired_sessions() and _is_event_finished().
#       A finished-but-unverified session shows the "⏰ FINISHED" badge in the UI.
#
#   # ── ACTIVITY-only extra fields ──────────────────────────────────────────
#
#   "activity_name": str
#       The parent activity's name (without the session suffix).
#       Used to look up the activity in list_of_activities.
#       e.g. "Math Revision"
#
#   "session_num": int
#       1-based index of this session within its parent activity.
#       Matches session_num in the corresponding session dict.
#       e.g. 2
#
#   "session_id": str
#       Globally unique identifier for this session.
#       Format: "{activity_name_underscored}_session_{n}"
#       e.g. "Math_Revision_session_2"
#       Used to cross-reference the session across timetable, activities, and
#       finished_sessions without relying on positional index.
#
#   "is_user_edited": bool
#       Present (and True) only when the user manually moved this session to a
#       different time or day via the edit form. Causes the "EDITED" badge to
#       appear in the UI.
#
#   # ── Read-time injected field (not stored in Firebase) ───────────────────
#
#   "can_verify": bool
#       Added by get_dashboard_data() / _can_verify_event() at read time.
#       True when the slot's scheduled time has passed AND the session has not
#       yet been verified (neither completed nor skipped).
#       Controls whether verification buttons are shown on the Dashboard.
# }

st.session_state.timetable_warnings: list[str]
# Human-readable messages produced during the most recent timetable generation.
# Displayed in an expander on the Dashboard tab.
# Each string is prefixed with an emoji severity marker:
#   "✓ ..."  — success / informational (e.g. all hours scheduled)
#   "⚠️ ..." — warning (e.g. could not fit all required hours before deadline)
#   "❌ ..."  — error   (e.g. no free days available before an activity's deadline)
# Example: ["✓ 'Math': All 3.0h scheduled in 3 sessions",
#           "⚠️ 'Essay': 1.0h still needed before deadline"]


# ==============================================================================
# ACTIVITIES
# ==============================================================================

st.session_state.list_of_activities: list[dict]
# The master list of all user-created activities.
# Persisted to Firebase under the 'activities' key.
#
# ── Activity dict ─────────────────────────────────────────────────────────────
# {
#   "activity": str
#       The user-provided display name for this activity.
#       Also used as a lookup key throughout the codebase — must be unique.
#       e.g. "Math Revision"
#
#   "priority": int
#       Urgency ranking from 1 (lowest) to 5 (highest).
#       Used when sorting activities before placing them into the timetable
#       (higher priority gets scheduled into earlier slots).
#       Currently hardcoded to 3 when added via the UI.
#
#   "deadline": int
#       Days remaining from today until this activity must be completed.
#       Calculated once at creation time and stored as-is (so it goes negative
#       over time if the user does not regenerate).
#       Used by the timetable generator to determine the latest available day
#       for scheduling sessions.
#       e.g. 14 (two weeks away), -2 (two days overdue)
#
#   "timing": float
#       Total number of hours the activity requires to complete.
#       The timetable generator fills sessions until this many hours are covered.
#       e.g. 3.0
#
#   "min_session_minutes": int
#       Minimum length (in minutes) of a single scheduled session.
#       Always a multiple of 15. The generator will not create sessions shorter
#       than this unless fewer minutes remain overall.
#       e.g. 30
#
#   "max_session_minutes": int
#       Maximum length (in minutes) of a single scheduled session.
#       Always a multiple of 15. The generator caps each session at this length,
#       splitting remaining work across multiple days if needed.
#       e.g. 120
#
#   "allowed_days": list[str]
#       Weekday names on which this activity is permitted to be scheduled.
#       Subset of WEEKDAY_NAMES = ["Monday", ..., "Sunday"].
#       The generator skips days not in this list when looking for free slots.
#       e.g. ["Monday", "Wednesday", "Friday"]
#
#   "session_mode": str
#       Controls how sessions are created for this activity.
#       "automatic" — timetable generator creates and places sessions.
#       "manual"    — user adds sessions individually via the Activities tab UI;
#                     the generator still places them into time slots but does
#                     not split or resize them.
#
#   "num_sessions": int
#       Total number of sessions (completed + pending) after the last generation.
#       Set by generate_timetable_with_sessions() after placing all sessions.
#       e.g. 4
#
#   "sessions": list[dict]
#       The individual work blocks that make up this activity.
#       See session dict format below.
# }
#
# ── Session dict (inside "sessions") ─────────────────────────────────────────
# {
#   "session_id": str
#       Globally unique identifier.
#       Format: "{activity_name_spaces_replaced_with_underscores}_session_{n}"
#       e.g. "Math_Revision_session_1"
#       Used to cross-reference between list_of_activities, timetable, and
#       finished_sessions without relying on list position.
#
#   "session_num": int
#       1-based index of this session within its parent activity.
#       Matches session_num on the corresponding timetable event dict.
#       e.g. 1
#
#   "scheduled_day": str
#       The day-display key this session is placed on.
#       Format: "Weekday DD/MM"  e.g. "Monday 17/02"
#       Matches a key in st.session_state.timetable.
#
#   "scheduled_date": str
#       Full ISO date string for the scheduled day.
#       Used by check_expired_sessions() to compare against today's date.
#       e.g. "2026-02-17"
#
#   "scheduled_time": str
#       "HH:MM" start time of this session.
#       e.g. "14:00"
#
#   "duration_minutes": int
#       Length of the session in minutes. Always a multiple of 15.
#       e.g. 60
#
#   "duration_hours": float
#       duration_minutes / 60, pre-computed and stored for convenience.
#       Used when summing completed hours for progress display.
#       e.g. 1.0
#
#   "is_completed": bool
#       True when the user verified this session as done.
#       Completed sessions survive timetable regeneration intact.
#
#   "is_skipped": bool
#       True when the user marked this session as not done.
#       Skipped sessions are discarded on the next timetable regeneration.
#
#   "is_finished": bool
#       True when the real-world clock is past this session's end time.
#       Set by check_expired_sessions(). A finished session awaits verification.
#
#   "is_locked": bool
#       Reserved for a future "lock this session in place" feature.
#       Currently always False.
#
#   # ── Manual-mode-only fields ──────────────────────────────────────────────
#
#   "is_manual": bool
#       Always True for sessions created via add_manual_session().
#       Distinguishes manually added sessions from auto-generated ones.
#
#   "is_scheduled": bool
#       False when first created via add_manual_session() (no time slot yet).
#       Intended to flip to True once the timetable generator places the session.
#       (Currently not updated by the generator — reserved for future use.)
#
#   "day_of_week": str | None
#       Optional scheduling preference provided by the user when adding a manual
#       session (e.g. "Tuesday"). The generator attempts to honour this but will
#       use other days if no slot is available on the preferred day.
#       None if the user selected "Any".
# }


# ==============================================================================
# EVENTS
# ==============================================================================

st.session_state.list_of_compulsory_events: list[dict]
# Fixed one-time (and monthly recurring) events that block out timetable slots
# and cannot be moved by the generator.
# Persisted to Firebase under the 'events' key.
#
# ── Event dict ────────────────────────────────────────────────────────────────
# {
#   "event": str
#       The user-provided display name for this event.
#       Shown directly on the timetable row.
#       e.g. "Doctor Appointment"
#
#   "start_time": str
#       "HH:MM" start time.
#       e.g. "10:00"
#
#   "end_time": str
#       "HH:MM" end time. Must be strictly after start_time.
#       e.g. "11:00"
#
#   "day": str
#       Day-display key matching a timetable key.
#       Format: "Weekday DD/MM"  e.g. "Wednesday 25/02"
#
#   "date": str
#       ISO datetime string for the event date (time component is midnight).
#       Used to check whether the event is in the future before placing it.
#       e.g. "2026-02-25T00:00:00"
#
#   "recurrence": str   ← monthly recurring events only
#       Always "monthly" for events added via add_recurring_event().
#       Absent on one-time events added via add_event().
# }


# ==============================================================================
# SCHOOL / RECURRING SCHEDULE
# ==============================================================================

st.session_state.school_schedule: dict[str, list[dict]]
# Recurring weekly or bi-weekly slots that are placed on every matching weekday
# across the generated month. Only weekdays that have at least one slot appear
# as keys. Persisted to Firebase under the 'school_schedule' key.
# Example key: "Monday"
#
# ── Schedule slot dict ────────────────────────────────────────────────────────
# {
#   "subject": str
#       The user-provided name for this recurring block.
#       This is the value written to the timetable event's "name" field,
#       so it is what appears on the Dashboard.
#       e.g. "Biology" or "Part-time Work"
#
#   "start_time": str
#       "HH:MM" start time for this slot on every occurrence.
#       e.g. "08:00"
#
#   "end_time": str
#       "HH:MM" end time for this slot on every occurrence.
#       e.g. "13:00"
#
#   "recurrence": str
#       How often this slot repeats.
#       "weekly"    — appears on every occurrence of this weekday in the month.
#       "bi-weekly" — intended to appear every other week (generator currently
#                     places it weekly; bi-weekly filtering is a planned feature).
#       This key may be absent on legacy entries created via add_school_schedule().
# }


# ==============================================================================
# SESSION VERIFICATION / FINISHED SESSIONS
# ==============================================================================

st.session_state.finished_sessions: list[dict]
# A running log of every session whose scheduled end time has passed.
# Built up incrementally by check_expired_sessions() on each app load.
# Displayed in the Verification tab for the user to confirm or skip.
# Persisted to Firebase under the 'finished_sessions' key.
#
# ── Finished session dict ─────────────────────────────────────────────────────
# {
#   "activity": str
#       Name of the parent activity. Used to look it up in list_of_activities.
#       e.g. "Math Revision"
#
#   "session_id": str
#       Matches session_id on the session dict in list_of_activities and on the
#       timetable event dict. The primary key for cross-referencing.
#       e.g. "Math_Revision_session_2"
#
#   "session_num": int
#       1-based session index, used for display purposes only.
#       e.g. 2
#
#   "scheduled_date": str
#       ISO date string of when the session was scheduled.
#       e.g. "2026-02-17"
#
#   "scheduled_time": str
#       "HH:MM" start time of the session, for display in the Verification tab.
#       e.g. "14:00"
#
#   "duration_minutes": int
#       Session length in minutes, for display in the Verification tab.
#       e.g. 60
#
#   "is_verified": bool
#       False when first added (session has expired but user has not acted yet).
#       Flipped to True when the user clicks either "Done" or "Skip".
#
#   "completed": bool   ← only present after the user verifies
#       True  if the user clicked "Done"  (session was actually completed).
#       False if the user clicked "Skip"  (session was not completed).
#       Absent entirely until is_verified becomes True.
# }

st.session_state.past_incomplete_sessions: dict[str, list[dict]]
# Sessions that were scheduled in the past but have no completion record.
# Populated during timetable generation by check_past_activities().
# Keys are activity names; values are lists of session dicts using the same
# shape as the session dicts inside list_of_activities.
# Shown as warnings in the timetable generation expander.
# Example: { "Math Revision": [ { "session_id": "...", ... } ] }

st.session_state.pending_verifications: any
# Loaded from Firebase under 'pending_verifications'.
# Not actively read in the current codebase — reserved for a future feature
# that would track sessions awaiting verification separately from finished_sessions.

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

st.session_state.user_edits: any
# Loaded from Firebase under 'user_edits'.
# Intended for auditing manual session edits (tracking which sessions the user
# moved and when). Not actively read or written in the current codebase.
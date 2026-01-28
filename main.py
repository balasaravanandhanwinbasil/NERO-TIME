import streamlit as st
import streamlit.components.v1 as components
import random
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore
import json

# -----------------------------
# Firebase init (safe + cached)
# -----------------------------
@st.cache_resource
def init_firebase():
    try:
        firebase_admin.get_app()
    except ValueError:
        try:
            cred = credentials.Certificate("firebase-credentials.json")
            firebase_admin.initialize_app(cred)
        except FileNotFoundError:
            cred = credentials.Certificate(dict(st.secrets["firebase"]))
            firebase_admin.initialize_app(cred)
    return firestore.client()

db = init_firebase()

# -----------------------------
# Constants
# -----------------------------
DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
BREAK_MINUTES = 120
MAX_ACTIVITY_PER_DAY = 6 * 60

# -----------------------------
# Session state
# -----------------------------
defaults = {
    "user_id": None,
    "timetable": {d: [] for d in DAY_NAMES},
    "list_of_activities": [],
    "list_of_compulsory_events": [],
    "data_loaded": False,
    "edit_activity_index": None,
    "edit_event_index": None,
}
for k, v in defaults.items():
    st.session_state.setdefault(k, v)

# -----------------------------
# Time helpers
# -----------------------------
def to_min(t): return int(t[:2]) * 60 + int(t[3:])
def to_str(m): return f"{m//60:02d}:{m%60:02d}"

def slot_free(day, s, e):
    for ev in st.session_state.timetable[day]:
        if not (e <= to_min(ev["start"]) or s >= to_min(ev["end"])):
            return False
    return True

def add_event(day, s, e, name, typ):
    st.session_state.timetable[day].append({
        "start": to_str(s),
        "end": to_str(e),
        "name": name,
        "type": typ
    })

# -----------------------------
# Firebase helpers
# -----------------------------
def save(user, key, data):
    db.collection("users").document(user).collection(key).document("current").set({"data": data})

def load(user, key):
    doc = db.collection("users").document(user).collection(key).document("current").get()
    return doc.to_dict()["data"] if doc.exists else None

# -----------------------------
# Placement logic
# -----------------------------
def place_compulsory():
    for e in st.session_state.list_of_compulsory_events:
        s, e_ = to_min(e["start_time"]), to_min(e["end_time"])
        add_event(e["day"], s, e_, e["event"], "COMPULSORY")

        # 🔑 break after compulsory
        if e_ + BREAK_MINUTES <= 1440:
            add_event(e["day"], e_, e_ + BREAK_MINUTES, "Break", "BREAK")

def place_activities():
    acts = st.session_state.list_of_activities.copy()
    random.shuffle(acts)

    for a in acts:
        remaining = a["timing"] * 60
        days = DAY_NAMES[:]

        while remaining > 0:
            chunk = min(60, remaining)
            random.shuffle(days)
            placed = False

            for d in days:
                used = sum(
                    to_min(ev["end"]) - to_min(ev["start"])
                    for ev in st.session_state.timetable[d]
                    if ev["type"] == "ACTIVITY"
                )
                if used + chunk > MAX_ACTIVITY_PER_DAY:
                    continue

                for h in range(6, 22):
                    s = h * 60
                    e = s + chunk
                    b = e + BREAK_MINUTES
                    if b <= 1440 and slot_free(d, s, b):
                        add_event(d, s, e, a["activity"], "ACTIVITY")
                        add_event(d, e, b, "Break", "BREAK")
                        remaining -= chunk
                        placed = True
                        break
                if placed:
                    break
            if not placed:
                break

def generate():
    st.session_state.timetable = {d: [] for d in DAY_NAMES}
    place_compulsory()
    place_activities()
    save(st.session_state.user_id, "timetable", st.session_state.timetable)

# -----------------------------
# UI
# -----------------------------
st.set_page_config("Timetable Generator", "📅", layout="wide")

if not st.session_state.user_id:
    st.title("🔐 Login")
    uid = st.text_input("User ID")
    if st.button("Login"):
        st.session_state.user_id = uid
        st.rerun()
    st.stop()

if not st.session_state.data_loaded:
    st.session_state.list_of_activities = load(st.session_state.user_id, "activities") or []
    st.session_state.list_of_compulsory_events = load(st.session_state.user_id, "events") or []
    st.session_state.timetable = load(st.session_state.user_id, "timetable") or st.session_state.timetable
    st.session_state.data_loaded = True

st.title("📅 Smart Timetable Generator")

# -----------------------------
# Sidebar
# -----------------------------
with st.sidebar:
    st.subheader("➕ Add Activity")
    with st.form("add_act"):
        n = st.text_input("Name")
        t = st.number_input("Hours", 1, 24, 1)
        if st.form_submit_button("Add"):
            st.session_state.list_of_activities.append({
                "activity": n,
                "timing": t,
                "priority": 3,
                "deadline": 5
            })
            save(st.session_state.user_id, "activities", st.session_state.list_of_activities)

    st.divider()

    st.subheader("➕ Add Event")
    with st.form("add_evt"):
        n = st.text_input("Event")
        d = st.selectbox("Day", DAY_NAMES)
        s = st.time_input("Start")
        e = st.time_input("End")
        if st.form_submit_button("Add"):
            st.session_state.list_of_compulsory_events.append({
                "event": n,
                "day": d,
                "start_time": s.strftime("%H:%M"),
                "end_time": e.strftime("%H:%M")
            })
            save(st.session_state.user_id, "events", st.session_state.list_of_compulsory_events)

# -----------------------------
# Controls
# -----------------------------
col1, col2 = st.columns(2)
with col1:
    if st.button("🚀 Generate"):
        generate()
        st.success("Generated!")

with col2:
    if st.button("💾 Save"):
        save(st.session_state.user_id, "timetable", st.session_state.timetable)

# -----------------------------
# Timetable (HTML)
# -----------------------------
st.header("📊 Weekly Timetable")

try:
    with open("timetable_component.html", "r", encoding="utf-8") as f:
        html = f.read()

    html = html.replace(
        'let timetableData = {"Monday":[],"Tuesday":[],"Wednesday":[],"Thursday":[],"Friday":[]};',
        f"let timetableData = {json.dumps(st.session_state.timetable)};"
    )

    components.html(html, height=900, scrolling=True)

except FileNotFoundError:
    st.error("Missing timetable_component.html")

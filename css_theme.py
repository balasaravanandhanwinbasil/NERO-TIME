css_colours = """
<style>
/* --------------------------------------------------
   GLOBAL THEME-AWARE COLORS
-------------------------------------------------- */

:root {
    --bg: var(--background-color);
    --bg-secondary: var(--secondary-background-color);
    --text: var(--text-color);
    --primary: var(--primary-color);
    --purple: #E91E63;
    --purple-dark: #C2185B;
    --purple-light: #F8BBD0;
    --purple-hover: #F48FB1;
    --activity-color: #E91E63;
    --school-color: #FF9800;
    --compulsory-color: #F44336;
    --break-color: #9E9E9E;
    --finished-color: #2196F3;
}

/* --------------------------------------------------
   BASE APP
-------------------------------------------------- */

#MainMenu { visibility: hidden; }
footer { visibility: hidden; }

.stApp {
    background: var(--bg);
    color: var(--text);
}

.block-container {
    background: var(--bg-secondary);
    border-radius: 12px;
    padding: 2rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

/* --------------------------------------------------
   HEADINGS & TEXT
-------------------------------------------------- */

h1, h2, h3, h4, h5, h6 {
    color: var(--text);
    font-weight: 600;
}

p, span, label, div {
    color: var(--text);
}

/* --------------------------------------------------
   LIVE CLOCK
-------------------------------------------------- */

.live-clock {
    text-align: center;
    padding: 1.5rem;
    background: linear-gradient(135deg, var(--purple-light) 0%, var(--purple) 100%);
    border-radius: 12px;
    margin: 1rem 0 2rem 0;
    box-shadow: 0 4px 12px rgba(233, 30, 99, 0.2);
}

.clock-time {
    font-size: 3rem;
    font-weight: 700;
    color: white;
    margin: 0;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
}

.clock-date {
    font-size: 1.2rem;
    color: rgba(255,255,255,0.9);
    margin-top: 0.5rem;
}

/* --------------------------------------------------
   BUTTONS - PINKISH PURPLE THEME
-------------------------------------------------- */

.stButton > button {
    font-size: 14px;
    padding: 10px 20px;
    border-radius: 8px;
    border: 2px solid var(--purple-light);
    background: var(--bg);
    color: var(--purple);
    font-weight: 600;
    transition: all 0.3s ease;
}

.stButton > button:hover {
    background: var(--purple-light);
    color: white;
    border-color: var(--purple);
    box-shadow: 0 4px 12px rgba(233, 30, 99, 0.3);
    transform: translateY(-2px);
}

.stButton > button[kind="primary"] {
    background: var(--purple);
    color: white;
    border: none;
    box-shadow: 0 4px 8px rgba(233, 30, 99, 0.3);
}

.stButton > button[kind="primary"]:hover {
    background: var(--purple-dark);
    box-shadow: 0 6px 16px rgba(233, 30, 99, 0.4);
    transform: translateY(-2px);
}

.stButton > button:active {
    transform: translateY(0px);
}

/* --------------------------------------------------
   TABS - PINKISH PURPLE THEME
-------------------------------------------------- */

.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    background: var(--bg);
    padding: 8px;
    border-radius: 12px;
}

.stTabs [data-baseweb="tab"] {
    height: 50px;
    padding: 12px 24px;
    border-radius: 8px;
    color: var(--text);
    transition: all 0.3s ease;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 500;
}

.stTabs [data-baseweb="tab"]:hover {
    background: var(--purple-light);
    color: white;
}

.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, var(--purple) 0%, var(--purple-dark) 100%);
    color: white !important;
    box-shadow: 0 2px 8px rgba(233, 30, 99, 0.3);
}

/* --------------------------------------------------
   INPUTS - PURPLE ACCENTS
-------------------------------------------------- */

.stTextInput input,
.stNumberInput input,
.stDateInput input,
.stTimeInput input {
    border-radius: 8px;
    border: 2px solid rgba(128,128,128,0.3);
    background: var(--bg);
    color: var(--text);
    transition: all 0.3s ease;
}

.stTextInput input:focus,
.stNumberInput input:focus,
.stDateInput input:focus,
.stTimeInput input:focus {
    border-color: var(--purple);
    box-shadow: 0 0 0 3px rgba(233, 30, 99, 0.15);
}

.stSlider [data-baseweb="slider"] {
    background: var(--purple-light);
}

.stSlider [role="slider"] {
    background-color: var(--purple);
}

/* --------------------------------------------------
   METRICS - PURPLE ACCENTS
-------------------------------------------------- */

[data-testid="stMetricValue"] {
    font-size: 32px;
    font-weight: 700;
    color: var(--purple);
}

[data-testid="stMetricLabel"] {
    color: var(--text);
    font-weight: 600;
}

/* --------------------------------------------------
   TIMETABLE ROW - HORIZONTAL LAYOUT (INFO LEFT, TIME+ACTIONS RIGHT)
-------------------------------------------------- */

.timetable-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin: 12px 0;
    padding: 16px 20px;
    border-radius: 10px;
    background: var(--bg);
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    border-left: 5px solid;
    transition: all 0.3s ease;
    min-height: 70px;
}

.timetable-row:hover {
    box-shadow: 0 4px 16px rgba(0,0,0,0.1);
    transform: translateX(4px);
}

.timetable-row.activity {
    border-left-color: var(--activity-color);
    background: linear-gradient(to right, rgba(233, 30, 99, 0.02), var(--bg));
}

.timetable-row.school {
    border-left-color: var(--school-color);
    background: linear-gradient(to right, rgba(255, 152, 0, 0.02), var(--bg));
}

.timetable-row.compulsory {
    border-left-color: var(--compulsory-color);
    background: linear-gradient(to right, rgba(244, 67, 54, 0.02), var(--bg));
}

.timetable-row.break {
    border-left-color: var(--break-color);
    opacity: 0.7;
}

.timetable-row.finished {
    border-left-color: var(--finished-color);
    background: linear-gradient(to right, rgba(33, 150, 243, 0.05), var(--bg));
}

.event-info {
    flex: 1;
    min-width: 0;
    display: flex;
    flex-direction: column;
    gap: 6px;
}

.event-title {
    font-weight: 600;
    font-size: 1.05rem;
    margin: 0;
    display: flex;
    align-items: center;
    gap: 10px;
    flex-wrap: wrap;
    line-height: 1.4;
}

.event-details {
    font-size: 0.88rem;
    opacity: 0.75;
    line-height: 1.5;
}

.event-right-section {
    display: flex;
    align-items: center;
    gap: 20px;
    min-width: fit-content;
}

.event-time {
    font-weight: 600;
    font-size: 1rem;
    color: var(--text);
    opacity: 0.85;
    white-space: nowrap;
    font-family: 'Courier New', monospace;
    min-width: 130px;
    text-align: right;
}

.event-actions {
    display: flex;
    gap: 6px;
    align-items: center;
}

.event-actions button {
    min-width: 36px !important;
    height: 36px !important;
    padding: 0 !important;
    font-size: 18px !important;
}

.happening-now {
    background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
    color: white;
    padding: 4px 10px;
    border-radius: 12px;
    font-weight: 600;
    font-size: 0.7rem;
    display: inline-block;
    box-shadow: 0 2px 4px rgba(76, 175, 80, 0.3);
    animation: pulse 2s infinite;
}

.finished-badge {
    background: linear-gradient(135deg, #2196F3 0%, #1976D2 100%);
    color: white;
    padding: 4px 10px;
    border-radius: 12px;
    font-weight: 600;
    font-size: 0.7rem;
    display: inline-block;
    box-shadow: 0 2px 4px rgba(33, 150, 243, 0.3);
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.8; }
}

.user-edited-badge {
    background: var(--purple);
    color: white;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 0.7rem;
    font-weight: 600;
}

/* --------------------------------------------------
   EXPANDERS 
-------------------------------------------------- */

.streamlit-expanderHeader {
    background: var(--bg);
    border-radius: 8px;
    padding: 12px 16px;
    border: 2px solid var(--purple-light);
    color: var(--text);
    transition: all 0.3s ease;
    font-weight: 600;
}

.streamlit-expanderHeader:hover {
    background: var(--purple-light);
    color: white;
    border-color: var(--purple);
}

/* --------------------------------------------------
   PROGRESS BAR
-------------------------------------------------- */

.stProgress > div > div > div {
    background: linear-gradient(90deg, var(--purple) 0%, var(--purple-dark) 100%);
}

/* Remove weird shape above expanders */
details summary::marker,
details summary::-webkit-details-marker {
    display: none;
}

</style>

"""
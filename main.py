# Constants
VALID_SUBJECTS = ["Math", "English", "Mother Tongue", "Cygames Glazing"]
DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

# Configuration
OpenManualTimetable = 1
break_time = 2  # hours

# Timetable structure - now stores events as a list of time ranges
timetable = {day: [] for day in DAY_NAMES}

# Completion tracking
completed = 0
completedWeek = {day: 0 for day in DAY_NAMES}

# Current day
day_index = datetime.now().weekday()

# Activity and event lists
list_of_activities = []
list_of_badges = []
list_of_compulsory_events = []
completed_events = []

# old stuff
validSubject = VALID_SUBJECTS
day_names = DAY_NAMES

# Helper functions for time manipulation
def time_str_to_minutes(time_str):
    """Convert HH:MM to minutes since midnight."""
    parts = time_str.split(":")
    return int(parts[0]) * 60 + int(parts[1])

def minutes_to_time_str(minutes):
    """Convert minutes since midnight to HH:MM."""
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours:02d}:{mins:02d}"

def add_minutes(time_str, minutes_to_add):
    """Add minutes to a time string."""
    total_minutes = time_str_to_minutes(time_str) + minutes_to_add
    # Handle overflow past midnight
    if total_minutes >= 1440:  # 24 hours = 1440 minutes
        total_minutes = 1439  # Cap at 23:59
    return minutes_to_time_str(total_minutes)

def is_time_slot_free(day, start_time, end_time):
    """Check if a time slot is free on a given day."""
    start_mins = time_str_to_minutes(start_time)
    end_mins = time_str_to_minutes(end_time)

    for event in timetable[day]:
        event_start = time_str_to_minutes(event["start"])
        event_end = time_str_to_minutes(event["end"])

        # Check for overlap
        if not (end_mins <= event_start or start_mins >= event_end):
            return False

    return True

def add_event_to_timetable(day, start_time, end_time, event_name, event_type):
    """Add an event to the timetable."""
    timetable[day].append({
        "start": start_time,
        "end": end_time,
        "name": event_name,
        "type": event_type
    })

    # Sort events by start time
    timetable[day].sort(key=lambda x: time_str_to_minutes(x["start"]))

def get_day_activity_minutes(day):
    """Calculate total minutes of activities (not compulsory events) on a day."""
    total_minutes = 0
    for event in timetable[day]:
        if event["type"] == "ACTIVITY":
            start_mins = time_str_to_minutes(event["start"])
            end_mins = time_str_to_minutes(event["end"])
            total_minutes += (end_mins - start_mins)
    return total_minutes

# Activity management functions
def activity(activity: str, priority: str, deadline: int, timing: int = 0):
    list_of_activities.append({"activity": activity, "priority": priority, "deadline": deadline, "timing": timing})

def add_activity():
    print("In multiple separate lines, enter the following information:")

    # Activity name validation
    activity_name = input("Activity name: ").strip()
    while activity_name == "":
        print("Activity name cannot be empty.")
        activity_name = input("Activity name: ").strip()

    # Priority validation (1-5)
    while True:
        try:
            priority = int(input("Priority (1–5): "))
            if 1 <= priority <= 5:
                break
            else:
                print("Priority must be between 1 and 5.")
        except ValueError:
            print("Invalid input. Please enter a number between 1 and 5.")

    # Deadline validation (date input, converted to days left)
    while True:
        deadline_input = input("Deadline date (YYYY-MM-DD): ").strip()
        try:
            deadline_date = datetime.strptime(deadline_input, "%Y-%m-%d")
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            days_left = (deadline_date - today).days

            if days_left < 0:
                print("Deadline cannot be in the past.")
            else:
                deadline = days_left
                print(f"Deadline set to {days_left} day(s) from now.")
                break
        except ValueError:
            print("Invalid date format. Please use YYYY-MM-DD (e.g., 2026-01-30).")

    # Timing validation IN HOURS btw (empty will result in it assuming it takes one hour)
    while True:
        timing_input = input("Total time needed to complete the activity (press Enter for 1 hour): ").strip()
        if timing_input == "":
            timing = 1
            break
        else:
            try:
                timing = int(timing_input)
                if timing > 0:
                    break
                else:
                    print("Timing must be greater than 0.")
            except ValueError:
                print("Invalid input. Please enter a valid number or press Enter for 1 hour.")

    activity(activity_name, priority, deadline, timing)
    print("Added Activity.")

# Compulsory event management functions
def compulsory_event(event: str, start_time: str, end_time: str, day: str):
    list_of_compulsory_events.append({
        "event": event,
        "start_time": start_time,
        "end_time": end_time,
        "day": day
    })

def validate_time_format(time_str: str):
    """Validate time format (HH:MM) and return True if valid."""
    try:
        time_parts = time_str.split(":")
        if len(time_parts) != 2:
            return False
        hour = int(time_parts[0])
        minute = int(time_parts[1])
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            return True
        return False
    except (ValueError, IndexError):
        return False

def time_to_minutes(time_str: str):
    """Convert time string (HH:MM) to minutes since midnight."""
    parts = time_str.split(":")
    return int(parts[0]) * 60 + int(parts[1])

def add_compulsory_event():
    print("In multiple separate lines, enter the following information:")

    # Event name validation
    event_name = input("Event name: ").strip()
    while event_name == "":
        print("Event name cannot be empty.")
        event_name = input("Event name: ").strip()

    # Start time validation
    while True:
        start_time = input("Start time (HH:MM, e.g. 09:00): ").strip()
        if validate_time_format(start_time):
            break
        else:
            print("Invalid time format. Please use HH:MM (e.g., 09:00).")

    # End time validation
    while True:
        end_time = input("End time (HH:MM, e.g. 10:00): ").strip()
        if validate_time_format(end_time):
            # Check that end time is after start time
            if time_to_minutes(end_time) > time_to_minutes(start_time):
                break
            else:
                print("End time must be after start time.")
        else:
            print("Invalid time format. Please use HH:MM (e.g., 10:00).")

    # Day validation
    while True:
        day = input("Day (Monday–Friday): ").strip().capitalize()
        if day in DAY_NAMES:
            break
        else:
            print(f"Invalid day. Please enter one of: {', '.join(DAY_NAMES)}")

    compulsory_event(event_name, start_time, end_time, day)
    print("Compulsory event added successfully!")

# Timetable generation functions
def place_compulsory_events():
    """Place compulsory events in the timetable."""
    for event in list_of_compulsory_events:
        day = event["day"]
        start_time = event["start_time"]
        end_time = event["end_time"]

        # Add compulsory event
        add_event_to_timetable(day, start_time, end_time, event["event"], "COMPULSORY")

        # Add break time after
        break_end = add_minutes(end_time, break_time * 60)
        if time_str_to_minutes(break_end) < 1440:  # Don't add break if it goes past midnight
            add_event_to_timetable(day, end_time, break_end, "Break", "BREAK")

def get_available_days_until_deadline(deadline_days):
    """Get list of available weekdays until deadline."""
    available_days = []
    current_day_index = datetime.now().weekday()

    for day_offset in range(deadline_days + 1):
        day_index = (current_day_index + day_offset) % 7
        # Only include weekdays (Monday=0 to Friday=4)
        if day_index < 5:
            available_days.append(DAY_NAMES[day_index])

    return available_days

def find_free_slot(day, duration_minutes, start_hour=6, end_hour=22):
    """Find a free slot on a given day for a specific duration."""
    # Try random starting times within study hours
    attempts = []

    # Generate all possible 15-minute increment start times
    for hour in range(start_hour, end_hour):
        for minute in [0, 15, 30, 45]:
            start_time = f"{hour:02d}:{minute:02d}"
            end_time = add_minutes(start_time, duration_minutes)

            # Check if end time is within study hours
            if time_str_to_minutes(end_time) > end_hour * 60:
                continue

            # Check if slot is free (including break time after)
            break_end = add_minutes(end_time, break_time * 60)
            if is_time_slot_free(day, start_time, break_end):
                attempts.append((start_time, end_time))

    # Randomize the attempts
    if attempts:
        random.shuffle(attempts)
        return attempts[0]

    return None

def place_activities():
    """Place activities in the timetable as randomized chunks of 45-60 minutes."""
    MAX_ACTIVITY_MINUTES_PER_DAY = 6 * 60  # 6 hours

    # Randomize activities completely
    randomized_activities = list_of_activities.copy()
    random.shuffle(randomized_activities)

    for activity in randomized_activities:
        total_duration_hours = activity["timing"]
        deadline_days = activity["deadline"]

        if total_duration_hours == 0:
            continue

        # Get available days until deadline
        available_days = get_available_days_until_deadline(deadline_days)
        if not available_days:
            print(f"Warning: Activity '{activity['activity']}' has no available days before deadline.")
            continue

        # Convert total duration to minutes
        total_duration_minutes = total_duration_hours * 60
        remaining_minutes = total_duration_minutes
        session_number = 1

        while remaining_minutes > 0:
            # Determine chunk size: random between 45-60 minutes, or remaining if less
            if remaining_minutes <= 60:
                chunk_minutes = remaining_minutes
            else:
                # Randomly choose between 45-60 minutes
                chunk_minutes = random.randint(45, 60)
                # But don't create tiny leftover chunks
                if remaining_minutes - chunk_minutes < 30:
                    chunk_minutes = remaining_minutes

            placed = False

            # Try to place this chunk on available days
            available_days_shuffled = available_days.copy()
            random.shuffle(available_days_shuffled)  # Randomize day selection

            for day in available_days_shuffled:
                # Check daily limit
                current_minutes = get_day_activity_minutes(day)
                if current_minutes + chunk_minutes > MAX_ACTIVITY_MINUTES_PER_DAY:
                    continue

                # Find a free slot
                slot = find_free_slot(day, chunk_minutes)

                if slot:
                    start_time, end_time = slot

                    # Create activity label
                    activity_label = activity['activity']
                    if total_duration_hours > 1:
                        activity_label += f" (Session {session_number})"

                    # Add activity to timetable
                    add_event_to_timetable(day, start_time, end_time, activity_label, "ACTIVITY")

                    # Add break after activity
                    break_end = add_minutes(end_time, break_time * 60)
                    if time_str_to_minutes(break_end) < 1440:
                        add_event_to_timetable(day, end_time, break_end, "Break", "BREAK")

                    remaining_minutes -= chunk_minutes
                    session_number += 1
                    placed = True
                    break

            if not placed:
                print(f"Warning: Could not place {chunk_minutes} minutes of '{activity['activity']}' - no suitable time slot found.")
                break

def generate_timetable():
    """Generate the complete timetable with compulsory events and activities."""
    # Clear existing timetable
    global timetable
    timetable = {day: [] for day in DAY_NAMES}

    place_compulsory_events()
    place_activities()

def print_timetable():
    """Print the timetable in a readable format."""
    for day in day_names:
        print(f"\n{day}")
        print("-" * 50)
        if not timetable[day]:
            print("  No events scheduled")
        else:
            for event in timetable[day]:
                type_emoji = {
                    "COMPULSORY": "🔴",
                    "ACTIVITY": "🔵",
                    "BREAK": "⚪"
                }
                emoji = type_emoji.get(event["type"], "")
                print(f"  {emoji} {event['start']} - {event['end']}: {event['name']}")

# Test code
print("=== ADD ACTIVITIES ===")
print("Press Enter to add an activity, or type 'n' to finish")
x = input("")

while x != "n":
    add_activity()
    print("\nPress Enter to add another activity, or type 'n' to finish")
    x = input("")

print("\n=== ADD COMPULSORY EVENTS ===")
print("Press Enter to add a compulsory event, or type 'n' to finish")
x = input("")

while x != "n":
    add_compulsory_event()
    print("\nPress Enter to add another event, or type 'n' to finish")
    x = input("")

print("\n=== GENERATING TIMETABLE ===")
generate_timetable()
print("\n=== YOUR TIMETABLE ===")
print_timetable()

print("\n=== SUMMARY ===")
print(f"Total activities added: {len(list_of_activities)}")
print(f"Total compulsory events added: {len(list_of_compulsory_events)}")

for day in DAY_NAMES:
    total_minutes = sum(
        time_str_to_minutes(event["end"]) - time_str_to_minutes(event["start"])
        for event in timetable[day]
        if event["type"] in ["ACTIVITY", "COMPULSORY"]
    )
    hours = total_minutes // 60
    minutes = total_minutes % 60
    if total_minutes > 0:
        print(f"{day}: {hours}h {minutes}m scheduled")

  # code test

# Test adding activities
print("=== ADD ACTIVITIES ===")
print("Press Enter to add an activity, or type 'n' to finish")
x = input("")

while x != "n":
    add_activity()
    print("\nPress Enter to add another activity, or type 'n' to finish")
    x = input("")

# Test adding compulsory events
print("\n=== ADD COMPULSORY EVENTS ===")
print("Press Enter to add a compulsory event, or type 'n' to finish")
x = input("")

while x != "n":
    add_compulsory_event()
    print("\nPress Enter to add another event, or type 'n' to finish")
    x = input("")

# Generate and display timetable
print("\n=== GENERATING TIMETABLE ===")
generate_timetable()
print("\n=== YOUR TIMETABLE ===")
print_timetable()

# Show summary
print("\n=== SUMMARY ===")
print(f"Total activities added: {len(list_of_activities)}")
print(f"Total compulsory events added: {len(list_of_compulsory_events)}")

for day in DAY_NAMES:
    total_minutes = sum(
        time_str_to_minutes(event["end"]) - time_str_to_minutes(event["start"])
        for event in timetable[day]
        if event["type"] in ["ACTIVITY", "COMPULSORY"]
    )
    hours = total_minutes // 60
    minutes = total_minutes % 60
    if total_minutes > 0:
        print(f"{day}: {hours}h {minutes}m scheduled")

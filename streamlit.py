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

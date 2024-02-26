import pandas as pd
from datetime import datetime, timedelta

# Replace the following date strings with your actual relationship start date and long-distance date
relationship_start_date = ""  # Format: "YYYY-MM-DD"
long_distance_date = ""  # Format: "YYYY-MM-DD"

# Fill in the details for each PAST in-person meeting in the format ("start_date", "end_date", "location")
time_together = [
    # ("YYYY-MM-DD", "YYYY-MM-DD", "City"),
    # Add more entries as needed
]

# Fill in the details for each FUTURE in person meeting in the format ("start_date", "end_date", "location")
future_plans = [
    # ("YYYY-MM-DD", "YYYY-MM-DD", "City"),
    # Add more entries as needed
]

current_date = datetime.today()
relationship_start_date = datetime.strptime(relationship_start_date, "%Y-%m-%d")

def format_time_duration(duration):
    if isinstance(duration, timedelta):
        years, days = divmod(duration.days, 365)
        months, days = divmod(days, 30)
        weeks, days = divmod(days, 7)
    else:
        years, days = divmod(duration, 365)
        months, days = divmod(days, 30)
        weeks, days = divmod(days, 7)

    formatted_duration = ""
    if years:
        formatted_duration += f"{years} year{'s' if years > 1 else ''} "
    if months:
        formatted_duration += f"{months} month{'s' if months > 1 else ''} "
    if weeks:
        formatted_duration += f"{weeks} week{'s' if weeks > 1 else ''} "
    if days:
        formatted_duration += f"{days} day{'s' if days > 1 else ''}"

    return formatted_duration.strip()

def calculate_relationship_duration(start_date, current_date):
    return current_date - start_date

def calculate_long_distance_duration(long_distance_date, current_date):
    return current_date - long_distance_date

def calculate_days_between_visits(time_together, long_distance_date):
    days_between_visits = []
    previous_end_date = datetime.strptime(long_distance_date, "%Y-%m-%d")

    for start, end, _ in time_together:
        current_start_date = datetime.strptime(start, "%Y-%m-%d")
        days_between = (current_start_date - previous_end_date).days
        days_between_visits.append(days_between)
        previous_end_date = datetime.strptime(end, "%Y-%m-%d") + timedelta(days=1)  # Add 1 day for inclusivity

    return days_between_visits

def calculate_time_since_last_visit(time_together, current_date):
    last_meeting_end_date = max([datetime.strptime(end, "%Y-%m-%d") for _, end, _ in time_together])
    time_since_last_visit = current_date - last_meeting_end_date
    return time_since_last_visit

def calculate_time_until_next_visit(future_plans, current_date):
    if not future_plans:
        return None

    next_meeting_start_date = None
    for start, _, _ in future_plans:
        if datetime.strptime(start, "%Y-%m-%d") > current_date:
            next_meeting_start_date = datetime.strptime(start, "%Y-%m-%d")
            break

    return format_time_duration(next_meeting_start_date - current_date) if next_meeting_start_date else None


def create_time_together_df(time_together, long_distance_date):
    time_together = {
        "Start Date": [datetime.strptime(start, "%Y-%m-%d") for start, _, _ in time_together],
        "End Date": [datetime.strptime(end, "%Y-%m-%d") for _, end, _ in time_together],
        "Location": [location for _, _, location in time_together],
        "Days Together": [(datetime.strptime(end, "%Y-%m-%d") - datetime.strptime(start, "%Y-%m-%d")).days + 1 for start, end, _ in time_together],
        "Days Between Visits": calculate_days_between_visits(time_together, long_distance_date)
    }
    return pd.DataFrame(time_together)


# Create time together DataFrame
time_together_df = create_time_together_df(time_together, long_distance_date)

def calculate_relationship_stats(time_together_df, long_distance_date, current_date):
    # Convert string dates to datetime objects
    long_distance_date = datetime.strptime(long_distance_date, "%Y-%m-%d")
    # Calculate relationship stats
    relationship_duration = calculate_relationship_duration(relationship_start_date, current_date)
    long_distance_duration = calculate_long_distance_duration(long_distance_date, current_date)
    total_in_person_duration = time_together_df["Days Together"].sum()
    total_in_person_meetings = time_together_df.shape[0]
    days_between_visits = time_together_df["Days Between Visits"]
    longest_gap = days_between_visits.max()
    shortest_gap = days_between_visits.min()
    days_together_since_long_distance = time_together_df[time_together_df["Start Date"] >= long_distance_date]["Days Together"].sum()
    average_in_person_duration = total_in_person_duration / total_in_person_meetings
    average_days_together_per_month = round(days_together_since_long_distance / (long_distance_duration.days / 30), 1)  # Average days together per long-distance month
    most_visited_city = time_together_df["Location"].mode().iloc[0]  # Get the most frequently occurring city
    time_since_last_visit = calculate_time_since_last_visit(time_together, current_date)
    time_until_next_visit = calculate_time_until_next_visit(future_plans, current_date)


    return {
        "relationship_duration": format_time_duration(relationship_duration),
        "long_distance_duration": format_time_duration(long_distance_duration),
        "percentage_long_distance": round((long_distance_duration.days / relationship_duration.days) * 100, 1),
        "percentage_in_person_LDR": round((total_in_person_duration / long_distance_duration.days) * 100, 1),
        "days_together_since_LDR": format_time_duration(days_together_since_long_distance),
        "days_together_current_year": time_together_df[time_together_df["Start Date"].dt.year == current_date.year]["Days Together"].sum(),
        "average_time_together_in_person": format_time_duration(average_in_person_duration),
        "average_time_between_visits": format_time_duration(round(days_between_visits.mean())),
        "average_days_together_per_month": average_days_together_per_month,
        "longest_gap_between_meetings": format_time_duration(longest_gap) if not pd.isna(longest_gap) else None,
        "shortest_gap_between_meetings": format_time_duration(shortest_gap) if not pd.isna(shortest_gap) else None,
        "days_together_since_long_distance": format_time_duration(days_together_since_long_distance),
        "number_of_locations_visited": time_together_df["Location"].nunique(),
        "most_visited_city": most_visited_city,
        "total_trips_taken": len(time_together_df),
        "time_since_last_visit": format_time_duration(time_since_last_visit),
        "time_until_next_visit": time_until_next_visit
    }

stats = calculate_relationship_stats(time_together_df, long_distance_date, current_date)

# Display the results in a more organized and readable format
print("\nRelationship Statistics:")
print("Total length of Relationship:", stats["relationship_duration"])
print("Length of Long-Distance Relationship (LDR):", stats["long_distance_duration"])
print("Percent LDR in total relationship:",stats["percentage_long_distance"], "%")

print("\nTime Spent Together:")
print("Total time spent together since LDR:", stats["days_together_since_LDR"])
print(f"Days spent together in {current_date.year}:", stats["days_together_current_year"], "days")
print("Percentage of relationship spent in person since LDR:", stats["percentage_in_person_LDR"], "%")
print("Average length of time spent together:", stats["average_time_together_in_person"])
print("Average number of days together (monthly):", stats["average_days_together_per_month"])

print("\nTime Spent Apart:")
print("Average time between visits:", stats["average_time_between_visits"])
print("Longest time between visits:", stats["longest_gap_between_meetings"])
print("Shortest time between visits:", stats["shortest_gap_between_meetings"])
print("Time since last visit:", stats["time_since_last_visit"])
print("Time until next visit:", "No future visits in the in-person calendar :( If this is a mistake, please update the calendar or buy a plane ticket." if stats["time_until_next_visit"] is None else stats["time_until_next_visit"])
print("\nTravel and Locations:")
print(f"Total trips taken:", stats["total_trips_taken"])
print("Number of places visited together:", stats["number_of_locations_visited"])
print(f"Most visited place:", stats["most_visited_city"])

print(f"\nLove between us: Lots and lots\n")
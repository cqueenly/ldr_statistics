import pandas as pd
from datetime import datetime, timedelta
import json
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageTemplate, Frame
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


# Load data from external file
with open('relationship_stats.json', 'r') as file:
    data = json.load(file)

relationship_start_date = datetime.strptime(data['relationship_start_date'], "%Y-%m-%d")
long_distance_date = datetime.strptime(data['long_distance_date'], "%Y-%m-%d")

# Convert list of dicts to the format needed by existing functions
time_together = [(item['start_date'], item['end_date'], item['location']) for item in data['time_together']]
future_plans = [(item['start_date'], item['end_date'], item['location']) for item in data['future_plans']]
gifts_and_letters = data['gifts_and_letters']
custom_alerts = data['custom_alerts']

current_date = datetime.today()

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
    previous_end_date = long_distance_date

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

def calculate_gift_and_letter_stats(gifts_and_letters):
    sorted_gifts_and_letters = sorted(gifts_and_letters, key=lambda x: x['date_received'], reverse=True)
    
    recent_gifts_and_letters = sorted_gifts_and_letters[:5]
    
    recent_gifts_info = [{
        "date_received": gift['date_received'],
        "description": gift['description'],
        "for": gift['for']
    } for gift in recent_gifts_and_letters]

    return {
        "total_gifts_and_letters": len(gifts_and_letters),
        "recent_gifts_and_letters": recent_gifts_info
    }

def calculate_upcoming_events(custom_alerts, current_date):
    upcoming_events = [alert for alert in custom_alerts if datetime.strptime(alert['date'], "%Y-%m-%d") > current_date]

    upcoming_events_sorted = sorted(upcoming_events, key=lambda x: datetime.strptime(x['date'], "%Y-%m-%d"))

    events_info = [{
        "date": event['date'],
        "description": event['description'],
        "days_until_event": (datetime.strptime(event['date'], "%Y-%m-%d") - current_date).days
    } for event in upcoming_events_sorted]

    return {
        "total_upcoming_events": len(upcoming_events_sorted),
        "upcoming_events": events_info
    }



# Create time together DataFrame
time_together_df = create_time_together_df(time_together, long_distance_date)

def calculate_relationship_stats(time_together_df, long_distance_date, current_date, gifts_and_letters, custom_alerts):
    # Convert string dates to datetime objects
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
    gift_stats = calculate_gift_and_letter_stats(gifts_and_letters)
    event_stats = calculate_upcoming_events(custom_alerts, current_date)


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
        "time_until_next_visit": time_until_next_visit,
        "gift_stats": gift_stats,
        "event_stats": event_stats
    }
stats = calculate_relationship_stats(time_together_df, long_distance_date, current_date, gifts_and_letters, custom_alerts)


# Define a love-themed color scheme
background_color = colors.HexColor("#ffccf2")  # Light pink
header_color = colors.HexColor("#ff99cc")  # Pink
text_color = colors.HexColor("#663366")  # Dark purple
highlight_color = colors.HexColor("#ff6699")  # Bright pink

page_width, page_height = letter

# Create a full-page frame
full_page_frame = Frame(0, 0, page_width, page_height, id='full_page')

# Create the PDF document
file_path = "Our_Relationship.pdf"
doc = SimpleDocTemplate(file_path, pagesize=letter)
flowables = []

def add_floral_borders(canvas, doc):
    
    canvas.drawImage('floral.png', 0, 0, width=doc.pagesize[0], height=doc.pagesize[1], mask='auto')

pdfmetrics.registerFont(TTFont('Garamond', 'Garamond.ttf'))
pdfmetrics.registerFont(TTFont('GreatVibes', 'GreatVibes.ttf'))
styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='FirstHeading', parent=styles['Heading1'], fontName='GreatVibes', fontSize=35, alignment=TA_CENTER, textColor=header_color))
styles.add(ParagraphStyle(name='CenterHeading', parent=styles['Heading1'], fontName='GreatVibes', fontSize=25, alignment=TA_CENTER, textColor=header_color))
styles.add(ParagraphStyle(name='BodysText', parent=styles['Normal'], fontName='Garamond', fontSize=13, textColor=text_color,alignment=TA_CENTER))
styles.add(ParagraphStyle(name='LoveNote', parent=styles['Normal'], textColor=highlight_color, fontSize=35, spaceAfter=20, alignment=TA_CENTER, fontName='GreatVibes'))

# Title
flowables.append(Spacer(1, 125))
flowables.append(Paragraph("Relationship Statistics", styles['FirstHeading']))
flowables.append(Spacer(1, 15))

# Relationship Duration and Details
flowables.append(Paragraph(f"We've been together for {stats['relationship_duration']}", styles['BodysText']))
flowables.append(Paragraph(f"We've been long distance for: {stats['long_distance_duration']}", styles['BodysText']))
flowables.append(Paragraph(f"We've been long distance for {stats['percentage_long_distance']}% of our relationship", styles['BodysText']))
flowables.append(Spacer(1, 12))

# Time Spent Together
flowables.append(Paragraph("Time Spent Together", styles['CenterHeading']))
flowables.append(Spacer(1, 12))
flowables.append(Paragraph(f"We have been together for {stats['days_together_since_LDR']}", styles['BodysText']))
flowables.append(Paragraph(f"This year we've been together for {stats['days_together_current_year']} days", styles['BodysText']))
flowables.append(Paragraph(f"We usually spend {stats['average_time_together_in_person']} together at time", styles['BodysText']))
flowables.append(Paragraph(f"Per month we see each other {stats['average_days_together_per_month']} times", styles['BodysText']))
flowables.append(Paragraph(f"Since we've been long distance we've spent {stats['percentage_in_person_LDR']}% of our time together", styles['BodysText']))
flowables.append(Spacer(1, 12))

# Time Spent Apart
flowables.append(Paragraph("Time Spent Apart", styles['CenterHeading']))
flowables.append(Spacer(1, 12))
flowables.append(Paragraph(f"On average we go {stats['average_time_between_visits']} between visits", styles['BodysText']))
flowables.append(Paragraph(f"Our longest time apart was {stats['longest_gap_between_meetings']}", styles['BodysText']))
flowables.append(Paragraph(f"Our shortest time apart was {stats['shortest_gap_between_meetings']}", styles['BodysText']))
flowables.append(Paragraph(f"It's been {stats['time_since_last_visit']} since we've last held each other", styles['BodysText']))
flowables.append(Paragraph(f"We'll be in each other's arms in {stats['time_until_next_visit']}", styles['BodysText']))
flowables.append(Spacer(1, 12))

# Travel and Locations
flowables.append(Paragraph("Travel and Locations", styles['CenterHeading']))
flowables.append(Spacer(1, 12))
flowables.append(Paragraph(f"We have been on {stats['total_trips_taken']} trips together", styles['BodysText']))
flowables.append(Paragraph(f"We've visited {stats['number_of_locations_visited']} different places", styles['BodysText']))
flowables.append(Paragraph(f"We most often find each other in {stats['most_visited_city']}", styles['BodysText']))
flowables.append(Spacer(1, 12))

# Gifts and Letters
flowables.append(Paragraph("Gifts and Letters", styles['CenterHeading']))
flowables.append(Spacer(1, 12))
for gift in stats['gift_stats']['recent_gifts_and_letters']:
    flowables.append(Paragraph(f"{gift['for']} was given {gift['description']} on {gift['date_received']}", styles['BodysText']))
flowables.append(Spacer(1, 12))

# Upcoming Events
flowables.append(Paragraph("Upcoming Events", styles['CenterHeading']))
flowables.append(Spacer(1, 12))
for event in stats['event_stats']['upcoming_events']:
    flowables.append(Paragraph(f"Only {event['days_until_event']} days until {event['description']} on {event['date']}", styles['BodysText']))
flowables.append(Spacer(1, 25))

# Love Note
flowables.append(Paragraph("Total love shared: Lots and lots", styles['LoveNote']))

floral_page_template = PageTemplate(id='FloralBordered', frames=[full_page_frame], onPage=add_floral_borders)
doc.addPageTemplates([floral_page_template])
# Finalize and save the PDF
doc.build(flowables)
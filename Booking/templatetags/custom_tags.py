from django import template
from datetime import datetime
from django.utils import timezone
from datetime import timedelta 
import re
from Booking.models import City

register = template.Library()

@register.filter
def map(value, arg):
    """Applies the given attribute to a list of dictionaries."""
    return [getattr(v, arg) for v in value]

@register.filter
def get_item(dictionary, key):
    try:
        return dictionary.get(key)
    except Exception as e:
        return {}


@register.filter
def is_oneway(flight_data):
    try:
        if isinstance(flight_data, dict) and 'data' in flight_data:
            # Check each flight in flight_data['data']
            for flight in flight_data['data']:
                itineraries = flight.get('itineraries', [])
                if len(itineraries) != 1:
                    return False
            return True
    except (TypeError, IndexError):
        return False
    return False


@register.filter
def is_multicity(flight_data):
    
    if not isinstance(flight_data, dict) or 'data' not in flight_data:
        return False
    try:
        for flight in flight_data.get('data', []):
            itineraries = flight.get('itineraries', [])
            if len(itineraries) > 2:
                return False
        return True
    except (TypeError, IndexError):
        return False
    
    
@register.filter
def format_time(value):
    """Format ISO 8601 datetime string to 'H:i'."""
    if not value:
        return 'N/A'
    try:
        dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
        return dt.strftime('%H:%M')
    except ValueError:
        return 'N/A'



@register.filter
def format_date(value):
    """Format ISO 8601 datetime string to 'd M y'."""
    if not value:
        return 'N/A'
    try:
        dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
        return dt.strftime('%d %b %y')
    except ValueError:
        return 'N/A'


@register.filter
def format_date_segment(value):
    """Format ISO 8601 datetime string to 'May 25, 2024'."""
    if not value:
        return 'N/A'
    try:
        dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
        return dt.strftime('%B %d, %Y')
    except ValueError:
        return 'N/A'
    
    
@register.filter
def format_date_short(value):
    """Format ISO 8601 datetime string to '30 Jan 25'."""
    if not value:
        return 'N/A'
    try:
        dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
        return dt.strftime('%d %b %y')
    except ValueError:
        return 'N/A'
    
    
@register.filter
def format_time_segment(value):
    """Format ISO 8601 datetime string to 'h:i AM/PM'."""
    if not value:
        return 'N/A'
    try:
        dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
        return dt.strftime('%I:%M %p')
    except ValueError:
        return 'N/A'
    
    


@register.filter(name='format_duration')
def format_duration(duration):
    hours = re.search(r'(\d+)H', duration)
    minutes = re.search(r'(\d+)M', duration)
    
    hours_str = f"{int(hours.group(1))}hr" if hours else ""
    minutes_str = f"{int(minutes.group(1))}min" if minutes else ""
    
    return f"{hours_str} {minutes_str}".strip()


@register.filter
def format_dob(value):
    """Format ISO 8601 date string to 'd M Y'."""
    if not value:
        return 'N/A'
    try:
        dt = datetime.strptime(value, '%Y-%m-%d')
        return dt.strftime('%d %b %Y')
    except ValueError:
        return 'N/A'


@register.filter
def get_city_name(airport_code):
    try:
        city = City.objects.get(airport_code=airport_code)
        return city.city_name
    except City.DoesNotExist:
        return None

@register.filter
def get_airport_name(airport_code):
    try:
        airport = City.objects.get(airport_code=airport_code)
        return airport.airport
    except City.DoesNotExist:
        return None
    
    
@register.filter
def format_price(price):
    try:
        # Convert price to float if it's not already
        price = float(price)
        # Format the price with commas
        formatted_price = "{:,.2f}".format(price)
        return formatted_price
    except (ValueError, TypeError):
        # Handle cases where conversion fails
        return price
    
    

# @register.filter
# def remove_dashes(text):
#     """
#     Custom template filter to remove lines containing more than two consecutive dashes ('--')
#     or more than two consecutive dots ('..') from the text.
#     """
#     def has_excessive_repeats(line):
#         return re.search(r'(-{3,}|\.{3,})', line)

#     return "\n".join(
#         line for line in text.splitlines()
#         if not has_excessive_repeats(line)
#     )


@register.filter
def remove_dashes(text):
    """
    Custom template filter to remove lines containing more than two consecutive dashes ('--')
    or more than two consecutive dots ('..') from the text, and add a new line after removal.
    """
    def replace_excessive_repeats(line):
        # Replace 3 or more dashes or dots with a newline
        return re.sub(r'(-{3,}|\.{3,})', '\n', line)

    # Split the text into lines, process each line, and join the result with a newline.
    return "\n".join(
        replace_excessive_repeats(line) for line in text.splitlines()
    )



@register.filter
def booking_expiry_date(value):
    try:
        # Parse the date string assuming the format is 'YYYY-MM-DD'
        date_obj = datetime.strptime(value, '%Y-%m-%d')
        # Format the date to 'Month Day, Year'
        return date_obj.strftime('%b. %d, %Y')
    except ValueError:
        return value
    

    
@register.filter
def strip_country_code(phone_number):
    if phone_number and len(phone_number) > 4:
        # Remove the first 4 characters (country code)
        return phone_number[4:]
    return phone_number


@register.filter
def chat_time(value):
    """
    Takes a datetime object and returns only the time part in the format '10:55 a.m.'.
    """
    if isinstance(value, datetime):
        # Return the formatted time if the value is already a datetime object
        return value.strftime('%I:%M %p')
    else:
        # Return the original value if it's not a datetime object
        return value

@register.filter
def chat_date(value):
    """
    Takes a datetime object and returns only the date part in the format 'September 11, 2024'.
    """
    if isinstance(value, datetime):
        # Return the formatted date if the value is already a datetime object
        return value.strftime('%B %d, %Y')
    else:
        # Return the original value if it's not a datetime object
        return value

    
@register.filter
def multiply(value, arg):
    return value * arg


@register.simple_tag
def define(val=None):
  return val



@register.filter
def custom_date_format(value):
    if not value:
        return ''
    
    # Get the current date and time
    now = timezone.now()
    
    # If the date is today, return only the time (e.g., 14:05)
    if value.date() == now.date():
        return value.strftime('%H:%M')
    
    # If the date is yesterday, return 'Yesterday'
    elif value.date() == (now - timedelta(days=1)).date():  # Correct timedelta import
        return 'Yesterday'
    
    # If the date is older than yesterday, return the date in 'd M Y' format (e.g., 12 Sep 2024)
    else:
        return value.strftime('%d %b %Y')
    
    
@register.filter
def first_name(value):
    """
    Extracts and returns the first name from a full name string.
    Example: "HYCENTH ARINZE" -> "HYCENTH"
    """
    # Split the string by space and return the first part
    return value.split()[0] if value else ''


@register.filter(name='format_underscore')
def format_underscore(value):
    """
    Converts 'base_fare' to 'Base Fare' by replacing underscores with spaces and capitalizing each word.
    """
    return value.replace('_', ' ').title()




@register.filter
def custom_date_format_chat(value):
    if not value:
        return ''
    
    # Get the current date and time
    now = timezone.now()
    
    # If the date is today, return only the time with AM/PM (e.g., 2:05 PM)
    if value.date() == now.date():
        return value.strftime('%I:%M %p')  # Changed to 12-hour format with AM/PM
    
    # If the date is yesterday, return 'Yesterday'
    elif value.date() == (now - timedelta(days=1)).date():
        return 'Yesterday'
    
    # If the date is older than yesterday, return the date in 'd M Y' format (e.g., 12 Sep 2024)
    else:
        return value.strftime('%d %b %Y')


@register.filter
def to_dict(value):
    print(value)
    # If the value is already a dictionary, return it
    if isinstance(value, dict):
        return value
    # Convert the value to a dictionary if it's not already one
    try:
        return dict(value)
    except (ValueError, TypeError):
        return {}  # Return an empty dict if conversion fails


# Custom filter to convert segments to a list of dictionaries
@register.filter
def to_list_of_dict(value):
    # Check if the value is a list and each item in the list is a dictionary
    if isinstance(value, list) and all(isinstance(item, dict) for item in value):
        return value  # Already a list of dictionaries, return as is

    # Handle other possible data types
    try:
        # Attempt to convert the value to a list of dicts if not already
        return list(value)
    except (ValueError, TypeError):
        return []  # Return an empty list if conversion fails
    
    
@register.filter
def get_payment_plan(value):
    payment_case = {
        'nextday': "Next Day",
        'oneweek': "1 Week",
        'twoweek': "2 Weeks",
        'threeweek': "3 Weeks",
        'onemonths': "1 Month",
        'twomonths': "2 Months"
    }
    return payment_case[value]


@register.filter
def extract_prefixes(value):
    """
    Extracts the first three characters from each comma-separated item in the input string.

    Args:
        value (str): A comma-separated string like "SHR1S28AA,ACCG828TY,LONU128XJ,LOSN828HJ".

    Returns:
        str: A comma-separated string containing the first three characters of each item, e.g., "SHR, ACC, LON, LOS".
    """
    if not value:
        return ""
    
    # Split the input string by commas and strip whitespace from each item
    items = [item.strip() for item in value.split(",")]
    
    # Extract the first 3 characters of each item if it has at least 3 characters
    prefixes = [item[:3] for item in items if len(item) >= 3]
    
    # Join the prefixes with commas
    return ", ".join(prefixes)



@register.filter
def first_three(value):
    """
    Custom filter to extract the first three characters of a string.
    """
    if isinstance(value, str):
        return value[:3]  # Return the first three characters
    return value  


@register.filter
def split(value, delimiter=','):
    """Splits a string by the given delimiter."""
    return value.split(delimiter) if value else []


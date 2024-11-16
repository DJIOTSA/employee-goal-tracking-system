from datetime import datetime, timedelta

# def get_current_week():
#   """
#   This function returns the current week as a tuple of two dates,
#   representing the start and end of the week.
#   """
#   today = datetime.today()
#   # Get the weekday (0 = Monday, 6 = Sunday)
#   weekday = today.weekday()
#   # Calculate the offset to get to Monday
#   offset = timedelta(days=-weekday)
#   # Get the start and end of the week
#   start_of_week = today + offset
#   end_of_week = start_of_week + timedelta(days=6)
#   return start_of_week, end_of_week


def get_current_week():
    """
    This function returns the current week as a tuple of three elements:
    - Start date of the week
    - End date of the week
    - Week number
    """
    today = datetime.today()
    # Get the weekday (0 = Monday, 6 = Sunday)
    weekday = today.weekday()
    # Calculate the offset to get to Monday
    offset = timedelta(days=-weekday)
    # Get the start and end of the week
    start_of_week = today + offset
    end_of_week = start_of_week + timedelta(days=6)
    # Get the week number
    week_number = today.isocalendar()[1]
    #   return start_of_week, end_of_week, week_number
    return {
       'start_of_week': start_of_week,
       'end_of_week': end_of_week,
       'week_number': week_number
    }


def get_week(date: datetime):
    # Get the weekday (0 = Monday, 6 = Sunday)
    weekday = date.weekday()
    # Calculate the offset to get to Monday
    offset = timedelta(days=-weekday)
    # Get the start and end of the week
    start_of_week = date + offset
    end_of_week = start_of_week + timedelta(days=6)
    # Get the week number
    week_number = date.isocalendar()[1]

    return start_of_week, end_of_week, week_number
    

# # Get the current week
# current_week_start, current_week_end, number = get_current_week()

# Print the current week
# print(f"Current week: {current_week_start.strftime('%Y-%m-%d')} to {current_week_end.strftime('%Y-%m-%d')}")

from django.utils import timezone

def is_event_in_current_week(event_start_date, event_end_date):
    """
    This function checks if an event falls within the current week.
    """
    week=get_current_week()
    current_week_start =  week['start_of_week']
    current_week_end = week['end_of_week']
    number = week['week_number']
    return (event_start_date >= current_week_start and event_start_date <= current_week_end) or \
           (event_end_date >= current_week_start and event_end_date <= current_week_end) or \
           (event_start_date <= current_week_start and event_end_date >= current_week_end)

# Example usage
# event_start_date = datetime.today() + timedelta(days=0)
# event_end_date = event_start_date + timedelta(2)
# print(event_start_date)
# print(is_event_in_current_week(timezone.now(), event_end_date))


def display_current_week_dates():
    """
    This function displays all the dates of the current week.
    """
    current_week_start, current_week_end, number = get_current_week()
    current_day = current_week_start
    i = 0
    week_days = {}
    while current_day <= current_week_end:
        day = {current_day.strftime("%Y-%m-%d"): 0}
        week_days.update(day)
        i+=1
        current_day += timedelta(days=1)

    return {
       'week_number': number,
       'week_days': week_days,
    }

def get_week(date: datetime):
    # Get the weekday (0 = Monday, 6 = Sunday)
    weekday = date.weekday()
    # Calculate the offset to get to Monday
    offset = timedelta(days=-weekday)
    # Get the start and end of the week
    start_of_week = date + offset
    end_of_week = start_of_week + timedelta(days=6)
    # Get the week number
    week_number = date.isocalendar()[1]

    return start_of_week, end_of_week, week_number
 
def get_week_days(date: datetime):
    """
    This function displays all the dates of the date week.
    """
    week_start, week_end, number = get_week(date)
    day = week_start
    i = 0

    week_days = {}
    while day <= week_end:
        week_days[day.strftime("%Y-%m-%d")] = []
        i+=1
        day += timedelta(days=1)

    return number, week_days
# week_number, days = get_week_days(datetime.now())
# print(week_number, days)
  
# def get_current_month_week_numbers():
#   """
#   This function returns a list of all week numbers in the current month.
#   """
#   today = datetime.today()
#   # Get the first and last day of the current month
#   first_day_of_month = today.replace(day=1)
#   last_day_of_month = first_day_of_month + timedelta(days=31)
#   # Initialize an empty list to store week numbers
#   week_numbers = []
#   # Loop through each day of the month
#   current_day = first_day_of_month
#   while current_day <= last_day_of_month:
#     # Get the week number for the current day
#     week_number = current_day.isocalendar()[1]
#     # Add the week number to the list if it's not already present
#     if week_number not in week_numbers:
#       week_numbers.append(week_number)
#     # Move to the next day
#     current_day += timedelta(days=1)
#   return week_numbers
def get_current_month_info():
  """
  This function returns a dictionary containing information about the current month,
  including the month number and a list of all week numbers.
  """
  today = datetime.today()
  # Get the month number and first day of the month
  month_number = today.month
  first_day_of_month = today.replace(day=1)
  last_day_of_month = first_day_of_month + timedelta(days=31)
  # Initialize an empty list to store week numbers
  week_numbers = []
  # Loop through each day of the month
  current_day = first_day_of_month
  while current_day <= last_day_of_month:
    # Get the week number for the current day
    week_number = current_day.isocalendar()[1]
    # Add the week number to the list if it's not already present
    if week_number not in week_numbers:
      week_numbers.append(week_number)
    # Move to the next day
    current_day += timedelta(days=1)
  # Return a dictionary with month number and week numbers
  return {
    "month_number": month_number,
    "week_numbers": week_numbers
  }


# Get the information about the current month
# current_month_info = get_current_month_info()

# # Print the month number and week numbers
# print(f"Month number: {current_month_info['month_number']}")
# print(f"Week numbers: {current_month_info['week_numbers']}")

def get_current_year_and_months():
    """
    This function returns a list of month names and the current year.
    """
    current_year = datetime.today().year
    month_names = {
        "January": 0, 
        "February": 0, 
        "March": 0, 
        "April": 0, 
        "May": 0, 
        "June": 0,
        "July": 0, 
        "August": 0, 
        "September": 0, 
        "October": 0, 
        "November": 0, 
        "December": 0,
    }
    return {
      'current_year': current_year,
      'months': month_names
    }

# Get the list of months and current year
# year_infos = get_current_year_and_months()

# print(f"Current year: {year_infos}")
# print(f"months: {year_infos['months']}")

def get_date_week_number(date):
    #  take a date as parameter and return it's week number
    week_number = date.isocalendar()[1]
    return week_number

# week_num = get_date_week_number(datetime(2022,12,26))
# print("###############################################")
# print(week_num)
# print("__________________________________________")

import datetime


def get_weeks_in_year(year):
    """ 
    This function take an integer year number as parameter and return a 
    dictionary containing all week number of the year as dictionary key and 
    a list of starting and ending date of each week number as values of each key

    example:
    --------
    weeks = get_weeks_in_year(2024)
    print(weeks) =

    {
    1: ['2024-01-01', '2024-01-07'],
    2: ['2024-01-08', '2024-01-14'],
    . . .
    . . .
    . . .
    52: ['2022-12-26', '2023-01-01'],
    }

    """
    weeks = {}
    data = {}

    start_date = datetime.date(year, 1, 1)
    end_date = datetime.date(year, 12, 31)
    week_num = start_date.isocalendar()[1]
    x = start_date
    while start_date < end_date:
        week_start = start_date - datetime.timedelta(days=start_date.weekday())
        week_end = week_start + datetime.timedelta(days=6)
        if week_num not in weeks:
            weeks[week_num] = [week_start.strftime('%Y-%m-%d'), week_end.strftime('%Y-%m-%d')]
        
        start_date += datetime.timedelta(days=7)

        if week_num >= 51:
            x = get_date_week_number(start_date)
            if x == 1:
                week_num = 0
            if x >= 51:
                # if x not in weeks:
                #     print(x)
                #     ws = start_date - datetime.timedelta(days=start_date.weekday())
                #     we = ws + datetime.timedelta(days=6)
                #     data[x] = [ws.strftime('%Y-%m-%d'), we.strftime('%Y-%m-%d')]
                pass
                    
        week_num += 1
        
    return weeks, data


# print("+++++++++++++++++++++++++++++++++++++++++++++++")
# print()
# weeks, data = get_weeks_in_year(2022)

# print(data)
# print(weeks)
# print()

from datetime import datetime
def get_date_from_string_date(date: str):
    
    a = date.count("-")
    b = date.count("/")
    if a == 2:
        x = date.split("-")
        year    = int(x[0])
        month   = int(x[1])
        day     = int(x[2])
    if b == 2:
        x = date.split("/")
        year    = int(x[2])
        month   = int(x[0])
        day     = int(x[1])
    
    return datetime(year, month, day)
    

# print(get_date_from_string_date("2024-01-22"))
# print(get_date_from_string_date("01/22/2024"))


# date = datetime.today().astimezone().year
# print(date)

from datetime import datetime, timedelta


def get_month_info(year, month_number):
  """
  This function returns a list containing information about a given month,
  handling invalid year and month numbers gracefully.

  Args:
    year: The year of the month to analyze (as an integer range[2024-9999]).
    month_number: The month number to analyze (can be outside 1-12).

  Returns:
    A list of week numbers,
    or an empty dictionary if the month number is invalid.
  """

  # Validate month number
  if not 1 <= month_number <= 12 or year < 2024 or year > 9999:
    return []  # Return empty dictionary for invalid month numbers

  # Create a datetime object for the first day of the specified month
  first_day_of_month = datetime(year, month_number, 1)

  # Calculate the last day of the month accurately
  last_day_of_month = (first_day_of_month + timedelta(days=31)).replace(day=1) - timedelta(days=1)

  # Initialize an empty list to store week numbers
  week_numbers = []

  # Loop through each day of the month
  current_day = first_day_of_month
  while current_day <= last_day_of_month:
    # Get the week number for the current day
    week_number = current_day.isocalendar()[1]
    # Add the week number to the list if it's not already present
    if week_number not in week_numbers:
      week_numbers.append(week_number)
    # Move to the next day
    current_day += timedelta(days=1)

  # Return a list of week numbers
  return week_numbers

def get_month_info(year, month_number):
    """
    This function returns a list containing information about a given month,
    handling invalid year and month numbers gracefully.

    Args:
      year: The year of the month to analyze (as an integer range[2024-9999]).
      month_number: The month number to analyze (can be outside 1-12).

    Returns:
      A list of week numbers,
      or an empty dictionary if the month number is invalid.
    """

    # Validate month number
    if not 1 <= month_number <= 12 or year < 2024 or year > 9999:
      return []  # Return empty dictionary for invalid month numbers

    # Create a datetime object for the first day of the specified month
    first_day_of_month = datetime(year, month_number, 1)

    # Calculate the last day of the month accurately
    last_day_of_month = (first_day_of_month + timedelta(days=31)).replace(day=1) - timedelta(days=1)

    # Initialize an empty list to store week numbers
    week_numbers = []

    # Loop through each day of the month
    current_day = first_day_of_month
    while current_day <= last_day_of_month:
        # Get the week number for the current day
        week_number = current_day.isocalendar()[1]
        # Add the week number to the list if it's not already present
        if week_number not in week_numbers:
            week_numbers.append(week_number)
        # Move to the next day
        current_day += timedelta(days=1)

    # Return a list of week numbers
    return week_numbers

# print(get_month_info(2024,1))

def get_week_days_by_year_week(year: int, week_number: int) -> list:
    """
    Returns a list of days in a given week, specified by year and week number.

    Args:
        year (int): The year of the week.
        week_number (int): The number of the week within the year.

    Returns:
        list: A list of datetime objects representing the days of that week.
    """

    # Create a datetime object for the first day of the week
    # Assuming Monday is the first day of the week
    monday_of_week = datetime.strptime(f"{year}-W{week_number}-1", "%Y-W%W-%w")

    # Get the week days using the provided function
    number, week_days = get_week_days(monday_of_week)

    # Extract a list of days from the resulting dictionary
    list_of_days = list(week_days.keys())

    return list_of_days

print(get_week_days_by_year_week(2023,1))

def get_year_week_numbers(year: int) -> list:
    """
    Returns a list of week numbers within a given year.

    Args:
        year (int): The year for which to generate week numbers.

    Returns:
        list: A list of integers representing the week numbers of that year.
    """

    week_numbers = []

    # Start with the first day of the year
    current_date = datetime(year=year, month=1, day=1)

    # Iterate through the year, getting week numbers until reaching the next year
    while current_date.year == year:
        # Get the week number directly using isocalendar
        week_number = current_date.isocalendar()[1]

        # Add the week number to the list if it's not already there
        if week_number not in week_numbers:
            week_numbers.append(week_number)

        # Move to the next week
        current_date += timedelta(days=7)

    return week_numbers

# print(get_year_week_numbers(2020))



import datetime

def is_event_in_week(event_start_date, event_end_date, year: int, month: int, week: int):
    """
    Checks if an event falls within a given week.

    Args:
        event_start_date (datetime.date): Start date of the event.
        event_end_date (datetime.date): End date of the event.
        year (int): Year of the week to check.
        month (int): Month of the week to check (optional, for clarity).
        week (int): Week number of the year to check.

    Returns:
        bool: True if the event overlaps with the given week, False otherwise.
    """

    # Get the Monday of the specified week
    monday_of_week = datetime.date(year, month, 1)  # Start with the first day of the month
    monday_of_week += datetime.timedelta(days=((week - 1) * 7 + (monday_of_week.weekday() + 1) % 7))  # Adjust to the Monday of the target week

    # Get the Sunday of the specified week
    sunday_of_week = monday_of_week + datetime.timedelta(days=6)

    # Check for overlap between event dates and week range
    return (
        event_start_date <= sunday_of_week and event_end_date >= monday_of_week
    )  # True if the event starts before or on Sunday and ends on or after Monday


# prev_starting_date = datetime.date(2025, 1,29)
# print(prev_starting_date)
# next_starting_date = prev_starting_date + timedelta(days=1)
# print(next_starting_date)
# next_starting_date = prev_starting_date + timedelta(weeks=1)
# print(next_starting_date)
# next_starting_date = prev_starting_date.replace(month=prev_starting_date.month + 1)
# print(next_starting_date)
    

from datetime import datetime, timedelta

def add_one_month(current_date):
    # Calculate the next month
    year = current_date.year + (current_date.month // 12)
    month = current_date.month % 12 + 1

    # Handle leap year
    if month == 2 and current_date.day == 29:
        day = 29 if (year % 4 == 0 and year % 100 != 0) or year % 400 == 0 else 28
    else:
        day = min(current_date.day, [31, 29 if (year % 4 == 0 and year % 100 != 0) or year % 400 == 0 else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1])

    return current_date.replace(year=year, month=month, day=day)

current_date = datetime(2025,2,28) #datetime.now()

# one_day_later = current_date + timedelta(days=1)
# one_week_later = current_date + timedelta(weeks=1)
# one_month_later = add_one_month(current_date)

# print("Current date:", current_date)
# print("One day later:", one_day_later)
# print("One week later:", one_week_later)
# print("One month later:", one_month_later)

# text_list = "[1,3,4,et,rer,re,rere,re,5,5,6,6,6]"
# new_list = text_list[1:len(text_list)-1]
# new_list = [int(i) for i in new_list.split(",") if int(i) in range(1, 1000000000)]

# print(type(new_list[1]))
# print(f"text_list: {text_list}")

# print(f"new list{new_list}")


import re

def extract_numbers(text:str):
    """Extracts all non-zero numbers from a string and returns them as a list."""
    if text is None:
        return []
    text = str(text)
    numbers = re.findall(r"\d+", text)  # Match digits
    return [int(num) for num in numbers if num != "0"]  # Convert and filter


extracted_numbers = extract_numbers(input_string)
print(extracted_numbers)  # Output: [35, 4, 45, 5, 545, 4, 4, 3, 7, 87, 8]

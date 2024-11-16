from django.db import models
from EGT.models import (Employee, Enterprise)
from django.utils.translation import gettext_lazy as _
from tasks.models import Report, Goal, Activities, TaskCompletionStatus, ReportStatus
from django.db.models.signals import post_save
from django.dispatch import receiver

import json
from datetime import datetime, timedelta
# Define default value of report option
ACTIVITY = 'A'
GOAL = 'G'

""" ################################ FUNCTIONS ###########################################"""

def is_valid_date_format(date_string:str):
    
    """
    Checks if the given string is in a valid date format (%Y-%m-%d or %m/%d/%y).

    Args:
        date_string: The string to be checked.

    Returns:
        True if the string is in a valid date format, False otherwise.
    """
    try:
        # Try parsing with both formats
        datetime.strptime(date_string, "%Y-%m-%d")
        return True
    except ValueError as e:
        pass
    try:
        datetime.strptime(date_string, "%m/%d/%Y")
        return True
    except ValueError:
        pass
    return False


def get_date_from_string_date(date: str):
    """ 
    Take a string date and return a datetime date.
    string date format: %Y-%m-%d or %m/%d/%Y
    """
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
    return datetime(year, month, day).astimezone()


def set_average_rate(average: int):
    """ Return the corresponding rate of a list of rate. """
    if average < 100:
        return 0
    elif average >=100 and average < 200:
        return 100
    elif average >=200 and average <300:
        return 200
    elif average >=300 and average <400:
        return 300
    elif average >=400 and average <500:
        return 400
    elif average == 500:
        return average
    
    
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
       'start_day_of_week': start_of_week,
       'end_day_of_week': end_of_week,
       'week_number': week_number
    }


def is_event_in_current_week(event_start_date, event_end_date):
    """
    This function checks if an event falls within the current week.
    """
    current_week_start, current_week_end, number = get_current_week()
    return (event_start_date >= current_week_start and event_start_date <= current_week_end) or \
           (event_end_date >= current_week_start and event_end_date <= current_week_end) or \
           (event_start_date <= current_week_start and event_end_date >= current_week_end)


def get_date_week_number(date):
    """take a date as parameter and return it's week number"""
    week_number = date.isocalendar()[1]
    return week_number


def get_current_week_dates():
    """
    This function displays all the dates of the current week.
    This function returns:
    -   week number
    -   week_days
    """
    current_week_start, current_week_end, number = get_current_week()
    current_day = current_week_start
    i = 0
    week_days = {}
    while current_day <= current_week_end:
        day = {current_day.strftime("%y-%m-%d"): 0}
        week_days.update(day)
        current_day += timedelta(days=1)

    return {
       'week_number': number,
       'week_days': week_days,
    }


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


def get_current_year_and_months():
    """
    This function returns a list of month names and the current year.
    """
    current_year = datetime.today().year
    month_names = {
        1: 0, 
        3: 0, 
        4: 0, 
        5: 0, 
        6: 0,
        7: 0, 
        8: 0, 
        9: 0, 
        10: 0, 
        11: 0, 
        12: 0,
    }
    
    return {
      'current_year': current_year,
      'months': month_names
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
    This function take a dates as argument and
    return it's week number including all
    the dates of that week.

    example: week_number, week_days = get_week_dates(date)
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
    start_date = datetime.date(year, 1, 1)
    end_date = datetime.date(year, 12, 31)
    week_num = start_date.isocalendar()[1]
    x = start_date
    while start_date < end_date:
        week_start = start_date - datetime.timedelta(days=start_date.weekday())
        week_end = week_start + datetime.timedelta(days=6)
        if week_num not in weeks:
            weeks[week_num] = [week_start.strftime('%Y-%m-%d'), week_end.strftime('%Y-%m-%d')]
        if week_num == 52:
            week_num = 0
        start_date += datetime.timedelta(days=7)
        
        week_num += 1
        
    return weeks


""" ################################### MODEL CLASSES ###################################### """
class Rate(models.IntegerChoices):
    NULL = 0, 'Null'
    ACCEPTABLE = 100, 'Acceptable'
    GOOD = 200, 'Good'
    VERY_GOOD = 300, 'Very Good'
    EXCELLENT = 400, 'Excellent'
    PERFECT = 500, 'Perfect'

def get_goal_progress(goal: Goal):
    """ 
    Return goal progress percentage on 100 
    to get the percentage of progress of a goal
    we are going to use the total number of report that must be 
    mark as completed (all the user who are amount users_in_charge of each activity are taking in
    consideration).

    The finale percentage is get by calculating the total number of submit and validated reports on the 
    required validated report to get 100%(100 progress)

    Return a tuple of integer
    return (required_reports_number, percentage, done_activity_reports_number, submit_activity_reports_number, non_submit_activity_reports_num)
    
    """
    queryset_a = Activities.objects.filter(goal=goal)
    required_reports = 0
    done_report = 0
    report_list = []
    done_activity_reports = 0
    submit_activity_reports = 0
    non_submit_activity_reports = 0
    percentage = 0

    if not queryset_a:
        required_reports = 1
        try:
            report = Report.objects.get(option=GOAL, goal=goal)
            if report.rate in [100, 200, 300, 400, 500]:
                percentage = 100
                
            return required_reports, percentage, done_activity_reports, submit_activity_reports, non_submit_activity_reports
        except Report.DoesNotExist:
            return required_reports, percentage, done_activity_reports, submit_activity_reports, non_submit_activity_reports

    # analysis
    for a in queryset_a:
        try:
            required_reports += a.employees.all().count()
            reports_for_a = Report.objects.filter(activity=a) if Report.objects.filter(activity=a).exists() else []
            if reports_for_a:
                report_list.extend(reports_for_a)
            done_activity_reports+=reports_for_a.filter(rate__in =[100,200,300,400,500]).count()
            submit_activity_reports += a.submit_employees.all().count()
        except:
            pass

    
    total = required_reports if required_reports >=1 else 1
    # get percentage
    percentage = int((100*done_report)/total)
    # get non submit report number
    non_submit_activity_reports = required_reports -done_activity_reports - submit_activity_reports

    return required_reports, percentage, done_activity_reports, submit_activity_reports, non_submit_activity_reports


from datetime import date, timedelta
from calendar import day_abbr

def is_event_in_week(event_start_date: date, event_end_date: date, year: int, month: int, week_number: int) -> bool:
    """
    Checks if an event falls within a given year, month, and week.

    Args:
        event_start_date: Start date of the event (datetime.date).
        event_end_date: End date of the event (datetime.date).
        year: Target year.
        month: Target month.
        week_number: Target week number.

    Returns:
        True if the event overlaps with the specified year, month, and week, False otherwise.
    """

    # Get the first day of the target week
    first_day_of_week = date(year, month, 1) + timedelta(days=(week_number - 1) * 7)
    first_day_of_week -= timedelta(days=first_day_of_week.weekday())  # Adjust to Monday

    # Get the last day of the target week
    last_day_of_week = first_day_of_week + timedelta(days=6)

    # Check for overlap between event dates and week range
    return (
        event_start_date <= last_day_of_week and event_end_date >= first_day_of_week
    )



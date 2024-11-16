from django.shortcuts import render
from .serializers import (
    DaySerializer,
    PerformanceSerializer,
    PerformanceMonthSerializer,
    PerformanceYearSerializer,
    PerformanceGoalSerializer,
    DayActivitiesSerializer,
    UserStatisticsSerializer,
    UserWeekStatisticsSerializer,
    UserMonthStatisticsSerializer,
    UserYearStatisticsSerializer,
    
    
    
)
from tasks.serializers import GoalSerializerList, ActivitiesListSerializer, ReportListSerializer, ActivitySerializerLink, GoalSerializerLink
from .models import(
    get_date_from_string_date,
    get_date_week_number,
    get_month_info,
    get_week_days_by_year_week,
    get_year_week_numbers,
    set_average_rate,
    get_goal_progress,
    is_event_in_week,
    is_valid_date_format,
    ACTIVITY,
    GOAL,
)

from django.db.models import Q
import json

from EGT.models import (
    check_user_enterprise_status,
    user_belong_to_enterprise,
    Enterprise,
    Status,
)


from datetime import datetime, timedelta
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

from tasks.models import (
    Report,
    Activities,
    Goal,
    Activities,
    is_user_in_charge_of_activity,
    is_user_in_charge_of_goal,
    is_event_in_current_week,
)
from tasks.serializers import ActivitiesListSerializer
from EGT.serializers import UserSerializer
from EGT.permissions import (
    checkAdministratorGroupMixin,
    checkEmployeeAdminGroupMixin,
    checkAdministratorEmployeeGroupMixin,
    PermissionDenied,
    IS_EMPLOYEE_ADMIN,
)
from rest_framework import generics
from rest_framework.views import Response, APIView
from rest_framework.exceptions import status
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination

ADMINISTRATOR = 'ADMINISTRATOR'
EMPLOYEE = 'EMPLOYEE'


def convert_string_to_int(string_number):
    """
    Converts a string to an integer if it contains only numbers, otherwise returns None.

    Args:
        string_number: The string to be converted.

    Returns:
        The integer value of the string if it's a valid number, otherwise None.
    """
    try:
        return int(string_number)
    except ValueError:
        return None


"""
    \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
    DayStatistic VIEW SECTION
"""

class DayFinishActivities(generics.ListAPIView):
    """ This  view get all the finish activities of the current day """
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated,]
    queryset = Report.objects.all()
    pagination_class = PageNumberPagination
    serializer_class = ReportListSerializer
    lookup_field= "pk"

    def get(self, request, format=None):
        # check user authentication group
        checkAdministratorEmployeeGroupMixin(self)
    
        #  get serializer data
        enterprise_name = request.GET.get('enterprise_name', '').upper()        

        # check enterprise existence
        try:
            enterprise = Enterprise.objects.get(name= enterprise_name)
        except Enterprise.DoesNotExist:
            content = {'detail': _(f"{enterprise_name} does not exists!")}
            return Response(content, status= status.HTTP_400_BAD_REQUEST)
        
        # check user and enterprise relationship
        if not user_belong_to_enterprise(request.user, enterprise):
            raise PermissionDenied
        if check_user_enterprise_status(request.user, enterprise) not in [Status.ACTIVE]:
            raise PermissionDenied
        
        reports = []
        try:
            #  check if the the record 
            for report in Report.objects.filter(option=ACTIVITY):
                date = report.date_of_submission.strftime("%y-%m-%d")
                today = datetime.today().strftime("%y-%m-%d")
                if date == today and is_user_in_charge_of_activity(request.user, report.activity) and report.activity.goal.enterprise == enterprise and report.rate in [100, 200, 300, 400, 500]:
                    reports.append(report.id)

            queryset = Report.objects.filter(id__in = reports)
            page = self.paginate_queryset(queryset)  # Apply pagination logic

            if page is not None:
                serializer = self.serializer_class(page, context={"request": request},  many=True)
                return self.get_paginated_response(serializer.data)
        except Exception as e:
            content = {"error": _(f"An error occur: {e}")}
            return Response(content, status.HTTP_400_BAD_REQUEST)
            

class DayUnFinishActivities(generics.ListAPIView):
    """ This  view get all un-finish activities related to the user"""
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated,]
    queryset = Activities.objects.all()
    pagination_class = PageNumberPagination
    lookup_field= "pk"
    serializer_class = ActivitiesListSerializer

    def get(self, request, format=None):
        # check user authentication group
        checkAdministratorEmployeeGroupMixin(self)
        
        
        #  get serializer data
        enterprise_name = request.GET.get('enterprise_name', '').upper()

        # check enterprise existence
        try:
            enterprise = Enterprise.objects.get(name= enterprise_name)
        except Enterprise.DoesNotExist:
            content = {'detail': _(f"{enterprise_name} does not exists!")}
            return Response(content, status= status.HTTP_400_BAD_REQUEST)
        
        # check user and enterprise relationship
        if not user_belong_to_enterprise(request.user, enterprise):
            raise PermissionDenied
        if check_user_enterprise_status(request.user, enterprise) in [Status.DEACTIVATED, Status.SUSPENDED, None]:
            raise PermissionDenied
        
        activities = []
        try:
            for activity in Activities.objects.filter(Q(goal__enterprise=enterprise)):
                start = activity.starting_date
                end = activity.ending_date
                
                today = datetime.today().astimezone() 
                if is_event_in_current_week(start, end):
                    if today >= start and today<=end and is_user_in_charge_of_activity(request.user, activity)==True:
                        # if Report.objects.filter()
                        activities.append(activity.id)
                    
            queryset =  Activities.objects.filter(id__in= activities)

            # get pagination logic
            page = self.paginate_queryset(queryset)

            if page is not None:
                serializer = self.serializer_class(page, context={"request": request}, many= True)
                return self.get_paginated_response(serializer.data)

        except Exception as e:
            content = {"error": _(f"An error occur: {e}")}
            return Response(content, status.HTTP_400_BAD_REQUEST)    
    

class DayFinishGoals( generics.ListAPIView):
    """ This  view get all completed goal of the current day """
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated,]
    queryset = Report.objects.all()
    pagination_class = PageNumberPagination
    lookup_field= "pk"
    serializer_class =ReportListSerializer

    def get(self, request, format=None):
        # check user authentication group
        checkAdministratorEmployeeGroupMixin(self)
        
        #  get serializer data
        enterprise_name = request.GET.get('enterprise_name', '').upper()

        # check enterprise existence
        try:
            enterprise = Enterprise.objects.get(name= enterprise_name)
        except Enterprise.DoesNotExist:
            content = {'detail': _(f"{enterprise_name} does not exists!")}
            return Response(content, status= status.HTTP_400_BAD_REQUEST)
        
        # check user and enterprise relationship
        if not user_belong_to_enterprise(request.user, enterprise):
            raise PermissionDenied
        if check_user_enterprise_status(request.user, enterprise) in [Status.DEACTIVATED, Status.SUSPENDED, None]:
            raise PermissionDenied
        
        reports = []
       
        try:
            #  check if the the record 
            for report in Report.objects.filter(Q(option=GOAL)):
                date = report.date_of_submission.strftime("%y-%m-%d")
                today = datetime.today().strftime("%y-%m-%d")
                if date == today and is_user_in_charge_of_goal(request.user, report.goal) and report.goal.enterprise == enterprise and report.rate in [100, 200, 300, 400, 500]:
                    reports.append(report.id)

            queryset  = Report.objects.filter(id__in = reports)
            # pagination logic
            page = self.paginate_queryset(queryset)

            if page is not None:
                serializer = self.serializer_class(page, context={"request": request}, many=True)
                return self.get_paginated_response(serializer.data)

        except Exception as e:
            content = {"error": _(f"An error occur: {e}")}
            return Response(content, status.HTTP_400_BAD_REQUEST)        
    

class DayUnFinishGoals( generics.ListAPIView):
    """ This  view get all un-finish goal of the day """
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated,]
    queryset = Goal.objects.all()
    serializer_class = GoalSerializerList
    lookup_field = "pk"
    pagination_class = PageNumberPagination


    def get(self, request, format=None):
        # check user authentication group
        checkAdministratorEmployeeGroupMixin(self)
        
        #  get serializer data
        enterprise_name = request.GET.get('enterprise_name', '').upper()

        # check enterprise existence
        try:
            enterprise = Enterprise.objects.get(name= enterprise_name)
        except Enterprise.DoesNotExist:
            content = {'detail': _(f"{enterprise_name} does not exists!")}
            return Response(content, status= status.HTTP_400_BAD_REQUEST)
        
        # check user and enterprise relationship
        if not user_belong_to_enterprise(request.user, enterprise):
            raise PermissionDenied
        if check_user_enterprise_status(request.user, enterprise) in [Status.DEACTIVATED, Status.SUSPENDED, None]:
            raise PermissionDenied
        
        goals = []
        try:
            #  check if the the record 
            for goal in Goal.objects.filter(Q(is_done=False) & Q(enterprise=enterprise)):
                start = goal.starting_date
                end = goal.ending_date
                today = datetime.today().astimezone() 
                if is_event_in_current_week(start, end):
                    if today >= start and today<=end and is_user_in_charge_of_goal(request.user, goal)==True :
                        goals.append(goal.id)
                    # pass

            queryset = Goal.objects.filter(id__in=goals)

            page = self.paginate_queryset(queryset)

            if page is not None:
                serializer = self.serializer_class(page, context={"request": request}, many=True)
                return self.get_paginated_response(serializer.data)

        except Exception as e:
            content = {"error": _(f"An error occur: {e}")}
            return Response(content, status.HTTP_400_BAD_REQUEST)
    

class DayActivitiesStatistic(generics.ListAPIView):
    """ 
    Get all submit activity reports of the given day.

    Note:   the date format should be as 
            follow 'Year-month-day' or 'month/day/Year' eg: (2024-01-22 or 01/22/2024)    """
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated,]
    serializer_class = ReportListSerializer
    pagination_class  = PageNumberPagination
    queryset = Report.objects.all()
    lookup_field = "pk"

    def get (self, request, format= None):
        # check user authentication group
        checkAdministratorEmployeeGroupMixin(self)
       
        enterprise_name = request.GET.get("enterprise_name", "").upper()
        date = request.GET.get("date", "") # format: %Y-%m-%d or  %m/%d/%y

        if date == "" or enterprise_name== "":
            return Response(
                {
                    "detail":_(f"This request require both enterprise_name and date(format: %Y-%m-%d or  %m/%d/%y) as parameters data."),
                    "status":_("FAILED")
                },
                status.HTTP_400_BAD_REQUEST
            )
        
        if not is_valid_date_format(date):
            return Response(
                {
                    "detail":_(f"Invalid date format. Accepted date format are %Y-%m-%d or  %m/%d/%y."),
                    "status":_("FAILED")
                },
                status.HTTP_400_BAD_REQUEST
            )
        
        date_time = get_date_from_string_date(date)
        date = date_time.date()

        print(date)
        # year validation
        if date_time.year < 2024 or date_time.year> 9999:
            content= {"detail": _(f"This year is not valid")}
            return Response(content, status.HTTP_400_BAD_REQUEST)

        try:
            enterprise = Enterprise.objects.get(name= enterprise_name)
        except Enterprise.DoesNotExist:
            return Response({'detail': _(f"Enterprise {enterprise_name} does not exist.")}, status.HTTP_400_BAD_REQUEST)

        # identify the user
        if not user_belong_to_enterprise(request.user, enterprise):
            raise PermissionDenied
        if check_user_enterprise_status(request.user, enterprise) not in [Status.ACTIVE]:
            raise PermissionDenied
        
        reports = []

        try:
            filtered_reports = Report.objects.filter(
                option=ACTIVITY,
                date_of_submission__date=date,
                activity__goal__enterprise=enterprise
            )
            
            for report in filtered_reports:
                if is_user_in_charge_of_activity(request.user, report.activity):
                    reports.append(report.id)

            queryset = Report.objects.filter(id__in = reports)

            page = self.paginate_queryset(queryset)

            if page is not None:
                serializer = self.serializer_class(page, context={"request": request}, many=True)
                return self.get_paginated_response(serializer.data)
            
        
        except Exception as e:
            content = {"error": _(f"An error occur: {e}")}
            return Response(content, status.HTTP_400_BAD_REQUEST)
    

class DayGoalsStatistic( generics.ListAPIView):
    """ 
    Get all submit goal reports of the given day.

    Note:   the date format should be as 
            follow 'Year-month-day' or 'month/day/Year' eg: (2024-01-22 or 01/22/2024)
    """
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated,]
    serializer_class = ReportListSerializer
    pagination_class  = PageNumberPagination
    queryset = Report.objects.all()
    lookup_field = "pk"
    
    def get(self, request, format= None):
        # check user authentication group
        checkAdministratorEmployeeGroupMixin(self)
        
        
        enterprise_name = request.GET.get("enterprise_name", "").upper()
        date = request.GET.get("date", "") # format: %Y-%m-%d or  %m/%d/%y

        if date == "" or enterprise_name== "":
            return Response(
                {
                    "detail":_(f"This request require both enterprise_name and date(format: %Y-%m-%d or  %m/%d/%y) as parameters data."),
                    "status":_("FAILED")
                },
                status.HTTP_400_BAD_REQUEST
            )
        
        if is_valid_date_format(date) == False:
            return Response(
                {
                    "detail":_(f"Invalid date format. Accepted date format are %Y-%m-%d(2024-1-1 or 2024-01-01) or  %m/%d/%Y(08/01/2024 or 8/1/2024)."),
                    "status":_("FAILED")
                },
                status.HTTP_400_BAD_REQUEST
            )
        
        date_time= get_date_from_string_date(date)
        date = date_time.date()

        # year validation
        if date_time.year < 2024 or date_time.year> 9999:
            content= {"detail": _(f"This year is not valid")}
            return Response(content, status.HTTP_400_BAD_REQUEST)
        
        try:
            enterprise = Enterprise.objects.get(name= enterprise_name)
        except Enterprise.DoesNotExist:
            return Response({'detail': _(f"Enterprise {enterprise_name} does not exist.")}, status.HTTP_400_BAD_REQUEST)

        # identify the user
        if not user_belong_to_enterprise(request.user, enterprise):
            raise PermissionDenied
        if check_user_enterprise_status(request.user, enterprise) not in [Status.ACTIVE]:
            raise PermissionDenied
        
        reports = []

        try:
            filtered_reports = Report.objects.filter(
                option=GOAL,
                date_of_submission__date=date,
                goal__enterprise=enterprise,
            )
            
            for report in filtered_reports:
                if is_user_in_charge_of_goal(request.user, report.goal):
                    reports.append(report.id)

            queryset = Report.objects.filter(id__in = reports)

            page = self.paginate_queryset(queryset)

            if page is not None:
                serializer = self.serializer_class(page, context={"request": request}, many=True)
                return self.get_paginated_response(serializer.data)
        
        except Exception as e:
            content = {"error": _(f"An error occur: {e}")}
            return Response(content, status.HTTP_400_BAD_REQUEST)


"""
    \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
    WeekStatistic VIEW SECTION
"""

class WeekActivitiesStatistic( generics.ListAPIView):
    """
    Returns all submit reports of all the activities of the given weeks.

    And this will filter the list of activities according to the permission granted 
    to the user. 

    NOTE:   Administrators will see the overview of everything he covers under the 
    
            enterprise. While, simple employee will only see what is related to him/her.
    """
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated,]
    queryset = Report.objects.all()
    serializer_class = ReportListSerializer
    pagination_class = PageNumberPagination
    lookup_field = "pk"


    def get(self, request, format=None):
        # check user authentication group
        checkAdministratorEmployeeGroupMixin(self)
        
        enterprise_name = request.GET.get("enterprise_name", "").upper()
        year = request.GET.get("year", "")
        month_number = request.GET.get("month_number", '')
        week_number = request.GET.get("week_number", '')

        if enterprise_name == "" or year=="" or week_number=="":
            return Response(
                {
                    "detail": _("This request requires enterprise_name, year, month_number and week_number as parameter data.")
                },
                status.HTTP_400_BAD_REQUEST
            )

        # validation of parameters
        year = convert_string_to_int(year)
        month_number = convert_string_to_int(month_number)
        week_number = convert_string_to_int(week_number)

        if year == None or month_number == None or week_number == None:
            content={
                "detail":_('Make sure year, month_number and week_number don\'t include string characters.')
            }
            return Response(content, status.HTTP_400_BAD_REQUEST)

        # get enterprise
        try:
            enterprise = Enterprise.objects.get(name= enterprise_name)
        except Enterprise.DoesNotExist:
            content={
                "detail": _(f"Enterprise {enterprise_name} does not exists.")
            }
            return Response(content, status= status.HTTP_400_BAD_REQUEST)
        
        # Check user enterprise status
        if not user_belong_to_enterprise(request.user, enterprise):
            raise PermissionDenied
        if check_user_enterprise_status(request.user, enterprise) not in [Status.ACTIVE]:
            raise PermissionDenied
        
        #  year validation
        if year < 2024 or year> 9999:
            content= {"detail": _(f"This year {year} is not valid")}
            return Response(content, status.HTTP_400_BAD_REQUEST)

        # month validation
        if month_number < 1 or month_number > 12:
            content= {"detail": _(f"This month {month_number} is not valid")}
            return Response(content, status.HTTP_400_BAD_REQUEST)
        
        #  week_number validation
        if week_number not in get_month_info(year, month_number):
            content = {"detail": _(f"This week_number {week_number} is not valid")}
            return Response(content, status.HTTP_400_BAD_REQUEST)
                
        try:
            # filter reports according to the year, week and user authorization
            queryset = Report.objects.filter(
                option=ACTIVITY,
                date_of_submission__year=year,
                date_of_submission__week=week_number,
                activity__goal__enterprise=enterprise
            )

            page = self.paginate_queryset(queryset)

            if page is not None:
                serializer = self.serializer_class(page, context={"request": request}, many=True)
                return self.get_paginated_response(serializer.data)
        
        except Exception as e:
            content = {"error": _(f"An error occur: {e}")}
            return Response(content, status.HTTP_400_BAD_REQUEST)
        

class WeekActivitiesDayEvaluation( generics.ListAPIView):
    """
    Return the average rate of all completed activities report of the week per days of the week.
    """
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated,]
    

    def get(self, request, format=None):
        # check user authentication group
        checkAdministratorEmployeeGroupMixin(self)
        
        enterprise_name = request.GET.get("enterprise_name", "").upper()
        year = request.GET.get("year", "")
        month_number = request.GET.get("month_number", '')
        week_number = request.GET.get("week_number", '')

        if enterprise_name == "" or year=="" or week_number=="":
            return Response(
                {
                    "detail": _("This request requires enterprise_name, year, month_number and week_number as parameter data.")
                },
                status.HTTP_400_BAD_REQUEST
            )

        # validation of parameters
        year = convert_string_to_int(year)
        month_number = convert_string_to_int(month_number)
        week_number = convert_string_to_int(week_number)

        if year == None or month_number == None or week_number == None:
            content={
                "detail":_('Make sure year, month_number and week_number don\'t include string characters.')
            }
            return Response(content, status.HTTP_400_BAD_REQUEST)

        # get enterprise
        try:
            enterprise = Enterprise.objects.get(name= enterprise_name)
        except Enterprise.DoesNotExist:
            content={
                "detail": _(f"Enterprise {enterprise_name} does not exists.")
            }
            return Response(content, status= status.HTTP_400_BAD_REQUEST)
        
        # Check user enterprise status
        if not user_belong_to_enterprise(request.user, enterprise):
            raise PermissionDenied
        if check_user_enterprise_status(request.user, enterprise) not in [Status.ACTIVE]:
            raise PermissionDenied
        
        #  year validation
        if year < 2024 or year> 9999:
            content= {"detail": _(f"This year {year} is not valid")}
            return Response(content, status.HTTP_400_BAD_REQUEST)

        # month validation
        if month_number < 1 or month_number > 12:
            content= {"detail": _(f"This month {month_number} is not valid")}
            return Response(content, status.HTTP_400_BAD_REQUEST)
        
        #  week_number validation
        if week_number not in get_month_info(year, month_number):
            content = {"detail": _(f"This week_number {week_number} is not valid")}
            return Response(content, status.HTTP_400_BAD_REQUEST)
            
        statistics = {}
        data = {}

        statistics["detail"] = "Return the average rate of all activities of each day of the week"
        try:
            # filter reports according to the year, week and user authorization
            filtered_reports = Report.objects.filter(
                option=ACTIVITY,
                date_of_submission__year=year,
                date_of_submission__week = week_number,
                activity__goal__enterprise=enterprise
            )
            weeks = get_week_days_by_year_week(year, week_number)
            for i in weeks:
                data[str(i)] = []
            
            for report in filtered_reports:
                date_str = report.date_of_submission.strftime("%Y-%m-%d")
                if date_str in weeks:
                    data[date_str].append(report.rate or 0)

            for i in data:
                average = sum(data[i])
            
                average = int(average/(len(data[i]) or 1))

                statistics[i] = set_average_rate(average)
           
            return Response(statistics, status.HTTP_200_OK)
        
        except Exception as e:
            content = {"error": _(f"An error occur: {e}")}
            return Response(content, status.HTTP_400_BAD_REQUEST)


class WeekGoalDayEvaluation( generics.ListAPIView):
    """
    Return the average rate of all completed goal report of the week per days of the week.
    """
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated,]
    

    def get(self, request, format=None):
        # check user authentication group
        checkAdministratorEmployeeGroupMixin(self)
        
        enterprise_name = request.GET.get("enterprise_name", "").upper()
        year = request.GET.get("year", "")
        month_number = request.GET.get("month_number", '')
        week_number = request.GET.get("week_number", '')

        if enterprise_name == "" or year=="" or week_number=="":
            return Response(
                {
                    "detail": _("This request requires enterprise_name, year, month_number and week_number as parameter data.")
                },
                status.HTTP_400_BAD_REQUEST
            )

        # validation of parameters
        year = convert_string_to_int(year)
        month_number = convert_string_to_int(month_number)
        week_number = convert_string_to_int(week_number)

        if year == None or month_number == None or week_number == None:
            content={
                "detail":_('Make sure year, month_number and week_number don\'t include string characters.')
            }
            return Response(content, status.HTTP_400_BAD_REQUEST)

        # get enterprise
        try:
            enterprise = Enterprise.objects.get(name= enterprise_name)
        except Enterprise.DoesNotExist:
            content={
                "detail": _(f"Enterprise {enterprise_name} does not exists.")
            }
            return Response(content, status= status.HTTP_400_BAD_REQUEST)
        
        # Check user enterprise status
        if not user_belong_to_enterprise(request.user, enterprise):
            raise PermissionDenied
        if check_user_enterprise_status(request.user, enterprise) not in [Status.ACTIVE]:
            raise PermissionDenied
        
        #  year validation
        if year < 2024 or year> 9999:
            content= {"detail": _(f"This year {year} is not valid")}
            return Response(content, status.HTTP_400_BAD_REQUEST)

        # month validation
        if month_number < 1 or month_number > 12:
            content= {"detail": _(f"This month {month_number} is not valid")}
            return Response(content, status.HTTP_400_BAD_REQUEST)
        
        #  week_number validation
        if week_number not in get_month_info(year, month_number):
            content = {"detail": _(f"This week_number {week_number} is not valid")}
            return Response(content, status.HTTP_400_BAD_REQUEST)
            
        statistics = {}
        data = {}

        statistics["detail"] = "Return the average rate of all goals of each day of the week"
        try:
            # filter reports according to the year, week and user authorization
            filtered_reports = Report.objects.filter(
                option=GOAL,
                date_of_submission__year=year,
                date_of_submission__month= month_number,
                date_of_submission__week = week_number,
                goal__enterprise=enterprise
            )
            print(filtered_reports)
            weeks = get_week_days_by_year_week(year, week_number)
            for i in weeks:
                data[str(i)] = []
            
            for report in filtered_reports:
                date_str = report.date_of_submission.strftime("%Y-%m-%d")
                if date_str in weeks:
                    data[date_str].append(report.rate or 0)

        

            for i in data:
                average = sum(data[i])
                average = int(average/(len(data[i]) or 1))

                statistics[i] = set_average_rate(average)
           
            return Response(statistics, status.HTTP_200_OK)
        
        except Exception as e:
            content = {"error": _(f"An error occur: {e}")}
            return Response(content, status.HTTP_400_BAD_REQUEST)


class WeekGoalsStatistic( generics.ListAPIView):
    """
    This view take an enterprise_name as input and return a serialized data that contains
    a list of statistics of all the activities per weeks.

    And this will filter the list of activities according to the permission granted 
    to the user. 

    NOTE:   Administrators will see the overview of everything he covers under the 
    
            enterprise. While, simple employee will only see what is related to him/her.
    """ 
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated,]
    queryset = Report.objects.all()
    serializer_class = ReportListSerializer
    pagination_class = PageNumberPagination
    lookup_field = "pk"

    def get(self, request, format=None):
        # check user authentication group
        checkAdministratorEmployeeGroupMixin(self)
        
        enterprise_name = request.GET.get("enterprise_name", "").upper()
        year = request.GET.get("year", "")
        month_number = request.GET.get("month_number", '')
        week_number = request.GET.get("week_number", '')

        if enterprise_name == "" or year=="" or week_number=="":
            return Response(
                {
                    "detail": _("This request requires enterprise_name, year, month_number and week_number as parameter data.")
                },
                status.HTTP_400_BAD_REQUEST
            )

        # validation of parameters
        year = convert_string_to_int(year)
        month_number = convert_string_to_int(month_number)
        week_number = convert_string_to_int(week_number)

        if year == None or month_number == None or week_number == None:
            content={
                "detail":_('Make sure year, month_number and week_number don\'t include string characters.')
            }
            return Response(content, status.HTTP_400_BAD_REQUEST)


        # get enterprise
        try:
            enterprise = Enterprise.objects.get(name= enterprise_name)
        except Enterprise.DoesNotExist:
            content={
                "detail": _(f"Enterprise {enterprise_name} does not exists.")
            }
            return Response(content, status= status.HTTP_400_BAD_REQUEST)
        
        # Check user enterprise status
        if not user_belong_to_enterprise(request.user, enterprise):
            raise PermissionDenied
        if check_user_enterprise_status(request.user, enterprise) not in [Status.ACTIVE]:
            raise PermissionDenied
        
        #  year validation
        if year < 2024 or year> 9999:
            content= {"detail": _(f"This year {year} is not valid")}
            return Response(content, status.HTTP_400_BAD_REQUEST)

        # month validation
        if month_number < 1 or month_number > 12:
            content= {"detail": _(f"This month {month_number} is not valid")}
            return Response(content, status.HTTP_400_BAD_REQUEST)
        
        #  week_number validation
        if week_number not in get_month_info(year, month_number):
            content = {"detail": _(f"This week_number {week_number} is not valid")}
            return Response(content, status.HTTP_400_BAD_REQUEST)
                
        try:
            # filter reports according to the year, week and user authorization
            queryset = Report.objects.filter(
                option=GOAL,
                date_of_submission__year=year,
                date_of_submission__month= month_number,
                date_of_submission__week = week_number,
                goal__enterprise=enterprise
            )

            page = self.paginate_queryset(queryset)

            if page is not None:
                serializer = self.serializer_class(page, context={"request": request}, many=True)
                return self.get_paginated_response(serializer.data)
        
        except Exception as e:
            content = {"error": _(f"An error occur: {e}")}
            return Response(content, status.HTTP_400_BAD_REQUEST)
        

"""
    \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
    MonthStatistic VIEW SECTION
"""
class MonthActivitiesStatistic(generics.ListAPIView):
    """
    This view take an enterprise_name as input and return a serialized data that contains
    a list of statistics of all the activities per weeks.

    And this will filter the list of activities according to the permission granted 
    to the user. 

    NOTE:   Administrators will see the overview of everything he covers under the 
    
            enterprise. While, simple employee will only see what is related to him/her.
    """
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated,]
    queryset = Report.objects.all()
    serializer_class = ReportListSerializer
    pagination_class = PageNumberPagination
    lookup_field = "pk"

    def get(self, request, format=None):
        # check user authentication group
        check = checkEmployeeAdminGroupMixin(self)
        
        
        enterprise_name = request.GET.get("enterprise_name", "").upper()
        year = request.GET.get("year", "")
        month_number = request.GET.get("month_number", '')

        if enterprise_name == "" or year=="" or month_number =="" :
            return Response(
                {
                    "detail": _("This request requires enterprise_name, year, month_number  as parameter data.")
                },
                status.HTTP_400_BAD_REQUEST
            )

        # validation of parameters
        year = convert_string_to_int(year)
        month_number = convert_string_to_int(month_number)

        if year == None or month_number == None:
            content={
                "detail":_('Make sure year and month_number don\'t include string characters.')
            }
            return Response(content, status.HTTP_400_BAD_REQUEST)

        
        # get enterprise
        try:
            enterprise = Enterprise.objects.get(name= enterprise_name)
        except Enterprise.DoesNotExist:
            content={
                "detail": _(f"Enterprise {enterprise_name} does not exists.")
            }
            return Response(content, status= status.HTTP_400_BAD_REQUEST)
        
        # Check user enterprise status
        if check == IS_EMPLOYEE_ADMIN and request.user not in enterprise.employee_admins.all():
            raise PermissionDenied
        if not user_belong_to_enterprise(request.user, enterprise):
            raise PermissionDenied
        if check_user_enterprise_status(request.user, enterprise) not in [Status.ACTIVE]:
            raise PermissionDenied
        
        #  year validation
        if year < 2024 or year> 9999:
            content= {"detail": _(f"This year {year} is not valid")}
            return Response(content, status.HTTP_400_BAD_REQUEST)

        # month validation
        if month_number < 1 or month_number > 12:
            content= {"detail": _(f"This month {month_number} is not valid")}
            return Response(content, status.HTTP_400_BAD_REQUEST)
        
        try:
            # filter reports according to the year, week and user authorization
            queryset = Report.objects.filter(
                option=ACTIVITY,
                date_of_submission__year=year,
                date_of_submission__month=month_number,
                activity__goal__enterprise=enterprise
            )

            page = self.paginate_queryset(queryset)

            if page is not None:
                serializer = self.serializer_class(page, context={"request": request}, many=True)
                return self.get_paginated_response(serializer.data)
            
        
        except Exception as e:
            content = {"error": _(f"An error occur: {e}")}
            return Response(content, status.HTTP_400_BAD_REQUEST)
        

        
        #filter the list according to the year 


class MonthWeeksActivitiesEvaluation(APIView):
    """ return the average rate of all activities per week_number of the month"""
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated,]
    
    def get(self, request, format=None):
        # check user authentication group
        check = checkEmployeeAdminGroupMixin(self)
        
        enterprise_name = request.GET.get("enterprise_name", "").upper()
        year = request.GET.get("year", "")
        month_number = request.GET.get("month_number", '')

        if enterprise_name == "" or year=="" or month_number=="" :
            return Response(
                {
                    "detail": _("This request requires enterprise_name, year, month_number  as parameter data.")
                },
                status.HTTP_400_BAD_REQUEST
            )

        # validation of parameters
        year = convert_string_to_int(year)
        month_number = convert_string_to_int(month_number)

        if year == None or month_number == None:
            content={
                "detail":_('Make sure year and month_number don\'t include string characters.')
            }
            return Response(content, status.HTTP_400_BAD_REQUEST)

        # get enterprise
        try:
            enterprise = Enterprise.objects.get(name= enterprise_name)
        except Enterprise.DoesNotExist:
            content={
                "detail": _(f"Enterprise {enterprise_name} does not exists.")
            }
            return Response(content, status= status.HTTP_400_BAD_REQUEST)
        
        # Check user enterprise status
        if check == IS_EMPLOYEE_ADMIN and request.user not in enterprise.employee_admins.all():
            raise PermissionDenied
        if not user_belong_to_enterprise(request.user, enterprise):
            raise PermissionDenied
        if check_user_enterprise_status(request.user, enterprise) not in [Status.ACTIVE]:
            raise PermissionDenied
        
        #  year validation
        if year < 2024 or year> 9999:
            content= {"detail": _(f"This year {year} is not valid")}
            return Response(content, status.HTTP_400_BAD_REQUEST)

        # month validation
        if month_number < 1 or month_number > 12:
            content= {"detail": _(f"This month {month_number} is not valid")}
            return Response(content, status.HTTP_400_BAD_REQUEST)
        
        week_numbers = get_month_info(year, month_number)
       
        statistics = {}
        data = {}

        statistics["detail"] = "Return the average rate of all activities of each week of the month"
        try:
            for week in week_numbers:
                average = 0
                # get all the reports of the week
                filtered_reports = Report.objects.filter(
                    option=ACTIVITY,
                    date_of_submission__year=year,
                    date_of_submission__week = week,
                    activity__goal__enterprise=enterprise
                )

                for report in filtered_reports:
                    average += report.rate or 0
                
                d = len(filtered_reports) or 1
                statistics[week] = set_average_rate(int(average/d))
                
            
            return Response(statistics, status.HTTP_200_OK)
        
        except Exception as e:
            content = {"error": _(f"An error occur: {e}")}
            return Response(content, status.HTTP_400_BAD_REQUEST)


class MonthWeeksGoalsEvaluation(APIView):
    """ return the average rate of all goals per week_number of the month"""
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated,]
    
    def get(self, request, format=None):
        # check user authentication group
        check = checkEmployeeAdminGroupMixin(self)
        
        enterprise_name = request.GET.get("enterprise_name", "").upper()
        year = request.GET.get("year", "")
        month_number = request.GET.get("month_number", '')

        if enterprise_name == "" or year=="" or month_number=="" :
            return Response(
                {
                    "detail": _("This request requires enterprise_name, year, month_number  as parameter data.")
                },
                status.HTTP_400_BAD_REQUEST
            )

        # validation of parameters
        year = convert_string_to_int(year)
        month_number = convert_string_to_int(month_number)

        if year == None or month_number == None:
            content={
                "detail":_('Make sure year and month_number don\'t include string characters.')
            }
            return Response(content, status.HTTP_400_BAD_REQUEST)


        # get enterprise
        try:
            enterprise = Enterprise.objects.get(name= enterprise_name)
        except Enterprise.DoesNotExist:
            content={
                "detail": _(f"Enterprise {enterprise_name} does not exists.")
            }
            return Response(content, status= status.HTTP_400_BAD_REQUEST)
        
        # Check user enterprise status
        if check == IS_EMPLOYEE_ADMIN and request.user not in enterprise.employee_admins.all():
            raise PermissionDenied
        if not user_belong_to_enterprise(request.user, enterprise):
            raise PermissionDenied
        if check_user_enterprise_status(request.user, enterprise) not in [Status.ACTIVE]:
            raise PermissionDenied
        
        #  year validation
        if year < 2024 or year> 9999:
            content= {"detail": _(f"This year {year} is not valid")}
            return Response(content, status.HTTP_400_BAD_REQUEST)

        # month validation
        if month_number < 1 or month_number > 12:
            content= {"detail": _(f"This month {month_number} is not valid")}
            return Response(content, status.HTTP_400_BAD_REQUEST)
        
        week_numbers = get_month_info(year, month_number)
       
        statistics = {}
        data = {}

        statistics["detail"] = "Return the average rate of all goals of each week of the month"
        try:
            for week in week_numbers:
                average = 0
                # get all the reports of the week
                filtered_reports = Report.objects.filter(
                    option=GOAL,
                    date_of_submission__year=year,
                    date_of_submission__week = week,
                    goal__enterprise=enterprise
                )

                
                for report in filtered_reports:
                    average += report.rate or 0
                
                d = len(filtered_reports) or 1
                statistics[week] = set_average_rate(int(average/d))
            
            
            return Response(statistics, status.HTTP_200_OK)
        
        except Exception as e:
            content = {"error": _(f"An error occur: {e}")}
            return Response(content, status.HTTP_400_BAD_REQUEST)


class MonthGoalsStatistic( generics.ListAPIView):
    """
    This view take an enterprise_name as input and return a serialized data that contains
    a list of statistics of all the activities per weeks.

    And this will filter the list of activities according to the permission granted 
    to the user. 

    NOTE:   Administrators will see the overview of everything he covers under the 
    
            enterprise. While, simple employee will only see what is related to him/her.
    """
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated,]
    queryset = Report.objects.all()
    serializer_class = ReportListSerializer
    pagination_class = PageNumberPagination
    lookup_field = "pk"

    def get(self, request, format=None):
        # check user authentication group
        check = checkEmployeeAdminGroupMixin(self)
        
        enterprise_name = request.GET.get("enterprise_name", "").upper()
        year = request.GET.get("year", "")
        month_number = request.GET.get("month_number", '')

        if enterprise_name == "" or year=="" or month_number=="" :
            return Response(
                {
                    "detail": _("This request requires enterprise_name, year, month_number  as parameter data.")
                },
                status.HTTP_400_BAD_REQUEST
            )

        # validation of parameters
        year = convert_string_to_int(year)
        month_number = convert_string_to_int(month_number)

        if year == None or month_number == None:
            content={
                "detail":_('Make sure year and month_number don\'t include string characters.')
            }
            return Response(content, status.HTTP_400_BAD_REQUEST)


        # get enterprise
        try:
            enterprise = Enterprise.objects.get(name= enterprise_name)
        except Enterprise.DoesNotExist:
            content={
                "detail": _(f"Enterprise {enterprise_name} does not exists.")
            }
            return Response(content, status= status.HTTP_400_BAD_REQUEST)
        
        # Check user enterprise status
        if check == IS_EMPLOYEE_ADMIN and request.user not in enterprise.employee_admins.all():
            raise PermissionDenied
        if not user_belong_to_enterprise(request.user, enterprise):
            raise PermissionDenied
        if check_user_enterprise_status(request.user, enterprise) not in [Status.ACTIVE]:
            raise PermissionDenied
        
        #  year validation
        if year < 2024 or year> 9999:
            content= {"detail": _(f"This year {year} is not valid")}
            return Response(content, status.HTTP_400_BAD_REQUEST)

        # month validation
        if month_number < 1 or month_number > 12:
            content= {"detail": _(f"This month {month_number} is not valid")}
            return Response(content, status.HTTP_400_BAD_REQUEST)
        
        try:
            # filter reports according to the year, week and user authorization
            queryset = Report.objects.filter(
                option=GOAL,
                date_of_submission__year=year,
                date_of_submission__month = month_number,
                goal__enterprise=enterprise
            )

            page = self.paginate_queryset(queryset)

            if page is not None:
                serializer = self.serializer_class(page, context={"request": request}, many=True)
                return self.get_paginated_response(serializer.data)
        
        except Exception as e:
            content = {"error": _(f"An error occur: {e}")}
            return Response(content, status.HTTP_400_BAD_REQUEST)



"""
    \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
    YearStatistic VIEW SECTION
"""
class YearActivitiesStatistic(generics.ListAPIView):
    """
    This view take an enterprise_name as input and return a serialized data that contains
    a list of statistics of all the activities of the year.
    """
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated,]
    queryset = Report.objects.all()
    serializer_class = ReportListSerializer
    pagination_class = PageNumberPagination
    lookup_field = "pk"

    def get(self, request, format=None):
        # check user authentication group
        checkAdministratorGroupMixin(self)
        
        enterprise_name = request.GET.get("enterprise_name", "").upper()
        year = request.GET.get("year", "")

        if enterprise_name == "" or year=="" :
            return Response(
                {
                    "detail": _("This request requires enterprise_name and year as parameter data.")
                },
                status.HTTP_400_BAD_REQUEST
            )

        # validation of parameters
        year = convert_string_to_int(year)

        if year == None:
            content={
                "detail":_('Make sure year does not include string characters.')
            }
            return Response(content, status.HTTP_400_BAD_REQUEST)

        
        # get enterprise
        try:
            enterprise = Enterprise.objects.get(name= enterprise_name)
        except Enterprise.DoesNotExist:
            content={
                "detail": _(f"Enterprise {enterprise_name} does not exists.")
            }
            return Response(content, status= status.HTTP_400_BAD_REQUEST)
        
        # Check user enterprise status
        if not user_belong_to_enterprise(request.user, enterprise):
            raise PermissionDenied
        if check_user_enterprise_status(request.user, enterprise) not in [Status.ACTIVE]:
            raise PermissionDenied
        
        #  year validation
        if year < 2024 or year> 9999:
            content= {"detail": _(f"This year {year} is not valid")}
            return Response(content, status.HTTP_400_BAD_REQUEST)
        
        try:
            # filter reports according to the year, week and user authorization
            queryset = Report.objects.filter(
                option=ACTIVITY,
                date_of_submission__year=year,
                activity__goal__enterprise=enterprise
            )

            page = self.paginate_queryset(queryset)

            if page is not None:
                serializer = self.serializer_class(page, context={"request": request}, many=True)
                return self.get_paginated_response(serializer.data)
        
        except Exception as e:
            content = {"error": _(f"An error occur: {e}")}
            return Response(content, status.HTTP_400_BAD_REQUEST)
        

class YearMonthsGoalsEvaluation( APIView):
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated,]

    def get(self, request, format=None):
        # check user authentication group
        checkAdministratorGroupMixin(self)
        
        enterprise_name = request.GET.get("enterprise_name", "").upper()
        year = request.GET.get("year", "")

        if enterprise_name == "" or year=="" :
            return Response(
                {
                    "detail": _("This request requires enterprise_name and year as parameter data.")
                },
                status.HTTP_400_BAD_REQUEST
            )

        # validation of parameters
        year = convert_string_to_int(year)

        if year == None:
            content={
                "detail":_('Make sure year does not include string characters.')
            }
            return Response(content, status.HTTP_400_BAD_REQUEST)


        # get enterprise
        try:
            enterprise = Enterprise.objects.get(name= enterprise_name)
        except Enterprise.DoesNotExist:
            content={
                "detail": _(f"Enterprise {enterprise_name} does not exists.")
            }
            return Response(content, status= status.HTTP_400_BAD_REQUEST)
        
        # Check user enterprise status
        if not user_belong_to_enterprise(request.user, enterprise):
            raise PermissionDenied
        if check_user_enterprise_status(request.user, enterprise) not in [Status.ACTIVE]:
            raise PermissionDenied
        
        #  year validation
        if year < 2024 or year> 9999:
            content= {"detail": _(f"This year {year} is not valid")}
            return Response(content, status.HTTP_400_BAD_REQUEST)
       
        statistics = {}
        data = {}

        statistics["detail"] = "Return the average rate of all goals of each month of the year"
        try:
            
            for month in range(1, 13):
                average  = 0
                queryset = Report.objects.filter(
                    option=GOAL,
                    date_of_submission__year = year,
                    date_of_submission__month = month,
                    goal__enterprise = enterprise
                )

                for report in queryset:
                    average += report.rate or 0

                average /= len(queryset) or 1

                statistics[month] = set_average_rate(average)


            return Response(statistics, status.HTTP_200_OK)
        
        except Exception as e:
            content = {"error": _(f"An error occur: {e}")}
            return Response(content, status.HTTP_400_BAD_REQUEST)


class YearMonthsActivitiesEvaluation( APIView):
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated,]

    def get(self, request, format=None):
        # check user authentication group
        checkAdministratorGroupMixin(self)
        
        enterprise_name = request.GET.get("enterprise_name", "").upper()
        year = request.GET.get("year", "")

        if enterprise_name == "" or year=="" :
            return Response(
                {
                    "detail": _("This request requires enterprise_name and year as parameter data.")
                },
                status.HTTP_400_BAD_REQUEST
            )

        # validation of parameters
        year = convert_string_to_int(year)

        if year == None:
            content={
                "detail":_('Make sure year does not include string characters.')
            }
            return Response(content, status.HTTP_400_BAD_REQUEST)


        # get enterprise
        try:
            enterprise = Enterprise.objects.get(name= enterprise_name)
        except Enterprise.DoesNotExist:
            content={
                "detail": _(f"Enterprise {enterprise_name} does not exists.")
            }
            return Response(content, status= status.HTTP_400_BAD_REQUEST)
        
        # Check user enterprise status
        if not user_belong_to_enterprise(request.user, enterprise):
            raise PermissionDenied
        if check_user_enterprise_status(request.user, enterprise) not in [Status.ACTIVE]:
            raise PermissionDenied
        
        #  year validation
        if year < 2024 or year> 9999:
            content= {"detail": _(f"This year {year} is not valid")}
            return Response(content, status.HTTP_400_BAD_REQUEST)
       
        statistics = {}
        data = {}

        statistics["detail"] = "Return the average rate of all activities of each month of the year"
        try:
            for month in range(1, 13):
                average  = 0
                queryset = Report.objects.filter(
                    option=ACTIVITY,
                    date_of_submission__year = year,
                    date_of_submission__month = month,
                    activity__goal__enterprise = enterprise
                )

                for report in queryset:
                    average += report.rate or 0

                average /= len(queryset) or 1

                statistics[month] = set_average_rate(average)
            
            return Response(statistics, status.HTTP_200_OK)
        
        except Exception as e:
            content = {"error": _(f"An error occur: {e}")}
            return Response(content, status.HTTP_400_BAD_REQUEST)


class YearGoalsStatistic( generics.ListAPIView):
    """
    This view take an enterprise_name and year number as input and return a serialized data that contains
    a list of all the Goals of the enterprise of that year.
    """
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated,]
    queryset = Report.objects.all()
    serializer_class = ReportListSerializer
    pagination_class = PageNumberPagination
    lookup_field = "pk"

    def get(self, request, format=None):
        # check user authentication group
        checkAdministratorGroupMixin(self)
        
        enterprise_name = request.GET.get("enterprise_name", "").upper()
        year = request.GET.get("year", "")

        if enterprise_name == "" or year=="" :
            return Response(
                {
                    "detail": _("This request requires enterprise_name and year as parameter data.")
                },
                status.HTTP_400_BAD_REQUEST
            )

        # validation of parameters
        year = convert_string_to_int(year)

        if year == None:
            content={
                "detail":_('Make sure year does not include string characters.')
            }
            return Response(content, status.HTTP_400_BAD_REQUEST)


        # get enterprise
        try:
            enterprise = Enterprise.objects.get(name= enterprise_name)
        except Enterprise.DoesNotExist:
            content={
                "detail": _(f"Enterprise {enterprise_name} does not exists.")
            }
            return Response(content, status= status.HTTP_400_BAD_REQUEST)
        
        # Check user enterprise status
        if not user_belong_to_enterprise(request.user, enterprise):
            raise PermissionDenied
        if check_user_enterprise_status(request.user, enterprise) not in [Status.ACTIVE]:
            raise PermissionDenied
        
        #  year validation
        if year < 2024 or year> 9999:
            content= {"detail": _(f"This year {year} is not valid")}
            return Response(content, status.HTTP_400_BAD_REQUEST)

        try:
            # filter reports according to the year, week and user authorization
            queryset = Report.objects.filter(
                option=GOAL,
                date_of_submission__year=year,
                goal__enterprise=enterprise
            )

            page = self.paginate_queryset(queryset)

            if page is not None:
                serializer = self.serializer_class(page, context={"request": request}, many=True)
                return self.get_paginated_response(serializer.data)
        
        except Exception as e:
            content = {"error": _(f"An error occur: {e}")}
            return Response(content, status.HTTP_400_BAD_REQUEST)


"""
    \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
    goal progress VIEW SECTION
"""

class GoalProgress( generics.RetrieveAPIView):
    """
    This view calculate the progress of a non finish goal base on 
    the numbers of activities of that goal.
    
    The total number of activities determine the percentage of each
    finish activity.
    """
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated,]
    queryset = Goal.objects.all()
    serializer_class = GoalSerializerList
    lookup_field = "pk"

    def get(self, request, *args, **kwargs):
        # check user authentication group
        checkAdministratorEmployeeGroupMixin(self)
        
        serializer = self.serializer_class

        try:
            goal = self.get_object()
        except Goal.DoesNotExist:
            content = {"detail": _(f"This element does not exists.")}
            return Response(content, status = status.HTTP_400_BAD_REQUEST)
        
        enterprise = goal.enterprise

        if not user_belong_to_enterprise(request.user, enterprise):
            raise PermissionDenied
        if check_user_enterprise_status(request.user, enterprise) not in [Status.ACTIVE]:
            raise PermissionDenied
        if not is_user_in_charge_of_goal(request.user, goal):
            raise PermissionDenied
        
        detail = serializer(goal, context={"request": request})
        data = detail.data
        total, percentage, completed, submit, non_submit = get_goal_progress(goal)

        
        data["required_reports_number"] = total
        data["completed"] = completed
        data["percentage"] = percentage
        data["submit"] = submit
        data["non_submit"] = non_submit

        # if total == 0:
        #     try:
        #         report = Report.objects.get(option=GOAL, goal=goal)
        #         if report.rate in [100, 200, 300, 400, 500]:
        #             data["percentage"] = 100
        #     except Report.DoesNotExist:
        #         pass
            

        return Response(data, status.HTTP_200_OK)

        
class GoalWeekStatistic(generics.ListAPIView):
    """
    This view calculate the progress of all goal of the week.
    """
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated,]
    pagination_class = PageNumberPagination
    queryset = Goal.objects.all()


    def get(self, request, format=None):
        # check user authentication group
        check = checkEmployeeAdminGroupMixin(self)
        
        enterprise_name = request.GET.get("enterprise_name", "").upper()
        year = request.GET.get("year", "")
        month_number = request.GET.get("month_number", '')
        week_number = request.GET.get("week_number", '')

        if enterprise_name == "" or year=="" or month_number=="" or week_number=="":
            return Response(
                {
                    "detail": _("This request requires enterprise_name, year, month_number and week_number as parameter data.")
                },
                status.HTTP_400_BAD_REQUEST
            )

        # validation of parameters
        year = convert_string_to_int(year)
        month_number = convert_string_to_int(month_number)
        week_number = convert_string_to_int(week_number)

        if year == None or month_number == None or week_number == None:
            content={
                "detail":_('Make sure year, month_number and week_number don\'t include string characters.')
            }
            return Response(content, status.HTTP_400_BAD_REQUEST)


        # get enterprise
        try:
            enterprise = Enterprise.objects.get(name= enterprise_name)
        except Enterprise.DoesNotExist:
            content={
                "detail": _(f"Enterprise {enterprise_name} does not exists.")
            }
            return Response(content, status= status.HTTP_400_BAD_REQUEST)
        
        # Check user enterprise status
        if check == IS_EMPLOYEE_ADMIN and request.user not in enterprise.employee_admins.all():
            raise PermissionDenied
        if not user_belong_to_enterprise(request.user, enterprise):
            raise PermissionDenied
        if check_user_enterprise_status(request.user, enterprise) not in [Status.ACTIVE]:
            raise PermissionDenied
        
        #  year validation
        if year < 2024 or year> 9999:
            content= {"detail": _(f"This year {year} is not valid")}
            return Response(content, status.HTTP_400_BAD_REQUEST)

        # month validation
        if month_number < 1 or month_number > 12:
            content= {"detail": _(f"This month {month_number} is not valid")}
            return Response(content, status.HTTP_400_BAD_REQUEST)
        
        #  week_number validation
        if week_number not in get_month_info(year, month_number):
            content = {"detail": _(f"This week_number {week_number} is not valid")}
            return Response(content, status.HTTP_400_BAD_REQUEST)
        
        
        statistics = {}
        statistics["goals"] = []
        percentage_sum = 0
        # try:
        goal_list =  Goal.objects.filter(
            enterprise = enterprise
        )

        if not goal_list:
            return Response({"detail": _("No goal found.")},status.HTTP_200_OK)
        
        content = []
        valid_goals = 0
        for goal in goal_list:
            
            if is_event_in_week(goal.starting_date.date(), goal.ending_date.date(), year, month_number, week_number):
                valid_goals +=1
                total, percentage, completed, submit, non_submit = get_goal_progress(goal)
                x = GoalSerializerList(goal,context={"request": request})
                data = x.data
                data["required_reports_number"] = total
                data["completed"] = completed
                data["percentage"] = percentage
                data["submit"] = submit
                data["non_submit"] = non_submit

                stat_data = statistics["goals"]
                stat_data.append(data)
                statistics["goals"] = stat_data
                percentage_sum +=percentage
        
        average = valid_goals if valid_goals != 0 else 1
        statistics["average_percentage"]= int(percentage_sum/average)

        return Response(statistics, status.HTTP_200_OK)

        # except Exception as e:
        #     return Response({"error": _(f"{e}")}, status=status.HTTP_400_BAD_REQUEST)
                

class GoalMonthStatistic(APIView):
    """
    This view calculate the progress of all goal of the month.
    """
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated,]

    def get(self, request, format=None):
        # check user authentication group
        check = checkEmployeeAdminGroupMixin(self)
        
        enterprise_name = request.GET.get("enterprise_name", "").upper()
        year = request.GET.get("year", "")
        month_number = request.GET.get("month_number", '')

        if enterprise_name == "" or year=="" or month_number=="":
            return Response(
                {
                    "detail": _("This request requires enterprise_name, year, month_number as parameter data.")
                },
                status.HTTP_400_BAD_REQUEST
            )

        # validation of parameters
        year = convert_string_to_int(year)
        month_number = convert_string_to_int(month_number)

        if year == None or month_number == None:
            content={
                "detail":_('Make sure the year, month_number  don\'t include string characters.')
            }
            return Response(content, status.HTTP_400_BAD_REQUEST)


        # get enterprise
        try:
            enterprise = Enterprise.objects.get(name= enterprise_name)
        except Enterprise.DoesNotExist:
            content={
                "detail": _(f"Enterprise {enterprise_name} does not exists.")
            }
            return Response(content, status= status.HTTP_400_BAD_REQUEST)
        
        # Check user enterprise status
        if check == IS_EMPLOYEE_ADMIN and request.user not in enterprise.employee_admins.all():
            raise PermissionDenied
        if not user_belong_to_enterprise(request.user, enterprise):
            raise PermissionDenied
        if check_user_enterprise_status(request.user, enterprise) not in [Status.ACTIVE]:
            raise PermissionDenied
        
        #  year validation
        if year < 2024 or year> 9999:
            content= {"detail": _(f"This year {year} is not valid")}
            return Response(content, status.HTTP_400_BAD_REQUEST)

        # month validation
        if month_number < 1 or month_number > 12:
            content= {"detail": _(f"This month {month_number} is not valid")}
            return Response(content, status.HTTP_400_BAD_REQUEST)
        
        content = []
        percentage_sum = 0
        try:
            goal_list =  Goal.objects.filter(
                (Q(starting_date__year= year) | Q(starting_date__year__gt= year)),
                (Q(starting_date__month= month_number) | Q(starting_date__month__lt= month_number)),
                (Q(ending_date__month= month_number) | Q(ending_date__month__gt= month_number)),
                enterprise = enterprise,
            )
            average = goal_list.count() if goal_list.count() > 0 else 1
            for goal in goal_list:
                total, percentage, completed, submit, non_submit = get_goal_progress(goal)
                x = GoalSerializerList(goal,context={"request": request})
                data = x.data
                data["required_reports_number"] = total
                data["completed"] = completed
                data["percentage"] = percentage
                data["submit"] = submit
                data["non_submit"] = non_submit
                percentage_sum +=percentage
                content.append(data)

            if not goal_list:
                return Response({"detail": _("No goal found.")},status.HTTP_200_OK)

            content.append({"average_percentage": int(percentage_sum/average)})
            return Response(content, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": _(f"{e}")}, status.HTTP_400_BAD_REQUEST)
    

class GoalYearStatistic( APIView):
    """
    This view calculate the progress of all goal of the Year.
    """
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated,]
    serializer_class = PerformanceYearSerializer

    def get(self, request, format=None):
        # check user authentication group
        checkAdministratorGroupMixin(self)
        
        serializer = self.serializer_class(data= request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)
        
        enterprise_name = serializer.data["enterprise_name"].upper()
        year = serializer.data["year"]
        
        # get enterprise
        try:
            enterprise = Enterprise.objects.get(name= enterprise_name)
        except Enterprise.DoesNotExist:
            content={
                "detail": _(f"Enterprise {enterprise_name} does not exists.")
            }
            return Response(content, status= status.HTTP_400_BAD_REQUEST)
        
        # Check user enterprise status
        if not user_belong_to_enterprise(request.user, enterprise):
            raise PermissionDenied
        if check_user_enterprise_status(request.user, enterprise) not in [Status.ACTIVE]:
            raise PermissionDenied
        
        #  year validation
        if year < 2024 or year> 9999:
            content= {"detail": _(f"This year {year} is not valid")}
            return Response(content, status.HTTP_400_BAD_REQUEST)

        percentage_sum = 0
        content = []
        try:
            goal_list =  Goal.objects.filter(
                date_of_registration__year = year,
                enterprise = enterprise,
            )
            average = goal_list.count() if goal_list.count() > 0 else 1
            for goal in goal_list:
                # is_event_in_current_week
                total, percentage, completed, submit, non_submit = get_goal_progress(goal)
                x = GoalSerializerList(goal, context={"request": request})
                data = x.data
                data["required_reports_number"] = total
                data["completed"] = completed
                data["percentage"] = percentage
                data["submit"] = submit
                data["non_submit"] = non_submit
                percentage_sum +=percentage

                content.append(data)

            if not goal_list:
                return Response({"detail": _("No goal found.")},status.HTTP_200_OK)
            
            content.append({"average_percentage": int(percentage_sum/average)})
            return Response(content, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": _(f"{e}")}, status.HTTP_400_BAD_REQUEST)
    

class AllGoalProgress( APIView):
    """ Get all the goals progress under the enterprise."""
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated,]
    serializer_class = DaySerializer

    def get(self, request, format=None):
        # check user authentication group
        checkAdministratorGroupMixin(self)

        serializer = self.serializer_class(data= request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)
        
        enterprise_name = serializer.data["enterprise_name"].upper()

        try:
            enterprise = Enterprise.objects.get(name= enterprise_name)
        except Enterprise.DoesNotExist:
            content = {"detail": _(f"Enterprise {enterprise_name} does not exists.")}
            return Response(content, status.HTTP_400_BAD_REQUEST)

        if not user_belong_to_enterprise(request.user, enterprise):
            raise PermissionDenied
        if check_user_enterprise_status(request.user, enterprise) not in [Status.ACTIVE]:
            raise PermissionDenied

        statistics = []
        percentage_sum = 0
        try:
            filtered_goals = Goal.objects.filter(enterprise=enterprise)
            average = filtered_goals.count() if filtered_goals.count() > 0 else 1
            for goal in filtered_goals:
                # get goal performance analysis
                total, percentage, completed, submit, non_submit = get_goal_progress(goal)
                x = GoalSerializerLink(goal, context={"request": request})
                data = x.data
                data["required_reports_number"] = total
                data["completed"] = completed
                data["percentage"] = percentage
                data["submit"] = submit
                data["non_submit"] = non_submit
                percentage_sum +=percentage
                statistics.append(data)

            if not filtered_goals:
                return Response({"detail": _("No goal found.")},status.HTTP_200_OK)
            statistics.append({"average_percentage": int(percentage_sum/average)})
            return Response(statistics, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({"error": _(f"{e}")}, status.HTTP_400_BAD_REQUEST)

        
        
"""
    \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
    user progress VIEW SECTION
"""


class UserStatistic( APIView):
    """
    This view calculate the total progress of a user over an enterprise.
    """
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated,]
    queryset = get_user_model().objects.all()
    serializer_class = UserStatisticsSerializer
    lookup_field = "pk"

    def get(self, request,format=None):
        # check user authentication group
        checkAdministratorGroupMixin(self)
        
        serializer = self.serializer_class(data = request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)
        
        enterprise_name = serializer.data["enterprise_name"].upper()
        user_id = serializer.data['user_id']

        try:
            enterprise = Enterprise.objects.get(name=enterprise_name)
        except Enterprise.DoesNotExist:
            content = {"detail": _(f"This enterprise {enterprise_name} does not exists.")}
            return Response(content, status = status.HTTP_400_BAD_REQUEST)

        # authenticate the requester
        if not user_belong_to_enterprise(request.user, enterprise):
            raise PermissionDenied
        if check_user_enterprise_status(request.user, enterprise) not in [Status.ACTIVE]:
            raise PermissionDenied

        try:
            user = get_user_model().objects.get(id=user_id)
        except get_user_model().DoesNotExist:
            return Response({"detail": _(f"This user does not exists.")}, status.HTTP_400_BAD_REQUEST)
        
        # authenticate user
        if not user_belong_to_enterprise(request.user, enterprise):
            return Response({"detail": _(f"Invalid user.")}, status.HTTP_400_BAD_REQUEST)
        if check_user_enterprise_status(user, enterprise) not in [Status.ACTIVE]:
            return Response({"detail": _(f"Invalid user.")}, status.HTTP_400_BAD_REQUEST)
        
        data = {} # for activity

        try:
            activities = Activities.objects.filter(
            # activities analysis
                Q(employees__in=[user]), 
                goal__enterprise=enterprise
            )
            done_activities = [a for a in activities if Report.objects.filter(activity=a, submit_by=user, rate__in=[100,200,300,400,500]).exists()]
            incomplete_activities = [a for a in activities if Report.objects.filter(activity=a, submit_by=user).exists() == False]
            submit_activities = [a for a in activities if Report.objects.filter(activity=a, submit_by=user).exists()]
        
            data["total_activities_number"] = activities.count()
            data["submit_activities_number"] = len(submit_activities)
            data["submit_activities_list"] = ActivitySerializerLink(submit_activities, context={"request":request}, many=True).data 
            data["done_activities_number"]= len(done_activities)
            data["done_activities_list"] = ActivitySerializerLink(done_activities, context={"request": request}, many=True).data 
            data["non_submit_activities_number"] = len(incomplete_activities)
            data["non_submit_activities_list"] = ActivitySerializerLink(incomplete_activities, context={"request": request}, many=True).data
            average = 0
            list_of_done_activities = [Report.objects.get(activity=a, submit_by=user).rate for a in done_activities]
            sum_of_rate = sum(list_of_done_activities)
            total_rated_activity_report = len(done_activities) if len(done_activities)>0 else 1
            average = sum_of_rate / total_rated_activity_report
            #  this represent the average performance
            data["rated_activities_performance"] = set_average_rate(int(average))
            

            # goal analysis
            goals = Goal.objects.filter(
                Q(goal_manager=user), 
                enterprise=enterprise
            )
        
            done_goals = [a for a in goals if Report.objects.filter(goal=a, submit_by=user, rate__in = [100, 200, 300, 400, 500]).exists()]
            incomplete_goals = [a for a in goals if Report.objects.filter(goal=a, submit_by=user).exists() == False]
            submit_goals = [a for a in goals if Report.objects.filter(goal=a, submit_by=user).exists()]
            done_reports = [Report.objects.filter(goal=a, submit_by=user,) for a in done_goals]
            submit_reports =[Report.objects.filter(goal=a, submit_by=user,) for a in submit_goals]

            data["total_goals_number"] = goals.count()
            data["submit_goals_number"] = len(submit_goals)
            data["submit_goals_list"] = GoalSerializerLink(submit_reports, context={"request":request}, many=True).data
            data["done_goals_number"]= len(done_goals)
            data["done_goals_list"] = GoalSerializerLink(done_reports, context={"request": request}, many=True).data
            data["non_submit_goals_number"] = len(incomplete_goals)
            data["non_submit_goals_list"] = GoalSerializerLink(incomplete_goals, context={"request": request}, many=True).data

            average = 0
            list_of_done_goals = [Report.objects.get(goal=a, submit_by=user).rate for a in done_goals]
            sum_of_rate = sum(list_of_done_goals)
            total_rated_goal_report = len(done_goals) if len(done_goals) > 0 else 1

            average = sum_of_rate / total_rated_goal_report
            #  this represent the average performance
            data["rated_goals_performance"] = set_average_rate(int(average))


        except Exception as e:
            return Response({"errors": _(f"An error occurs while analyzing all user's goals: {e}.")}, status.HTTP_400_BAD_REQUEST)

        

        return Response(data, status.HTTP_200_OK)

        
class UserWeekStatistic( APIView):
    """
    This view evaluate the week performance of a user on week activities.
    """
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated,]
    serializer_class = UserWeekStatisticsSerializer

    def get(self, request, format=None):
        # check user authentication group
        checkAdministratorGroupMixin(self)
        
        serializer = self.serializer_class(data= request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)
        enterprise_name = serializer.data["enterprise_name"].upper()
        user_id = serializer.data["user_id"]
        year = serializer.data["year"]
        month_number = serializer.data["month_number"]
        week_number = serializer.data["week_number"]

        # get enterprise
        try:
            enterprise = Enterprise.objects.get(name= enterprise_name)
        except Enterprise.DoesNotExist:
            content={
                "detail": _(f"Enterprise {enterprise_name} does not exists.")
            }
            return Response(content, status= status.HTTP_400_BAD_REQUEST)
        
        # Check requester enterprise status
        if not user_belong_to_enterprise(request.user, enterprise):
            raise PermissionDenied
        if check_user_enterprise_status(request.user, enterprise) not in [Status.ACTIVE]:
            raise PermissionDenied
        
        try:
            user = get_user_model().objects.get(id=user_id)
        except get_user_model().DoesNotExist:
            return Response({"detail": _(f"This user does not exists.")}, status.HTTP_400_BAD_REQUEST)
        
        # authenticate user
        if not user_belong_to_enterprise(request.user, enterprise):
            return Response({"detail": _(f"Invalid user.")}, status.HTTP_400_BAD_REQUEST)
        if check_user_enterprise_status(user, enterprise) not in [Status.ACTIVE]:
            return Response({"detail": _(f"Invalid user.")}, status.HTTP_400_BAD_REQUEST)
        
        
        #  year validation
        if year < 2024 or year> 9999:
            content= {"detail": _(f"This year {year} is not valid")}
            return Response(content, status.HTTP_400_BAD_REQUEST)

        if month_number is None:
            pass
        else:
            # month validation
            if month_number < 1 or month_number > 12:
                content= {"detail": _(f"This month {month_number} is not valid")}
                return Response(content, status.HTTP_400_BAD_REQUEST)
        
        #  week_number validation
        if week_number not in get_month_info(year, month_number):
            content = {"detail": _(f"This week_number {week_number} is not valid")}
            return Response(content, status.HTTP_400_BAD_REQUEST)

        data = {}

        try:
            # get the first date of the week
            first_day_of_week = datetime(year, month_number, 1) + timedelta(days=(week_number - 1) * 7)
            first_day_of_week -= timedelta(days=first_day_of_week.weekday())  # Adjust to Monday
            # get the last day of the week
            last_day_of_week = first_day_of_week + timedelta(days=6)
            
            activities = Activities.objects.filter(
                Q(starting_date__date__lt= last_day_of_week) | Q(starting_date__date= last_day_of_week),
                Q(ending_date__date = first_day_of_week) | Q(ending_date__date__gt = first_day_of_week),
                Q(employees__in= [user]) ,
                goal__enterprise=enterprise,
            )

            done_activities = [a for a in activities if Report.objects.filter(activity=a, submit_by=user, rate__in=[100,200,300,400,500]).exists()]
            incomplete_activities = [a for a in activities if Report.objects.filter(activity=a, submit_by=user).exists() == False]
            submit_activities = [a for a in activities if Report.objects.filter(activity=a, submit_by=user).exists()]
        
            data["total_activities_number"] = activities.count()
            data["submit_activities_number"] = len(submit_activities)
            data["submit_activities_list"] = ActivitySerializerLink(submit_activities, context={"request":request}, many=True).data 
            data["done_activities_number"]= len(done_activities)
            data["done_activities_list"] = ActivitySerializerLink(done_activities, context={"request": request}, many=True).data 
            data["non_submit_activities_number"] = len(incomplete_activities)
            data["non_submit_activities_list"] = ActivitySerializerLink(incomplete_activities, context={"request": request}, many=True).data
            average = 0
            list_of_done_activities = [Report.objects.get(activity=a, submit_by=user).rate for a in done_activities]
            sum_of_rate = sum(list_of_done_activities)
            total_rated_activity_report = len(done_activities) if len(done_activities)>0 else 1
            average = sum_of_rate / total_rated_activity_report
            #  this represent the average performance
            data["rated_activities_performance"] = set_average_rate(int(average))
            
            # goal analysis
            goals = Goal.objects.filter(
                Q(starting_date__date__lt= last_day_of_week) | Q(starting_date__date= last_day_of_week),
                Q(ending_date__date = first_day_of_week) | Q(ending_date__date__gt = first_day_of_week),
                Q(goal_manager= user) ,
                enterprise=enterprise,
            )

            done_goals = [a for a in goals if Report.objects.filter(goal=a, submit_by=user, rate__in = [100, 200, 300, 400, 500]).exists()]
            incomplete_goals = [a for a in goals if Report.objects.filter(goal=a, submit_by=user).exists() == False]
            submit_goals = [a for a in goals if Report.objects.filter(goal=a, submit_by=user).exists()]
            done_reports = [Report.objects.filter(goal=a, submit_by=user,) for a in done_goals]
            submit_reports =[Report.objects.filter(goal=a, submit_by=user,) for a in submit_goals]

            data["total_goals_number"] = goals.count()
            data["submit_goals_number"] = len(submit_goals)
            data["submit_goals_list"] = GoalSerializerLink(submit_reports, context={"request":request}, many=True).data
            data["done_goals_number"]= len(done_goals)
            data["done_goals_list"] = GoalSerializerLink(done_reports, context={"request": request}, many=True).data
            data["non_submit_goals_number"] = len(incomplete_goals)
            data["non_submit_goals_list"] = GoalSerializerLink(incomplete_goals, context={"request": request}, many=True).data

            average = 0
            list_of_done_goals = [Report.objects.get(goal=a, submit_by=user).rate for a in done_goals]
            sum_of_rate = sum(list_of_done_goals)
            total_rated_goal_report = len(done_goals) if len(done_goals) > 0 else 1

            average = sum_of_rate / total_rated_goal_report
            #  this represent the average performance
            data["rated_goals_performance"] = set_average_rate(int(average))


            return Response(data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"errors": _(f"An error occurs: {e}.")}, status.HTTP_400_BAD_REQUEST)

        
class UserMonthStatistic( APIView):
    """
    This view evaluate the month performance of a user on month activities.
    """
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated,]
    serializer_class = UserMonthStatisticsSerializer

    def get(self, request, format=None):
        # check user authentication group
        checkAdministratorGroupMixin(self)
        
        serializer = self.serializer_class(data= request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)
        enterprise_name = serializer.data["enterprise_name"].upper()
        user_id = serializer.data["user_id"]
        year = serializer.data["year"]
        month_number = serializer.data["month_number"]

        # get enterprise
        try:
            enterprise = Enterprise.objects.get(name= enterprise_name)
        except Enterprise.DoesNotExist:
            content={
                "detail": _(f"Enterprise {enterprise_name} does not exists.")
            }
            return Response(content, status= status.HTTP_400_BAD_REQUEST)
        
        # Check requester enterprise status
        if not user_belong_to_enterprise(request.user, enterprise):
            raise PermissionDenied
        if check_user_enterprise_status(request.user, enterprise) not in [Status.ACTIVE]:
            raise PermissionDenied
        
        try:
            user = get_user_model().objects.get(id=user_id)
        except get_user_model().DoesNotExist:
            return Response({"detail": _(f"This user does not exists.")}, status.HTTP_400_BAD_REQUEST)
        
        # authenticate user
        if not user_belong_to_enterprise(request.user, enterprise):
            return Response({"detail": _(f"Invalid user.")}, status.HTTP_400_BAD_REQUEST)
        if check_user_enterprise_status(user, enterprise) not in [Status.ACTIVE]:
            return Response({"detail": _(f"Invalid user.")}, status.HTTP_400_BAD_REQUEST)
        
        
        #  year validation
        if year < 2024 or year> 9999:
            content= {"detail": _(f"This year {year} is not valid")}
            return Response(content, status.HTTP_400_BAD_REQUEST)

        # month validation
        if month_number < 1 or month_number > 12:
            content= {"detail": _(f"This month {month_number} is not valid")}
            return Response(content, status.HTTP_400_BAD_REQUEST)
        
        data = {}

        try:
            # get the first date of the month
            first_day_of_month = datetime(year, month_number, 1)
            # Calculate the last day of the month accurately
            last_day_of_month = (first_day_of_month + timedelta(days=31)).replace(day=1) - timedelta(days=1)

            activities = Activities.objects.filter(
                Q(starting_date__date__lt= last_day_of_month) | Q(starting_date__date= last_day_of_month),
                Q(ending_date__date = first_day_of_month) | Q(ending_date__date__gt = first_day_of_month),
                Q(employees__in = [user]),
                goal__enterprise=enterprise,
            )

            done_activities = [a for a in activities if Report.objects.filter(activity=a, submit_by=user, rate__in=[100,200,300,400,500]).exists()]
            incomplete_activities = [a for a in activities if Report.objects.filter(activity=a, submit_by=user).exists() == False]
            submit_activities = [a for a in activities if Report.objects.filter(activity=a, submit_by=user).exists()]
        
            data["total_activities_number"] = activities.count()
            data["submit_activities_number"] = len(submit_activities)
            data["submit_activities_list"] = ActivitySerializerLink(submit_activities, context={"request":request}, many=True).data 
            data["done_activities_number"]= len(done_activities)
            data["done_activities_list"] = ActivitySerializerLink(done_activities, context={"request": request}, many=True).data 
            data["non_submit_activities_number"] = len(incomplete_activities)
            data["non_submit_activities_list"] = ActivitySerializerLink(incomplete_activities, context={"request": request}, many=True).data
            average = 0
            list_of_done_activities = [Report.objects.get(activity=a, submit_by=user).rate for a in done_activities]
            sum_of_rate = sum(list_of_done_activities)
            total_rated_activity_report = len(done_activities) if len(done_activities)>0 else 1
            average = sum_of_rate / total_rated_activity_report
            #  this represent the average performance
            data["rated_activities_performance"] = set_average_rate(int(average))
            
            #  goal analysis
            goals = Goal.objects.filter(
                Q(starting_date__date__lt= last_day_of_month) | Q(starting_date__date= last_day_of_month),
                Q(ending_date__date = first_day_of_month) | Q(ending_date__date__gt = first_day_of_month),
                Q(goal_manager = user),
                enterprise=enterprise,
            )

            done_goals = [a for a in goals if Report.objects.filter(goal=a, submit_by=user, rate__in = [100, 200, 300, 400, 500]).exists()]
            incomplete_goals = [a for a in goals if Report.objects.filter(goal=a, submit_by=user).exists() == False]
            submit_goals = [a for a in goals if Report.objects.filter(goal=a, submit_by=user).exists()]
            done_reports = [Report.objects.filter(goal=a, submit_by=user,) for a in done_goals]
            submit_reports =[Report.objects.filter(goal=a, submit_by=user,) for a in submit_goals]

            data["total_goals_number"] = goals.count()
            data["submit_goals_number"] = len(submit_goals)
            data["submit_goals_list"] = GoalSerializerLink(submit_reports, context={"request":request}, many=True).data
            data["done_goals_number"]= len(done_goals)
            data["done_goals_list"] = GoalSerializerLink(done_reports, context={"request": request}, many=True).data
            data["non_submit_goals_number"] = len(incomplete_goals)
            data["non_submit_goals_list"] = GoalSerializerLink(incomplete_goals, context={"request": request}, many=True).data

            average = 0
            list_of_done_goals = [Report.objects.get(goal=a, submit_by=user).rate for a in done_goals]
            sum_of_rate = sum(list_of_done_goals)
            total_rated_goal_report = len(done_goals) if len(done_goals) > 0 else 1

            average = sum_of_rate / total_rated_goal_report
            #  this represent the average performance
            data["rated_goals_performance"] = set_average_rate(int(average))


            return Response(data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"errors": _(f"An error occurs: {e}.")}, status.HTTP_400_BAD_REQUEST)


class UserYearStatistic( APIView):
    """
    This view evaluate the year performance of a user over on activities.
    """
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated,]
    serializer_class = UserYearStatisticsSerializer

    def get(self, request, format=None):
        # check user authentication group
        checkAdministratorGroupMixin(self)
        
        serializer = self.serializer_class(data= request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)
        enterprise_name = serializer.data["enterprise_name"].upper()
        user_id = serializer.data["user_id"]
        year = serializer.data["year"]

        # get enterprise
        try:
            enterprise = Enterprise.objects.get(name= enterprise_name)
        except Enterprise.DoesNotExist:
            content={
                "detail": _(f"Enterprise {enterprise_name} does not exists.")
            }
            return Response(content, status= status.HTTP_400_BAD_REQUEST)
        
        # Check requester enterprise status
        if not user_belong_to_enterprise(request.user, enterprise):
            raise PermissionDenied
        if check_user_enterprise_status(request.user, enterprise) not in [Status.ACTIVE]:
            raise PermissionDenied
        
        try:
            user = get_user_model().objects.get(id=user_id)
        except get_user_model().DoesNotExist:
            return Response({"detail": _(f"This user does not exists.")}, status.HTTP_400_BAD_REQUEST)
        
        # authenticate user
        if not user_belong_to_enterprise(request.user, enterprise):
            return Response({"detail": _(f"Invalid user.")}, status.HTTP_400_BAD_REQUEST)
        if check_user_enterprise_status(user, enterprise) not in [Status.ACTIVE]:
            return Response({"detail": _(f"Invalid user.")}, status.HTTP_400_BAD_REQUEST)
        
        
        #  year validation
        if year < 2024 or year> 9999:
            content= {"detail": _(f"This year {year} is not valid")}
            return Response(content, status.HTTP_400_BAD_REQUEST)

       
        
        data = {}

        try:
            # get the first date of the month
            first_day_of_year = datetime(year, 1, 1)
            # Calculate the last day of the month accurately
            last_day_of_year = datetime(year, 12, 31)

            activities = Activities.objects.filter(
                Q(starting_date__date__lt= last_day_of_year) | Q(starting_date__date= last_day_of_year),
                Q(ending_date__date = first_day_of_year) | Q(ending_date__date__gt = first_day_of_year),
                Q(employees__in=[user]),
                goal__enterprise=enterprise,
            )

            done_activities = [a for a in activities if Report.objects.filter(activity=a, submit_by=user, rate__in=[100,200,300,400,500]).exists()]
            incomplete_activities = [a for a in activities if Report.objects.filter(activity=a, submit_by=user).exists() == False]
            submit_activities = [a for a in activities if Report.objects.filter(activity=a, submit_by=user).exists()]
        
            data["total_activities_number"] = activities.count()
            data["submit_activities_number"] = len(submit_activities)
            data["submit_activities_list"] = ActivitySerializerLink(submit_activities, context={"request":request}, many=True).data 
            data["done_activities_number"]= len(done_activities)
            data["done_activities_list"] = ActivitySerializerLink(done_activities, context={"request": request}, many=True).data 
            data["non_submit_activities_number"] = len(incomplete_activities)
            data["non_submit_activities_list"] = ActivitySerializerLink(incomplete_activities, context={"request": request}, many=True).data
            average = 0
            list_of_done_activities = [Report.objects.get(activity=a, submit_by=user).rate for a in done_activities]
            sum_of_rate = sum(list_of_done_activities)
            total_rated_activity_report = len(done_activities) if len(done_activities)>0 else 1
            average = sum_of_rate / total_rated_activity_report
            #  this represent the average performance
            data["rated_activities_performance"] = set_average_rate(int(average))
            
            # goal analysis
            goals = Goal.objects.filter(
                Q(starting_date__date__lt= last_day_of_year) | Q(starting_date__date= last_day_of_year),
                Q(ending_date__date = first_day_of_year) | Q(ending_date__date__gt = first_day_of_year),
                Q(goal_manager=user),
                enterprise=enterprise,
            )

            done_goals = [a for a in goals if Report.objects.filter(goal=a, submit_by=user, rate__in = [100, 200, 300, 400, 500]).exists()]
            incomplete_goals = [a for a in goals if Report.objects.filter(goal=a, submit_by=user).exists() == False]
            submit_goals = [a for a in goals if Report.objects.filter(goal=a, submit_by=user).exists()]
            done_reports = [Report.objects.filter(goal=a, submit_by=user,) for a in done_goals]
            submit_reports =[Report.objects.filter(goal=a, submit_by=user,) for a in submit_goals]

            data["total_goals_number"] = goals.count()
            data["submit_goals_number"] = len(submit_goals)
            data["submit_goals_list"] = GoalSerializerLink(submit_reports, context={"request":request}, many=True).data
            data["done_goals_number"]= len(done_goals)
            data["done_goals_list"] = GoalSerializerLink(done_reports, context={"request": request}, many=True).data
            data["non_submit_goals_number"] = len(incomplete_goals)
            data["non_submit_goals_list"] = GoalSerializerLink(incomplete_goals, context={"request": request}, many=True).data

            average = 0
            list_of_done_goals = [Report.objects.get(goal=a, submit_by=user).rate for a in done_goals]
            sum_of_rate = sum(list_of_done_goals)
            total_rated_goal_report = len(done_goals) if len(done_goals) > 0 else 1

            average = sum_of_rate / total_rated_goal_report
            #  this represent the average performance
            data["rated_goals_performance"] = set_average_rate(int(average))


            return Response(data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"errors": _(f"An error occurs: {e}.")}, status.HTTP_400_BAD_REQUEST)


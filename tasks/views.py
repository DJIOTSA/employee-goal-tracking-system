from django.db.models import Q
from rest_framework.parsers import MultiPartParser
from django.utils import timezone
import json
from .serializers import(
    GoalSerializer,
    GoalSerializerList,
    GoalListSerializer,
    GoalActivitiesSerializer,
    ActivitiesSerializer, 
    ActivitiesListSerializer,
    ReportSerializer,
    ReportEmployeeUpdateSerializer,
    ReportListSerializer,
    ReportDeleteSerializer,
    ActivitiesDeleteSerializer,
    GoalSetUserInChargeOfGoalSerializer,
    TasksListSerializer,
    GoalSetGoalManagerSerializer,
    ReportGoalCreateSerializer,
    ReportActivityCreateSerializer,
    GoalActivityReportListSerializer,
    ActivitiesCreateMulSerializer,
    ActivityMulUpdateSerializer,
    TasksRateResetSerializer,
    TaskUpdate2Serializer,
    ActivityAddUserInChargeSerializer,
    GoalUpdateSerializer,

)
from Notification.models import NotificationStatus, get_enterprise_active_administrator, create_notification

from rest_framework.exceptions import ValidationError
from EGT.serializers import UserSerializer
from payroll.models import  _subtract_completion_bonus
from .models import (
    Goal, 
    Activities, 
    Report,
    is_user_in_charge_of_activity,
    is_user_in_charge_of_goal,
    is_goal_managers,
    is_event_in_current_week,
    ReportStatus, # for goal and activity status
    Rate, # for report rate
    TaskCompletionStatus,
    
)

from datetime import datetime

from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from rest_framework import generics
from rest_framework import permissions, authentication

from EGT.permissions import (
    checkAdministratorGroupMixin,
    checkEmployeeAdminGroupMixin,
    checkAdministratorEmployeeGroupMixin,
    IS_EMPLOYEE_ADMIN,
)

from rest_framework.views import  APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination

from EGT.models import (
    user_belong_to_enterprise,
    Enterprise,
    check_user_enterprise_status,
    Status,
    check_user_status,
    MyUser,
    _get_user_profile,
    return_jsonfield_value,
)

ACTIVE = Status.ACTIVE
ACTIVITY = "A"
GOAL = "G"

from django.core.exceptions import PermissionDenied
from Chat.models import create_group_chat

import re

def extract_numbers(text:str):
    """Extracts all non-zero numbers from a string and returns them as a list."""
    
    if text is None:
        return []
    if type(text) != str:
        text = str(text)
    numbers = re.findall(r"\d+", text)  # Match digits
    return [int(num) for num in numbers if num != "0"]  # Convert and filter


# payroll
from payroll.models import tasks_bonus_management, tasks_bonus_subtraction_management

"""
    \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
    Goal VIEW SECTION
"""

class GoalCreateView(APIView):
    """ 
    Create a new goal for an enterprise. 
    
    this action can only be performed by an Administrator or 
    an employee with sub- administration privileges: admin
    """
    authentication_classes =(authentication.TokenAuthentication, authentication.SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Goal.objects.all()
    serializer_class = GoalSerializer
    lookup_field = 'pk'


    def post(self, request, format=None):
        # check user permission group
        check = checkEmployeeAdminGroupMixin(self)
        
        serializer = self.serializer_class(data = request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)
        
        enterprise = serializer.validated_data["enterprise"]
        employee_ids = serializer.validated_data["employee_ids"]
        created_by = serializer.validated_data.get("created_by")
        title = serializer.validated_data["title"]
        description = serializer.validated_data.get("description")
        starting_date = serializer.validated_data.get("starting_date")
        ending_date = serializer.validated_data.get("ending_date")
        attached_file = serializer.validated_data["attached_file"]
        attached_file1 = serializer.validated_data["attached_file1"]
        attached_file2 = serializer.validated_data["attached_file2"]
        bonus = serializer.validated_data.get("bonus")
        repeat = serializer.validated_data.get("repeat")
        important = serializer.validated_data.get("important")


        if check == IS_EMPLOYEE_ADMIN and request.user not in enterprise.employee_admins.all():
            raise PermissionDenied
        if not user_belong_to_enterprise(request.user, enterprise):
            raise PermissionDenied
        if check_user_enterprise_status(request.user, enterprise) not in [Status.ACTIVE]:
            raise PermissionDenied
        
        try:
            if employee_ids is None:
                return Response({
                    "detail": _("Enter valid users id"),
                    "status": _("FAILED")
                    },
                    status.HTTP_400_BAD_REQUEST
                )

            employee_ids_list = extract_numbers(employee_ids)
            employee_list = []

            if len(employee_ids_list) == 0:
                return Response({
                    "detail": _("Enter valid users ids"),
                    "status": _("FAILED")
                    },
                    status.HTTP_400_BAD_REQUEST
                )

            employee_list = [get_user_model().objects.get(id=e) for e in employee_ids_list if get_user_model().objects.filter(id=e).exists()]
            
            # avoid one by one iteration 
            active_users = [e for e in employee_list if check_user_enterprise_status(e, enterprise) == Status.ACTIVE]

            if active_users:
                goal = Goal.objects.create(
                    enterprise = enterprise,
                    created_by = request.user,
                    title = title,
                    description = description,
                    starting_date = starting_date,
                    ending_date = ending_date,
                    attached_file = attached_file,
                    attached_file1 = attached_file1,
                    attached_file2 = attached_file2,
                    bonus = bonus,
                    repeat = repeat,
                    important = important
                )
                goal.users_in_charge.set(active_users)
                goal.save()

                # create chat
                chat_name = f"goal_{goal.id}"
                chat =create_group_chat(name=chat_name, participants=active_users, enterprise=enterprise)
                
                for user in goal.users_in_charge.all():
                    create_notification( 
                        user = user,
                        message = _("New goal added"),
                        enterprise=goal.enterprise,
                        target = goal.get_absolute_url()
                    )
                try:
                    administrator, e = get_enterprise_active_administrator(enterprise)
                    for u in administrator:
                        if request.user != u:
                            user_profile = _get_user_profile(request.user)
                            user_codes = json.loads(user_profile.user_enterprise_code)
                            code: str
                            enterprise_name = goal.enterprise.name
                            # set user code
                            if enterprise_name in user_codes:
                                code = user_codes[enterprise_name]
                            create_notification( 
                                user = u,
                                message =  _(f"New goal added by: {code}"),
                                enterprise= goal.enterprise,
                                target = goal.get_absolute_url()
                            )
                except Exception as e:
                    pass

                content = {
                    "detail": _(f"New goal created for enterprise {goal.enterprise}")
                }
                return Response(content, status.HTTP_200_OK)
                
        except Exception as e:
            return Response({"detail":_(f"An error occur: {e}")}, status.HTTP_400_BAD_REQUEST)


class GoalList(generics.ListAPIView):
    """ 
    List all goal according to the user enterprise role.
    
    ser is enterprise administrator then return all goals of the enterprise.
    If user is enterprise employee then, return all employee goals under that enterprise.
    """
    authentication_classes =( authentication.TokenAuthentication, authentication.SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Goal.objects.all()
    serializer_class = GoalSerializerList
    pagination_class = PageNumberPagination
    lookup_field ='pk'

    
    def get(self, request,  format=None):
        # check user permission group
        checkAdministratorEmployeeGroupMixin(self)
        
        # get the enterprise_name
        enterprise_name = request.GET.get('enterprise_name', '').upper()

        # check if the enterprise exists
        try:
            enterprise = Enterprise.objects.get(name=enterprise_name)
        except Enterprise.DoesNotExist:
            content = {'detail': _(f"Enterprise '{enterprise_name}' does not exists.")}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)
        
        # check if the the user belong to the enterprise
        if user_belong_to_enterprise(request.user, enterprise) == False:
            raise PermissionDenied
        
        #check if the user is an active member of the enterprise
        if check_user_enterprise_status(request.user, enterprise) in [Status.DEACTIVATED, Status.SUSPENDED, None]:
            raise PermissionDenied

        # data to response
        goals = []
        # queryset
        list = Goal.objects.filter(Q(enterprise=enterprise))
        
        if list:
            goals = [goal.id for goal in list if is_user_in_charge_of_goal(request.user, goal)]

        goals = Goal.objects.filter(id__in = goals)

        page = self.paginate_queryset(goals)  # Apply pagination logic

        if page is not None:
            serializer = self.serializer_class(page, context={"request": request},  many=True)
            return self.get_paginated_response(serializer.data)

            
class GoalDetails( generics.RetrieveAPIView):
    """ Retrieve goal allow"""
    queryset = Goal.objects.all()
    serializer_class = GoalSerializerList
    lookup_field ="pk"
    authentication_classes =( authentication.TokenAuthentication, authentication.SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated,)


    def get(self, request, *args, **kwargs):
        # check user permission group
        checkAdministratorEmployeeGroupMixin(self)
        
        goal = self.get_object()

        if is_user_in_charge_of_goal(request.user, goal) == False:
            raise PermissionDenied
        
        serializer = self.get_serializer(goal)
        return Response(serializer.data)
        
        
class GoalUpdate(generics.RetrieveUpdateAPIView):
    """ Goal update view. 
        NOTE: the field enterprise REQUIRE THE NAME OF THE ENTERPRISE IS UPPERCASE
    """
    authentication_classes =( authentication.TokenAuthentication, authentication.SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Goal.objects.all()
    serializer_class = GoalUpdateSerializer
    parser_classes = [MultiPartParser]
    lookup_field = "pk"


    def perform_update(self, serializer):
        # check user permission group
        check = checkEmployeeAdminGroupMixin(self)
        
        obj = self.get_object()

        enterprise = obj.get_goal_enterprise()
        if check == IS_EMPLOYEE_ADMIN and self.request.user not in enterprise.employee_admins.all():
            raise PermissionDenied
        if check_user_enterprise_status(self.request.user, enterprise) not in [Status.ACTIVE]:
            raise PermissionDenied

        
        title = serializer.validated_data.get("title")
        goal_manager = serializer.validated_data.get("goal_manager")
        description = serializer.validated_data.get("description")
        starting_date = serializer.validated_data.get("starting_date")
        ending_date = serializer.validated_data.get("ending_date")
        attached_file = serializer.validated_data.get("attached_file")
        attached_file1 = serializer.validated_data.get("attached_file1")
        attached_file2 = serializer.validated_data.get("attached_file2")
        rate = serializer.validated_data.get("rate")
        bonus = serializer.validated_data.get("bonus")
        repeat = serializer.validated_data.get("repeat")
        importance = serializer.validated_data.get("importance")

        for u in obj.get_users_in_charge():
            create_notification( 
                user = u,
                message =  _(f"Goal updated."),
                enterprise=obj.get_goal_enterprise(),
                target = obj.get_absolute_url()
            )

        return serializer.save()


class GoalDelete(generics.RetrieveUpdateAPIView):
    authentication_classes =( authentication.TokenAuthentication, authentication.SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Goal.objects.all()
    serializer_class = GoalUpdateSerializer
    lookup_field = "pk"

    def get_queryset(self, request):
        # Access and utilize query parameters for filtering
        queryset = super().get_queryset(request)
    
        queryset = queryset.filter(is_deleted=False)
        return queryset

    def perform_update(self, serializer):
        # check user permission group
        checkAdministratorGroupMixin(self)
        
        is_deleted = serializer.validated_data('is_deleted')

        return serializer.save(is_deleted=True)


class GoalSetUserInCharge( APIView):
    """
    This view update the goal objects by adding a many to many relationship 
    with the selected users and the goal.
    """
    authentication_classes = [ authentication.TokenAuthentication, authentication.SessionAuthentication,]
    permission_classes = [permissions.IsAuthenticated,]
    serializer_class = GoalSetUserInChargeOfGoalSerializer

    def post(self, request, format=None):
        # check user permission group
        check = checkEmployeeAdminGroupMixin(self)

        serializer = self.serializer_class(data = request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)
        
        goal_id = serializer.data['goal_id']
        users = serializer.data['users']

        #  check if a goal with that title exist under that enterprise
        try:
            goal = Goal.objects.get(id=goal_id)
        except Goal.DoesNotExist:
            content = {"detail": _(f"Invalid goal.")}
            return Response(content, status.HTTP_400_BAD_REQUEST)

        
        if check == IS_EMPLOYEE_ADMIN and request.user not in goal.enterprise.employee_admins.all():
            raise PermissionDenied
        # Check if the user is an active user of the platform
        if check_user_enterprise_status(self.request.user, goal.enterprise)not in [Status.ACTIVE]:
            raise PermissionDenied
        
        
        
        #  Check if users belong to enterprise
        items = []

        if users is None:
            return Response({
                "detail": _("Enter valid users id"),
                "status": _("FAILED")
                },
                status.HTTP_400_BAD_REQUEST
            )

        employee_ids_list = extract_numbers(users)
        employee_list = []

        if len(employee_ids_list) == 0:
            return Response({
                "detail": _("Enter valid users ids"),
                "status": _("FAILED")
                },
                status.HTTP_400_BAD_REQUEST
            )

        enterprise_active_users = [get_user_model().objects.get(id=e) for e in employee_ids_list if get_user_model().objects.filter(id=e).exists() and check_user_enterprise_status(get_user_model().objects.get(id=e), goal.enterprise) == Status.ACTIVE]
        

        item = [ u  for u in enterprise_active_users if u not in goal.users_in_charge.all()]
        if item:
            goal.users_in_charge.add(*item)
            goal.save()
            
            content = {
                'detail': _(f"Successfully added! {item}"),
                "status": _("SUCCESS")
            }
            return Response(content, status.HTTP_201_CREATED)
        else:
            # Handle case where no users meet the criteria
            return Response(
                {"detail": _("Nobody was added!(field: users). Please enter in string user ids(separated with anything except a number) that is currently active in the enterprise and is not in the goal users_in_charge  field.")},
                status.HTTP_200_OK
            )


class GoalRemoveUserInCharge(  APIView):
    """
    This view update the goal objects by removing the many to many relationship 
    with the selected users and the goal.
    """
    queryset = Goal.objects.all()
    authentication_classes = [ authentication.TokenAuthentication, authentication.SessionAuthentication,]
    permission_classes = [permissions.IsAuthenticated,]
    serializer_class = GoalSetUserInChargeOfGoalSerializer

    def post(self, request, format=None):
        # check user permission group
        check = checkEmployeeAdminGroupMixin(self)

        serializer = self.serializer_class(data = request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)
    
        goal_id = serializer.data['goal_id']
        users = serializer.data['users']

        #  check if a goal with that title exist under that enterprise
        try:
            goal = Goal.objects.get(id=goal_id)
        except Goal.DoesNotExist:
            content = {"detail": _("Invalid goal")}
            return Response(content, status.HTTP_400_BAD_REQUEST)
        
        if check == IS_EMPLOYEE_ADMIN and request.user not in goal.enterprise.employee_admins.all():
            raise PermissionDenied
        # Check if the user is an active user of the platform
        if check_user_enterprise_status(self.request.user, goal.enterprise)not in [Status.ACTIVE]:
            raise PermissionDenied
        
        
        
        #  Check if users belong to enterprise
        items = []

        if users is None:
            return Response({
                "detail": _("Enter valid users id"),
                "status": _("FAILED")
                },
                status.HTTP_400_BAD_REQUEST
            )

        employee_ids_list = extract_numbers(users)

        if len(employee_ids_list) == 0:
            return Response({
                "detail": _("Enter valid users ids"),
                "status": _("FAILED")
                },
                status.HTTP_400_BAD_REQUEST
            )

        enterprise_active_users = [get_user_model().objects.get(id=e) for e in employee_ids_list if get_user_model().objects.filter(id=e).exists() and check_user_enterprise_status(get_user_model().objects.get(id=e), goal.enterprise) == Status.ACTIVE]
        
        item = [ u  for u in enterprise_active_users if u in goal.users_in_charge.all()]
        if item:
            goal.users_in_charge.remove(*item)
            goal.save()
            
            content = {
                'detail': _(f"Successfully removed! {item}"),
                "status": _("SUCCESS")
            }
            return Response(content, status.HTTP_201_CREATED)
        else:
            # Handle case where no users meet the criteria
            return Response(
                {"detail": _("Nobody was removed!(field: users). Please enter in string user ids(separated with anything except a number) that is currently active in the enterprise and is not in the goal users_in_charge  field.")},
                status.HTTP_200_OK
            )
    

class GoalSetGoalManager( APIView):
    """ 
    This view set one of the goal.users_in_charge of a goal as the goal 
    manager given him the authorization to submit the final goal report. 
    Which will represent the final solution of the entire team working on the 
    goal.
    """
    authentication_classes = [ authentication.TokenAuthentication, authentication.SessionAuthentication,]
    permission_classes = [permissions.IsAuthenticated,]
    serializer_class = GoalSetGoalManagerSerializer


    def post(self, request, format=None):
        # check user permission group
        check = checkEmployeeAdminGroupMixin(self)
        
        serializer = self.serializer_class(data = request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)
        
        goal_id = serializer.validated_data['goal_id']
        user_id = serializer.validated_data['user_id']
        
        #  check if a goal with that title exist under that enterprise
        try:
            goal = Goal.objects.get(id=goal_id)
        except Goal.DoesNotExist:
            content = {"detail": _(f"Invalid goal!")}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)
        
        if check == IS_EMPLOYEE_ADMIN and request.user not in goal.enterprise.employee_admins.all():
            raise PermissionDenied
        # Check if the user is an active user of the platform
        if not user_belong_to_enterprise(request.user, goal.enterprise):
            raise PermissionDenied
        if check_user_enterprise_status(request.user, goal.enterprise)not in [Status.ACTIVE]:
            raise PermissionDenied
        
       
        try:
            user = get_user_model().objects.get(id=user_id)
            # Check if the user is an active user of the platform
            if not user_belong_to_enterprise(user, goal.enterprise):
                raise PermissionDenied
            if check_user_enterprise_status(user, goal.enterprise)not in [Status.ACTIVE]:
                raise PermissionDenied
            
            if user not in goal.users_in_charge.all():
                goal.users_in_charge.add(user)
                
            goal.goal_manager = user
            goal.save()
            content  ={"detail": _(f"Goal_manager set successfully!")}
            return Response(content, status.HTTP_200_OK)
        except Exception as e:
            return Response({"Exception":_(f"{e}!")}, status.HTTP_400_BAD_REQUEST)
            # pass


"""
    \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
    Activities VIEW SECTION
"""

class ActivityCreateView(APIView):
    """ 
    CREATE ONE ACTIVITY and assign it to ONE OR MULTIPLE EMPLOYEES

    employee_ids = "[<list of user ids>]"
        eg: employee_ids = [1,2,3,4,5,6]
    """
    authentication_classes =(authentication.TokenAuthentication, authentication.SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Activities.objects.all()
    serializer_class = ActivitiesCreateMulSerializer
    parser_classes = [MultiPartParser]
    lookup_field = 'pk'


    def post(self, request, format=None):
        # check user permission group
        check  = checkEmployeeAdminGroupMixin(self)

        serializer = self.serializer_class(data= request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)
        
        goal = serializer.validated_data["goal"]
        employee_ids = serializer.validated_data["employee_ids"]
        title = serializer.validated_data["title"].upper()
        description = serializer.validated_data["description"]
        starting_date = serializer.validated_data["starting_date"]
        ending_date = serializer.validated_data["ending_date"]
        attached_file = serializer.validated_data["attached_file"]
        attached_file1 = serializer.validated_data["attached_file1"]
        attached_file2 = serializer.validated_data["attached_file2"]
        bonus = serializer.validated_data["bonus"]
        repeat = serializer.validated_data["repeat"]
        created_by = serializer.validated_data["created_by"]

        if check == IS_EMPLOYEE_ADMIN and self.request.user not in goal.enterprise.employee_admins.all():
            raise PermissionDenied
        if check_user_enterprise_status(self.request.user, goal.enterprise) not in [Status.ACTIVE]:
            raise PermissionDenied
        # check if the user has the right to create a goal activity.
        if not is_goal_managers(self.request.user, goal):
            raise PermissionDenied

        if employee_ids is None:
            return Response({
                "detail": _("Enter valid users id"),
                "status": _("FAILED")
                },
                status.HTTP_400_BAD_REQUEST
            )

        employee_ids_list = extract_numbers(employee_ids)
        employee_list = []

        if len(employee_ids_list) == 0:
            return Response({
                "detail": _("Enter valid users ids"),
                "status": _("FAILED")
                },
                status.HTTP_400_BAD_REQUEST
            )

        employee_list = [get_user_model().objects.get(id=e) for e in employee_ids_list if get_user_model().objects.filter(id=e).exists()]
        
        # avoid one by one iteration 
        active_users = [e for e in employee_list if check_user_enterprise_status(e, goal.enterprise) == Status.ACTIVE]
        # get active administrator
        
        if active_users:
            activity=Activities.objects.create(
                goa=goal,
                title=title,
                description=description,
                starting_date=starting_date,
                ending_date=ending_date,
                attached_file=attached_file,
                attached_file1=attached_file1,
                attached_file2=attached_file2,
                bonus=bonus,
                repeat=repeat,
                created_by=request.user
            )
            activity.employees.add(*[e for e in active_users])
            activity.save()

            # bulk addition
            goal.users_in_charge.add(*[e for e in active_users if e not in goal.users_in_charge.all()])
            goal.save()

            
            for user in active_users:
                create_notification( 
                    user = user,
                    message =  _("New activity added"),
                    enterprise=activity.goal.enterprise,
                    target = activity.get_absolute_url()
                )
            try:
                administrator, e = get_enterprise_active_administrator(goal.enterprise)
                for u in administrator:
                    if request.user != u:
                        user_profile = _get_user_profile(request.user)
                        user_codes = json.loads(user_profile.user_enterprise_code)
                        code: str
                        enterprise_name = goal.enterprise.name
                        # set user code
                        if enterprise_name in user_codes:
                            code = user_codes[enterprise_name]
                        create_notification( 
                            user = u,
                            message =  _(f"New activity added by: {code}"),
                            enterprise=activity.goal.enterprise,
                            target = activity.get_absolute_url()
                        )
            except Exception as e:
                pass
            return Response(
                {
                    "detail":_("activity created."),
                    "status":  _("SUCCESS")
                },
                status.HTTP_201_CREATED
            )

        return Response(
            {
                "detail": _("Something when wrong."),
                "status": _("SUCCESS")
            }, 
            status.HTTP_400_BAD_REQUEST
        )


class ActivitiesList(generics.ListAPIView):
    """ 
    List all activities.
    
    For administrators :    list all activities of the enterprise
    For goal_manager:       list all activities of the goal.
    For sub-administrators: list all activities of the enterprise
    employee:               list all activities related to him

    All those users (administrators, sub-administrators, goal_manager, employee) must belong to the enterprise
    """
    authentication_classes =( authentication.TokenAuthentication, authentication.SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = PageNumberPagination
    queryset = Activities.objects.all()
    serializer_class = ActivitiesListSerializer


    def get(self, request,  format=None):
        # check user permission group
        checkAdministratorEmployeeGroupMixin(self)
        
        
        # get the enterprise_name
        enterprise_name = request.GET.get("enterprise_name", "")
        enterprise_name = enterprise_name.upper()

        # check if the enterprise exists
        try:
            enterprise = Enterprise.objects.get(name=enterprise_name)
        except Enterprise.DoesNotExist:
            content = {'detail': _(f"Enterprise '{enterprise_name}' does not exists.")}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)
        
        # check if the the user belong to the enterprise
        if user_belong_to_enterprise(request.user, enterprise) == False:
            raise PermissionDenied
        
        #check if the user is an active member of the enterprise
        if check_user_enterprise_status(request.user, enterprise) in [Status.DEACTIVATED, Status.SUSPENDED, None]:
            raise PermissionDenied

        # data to response
        activities = []
        # queryset
        list = Activities.objects.filter(Q(goal__enterprise=enterprise))
        
        if list:
            activities = [activity.id for activity in list if is_user_in_charge_of_activity(request.user, activity)]

        activities = Activities.objects.filter(id__in= activities)

        page = self.paginate_queryset(activities)  # Apply pagination logic

        if page is not None:
            serializer = self.serializer_class(page, context={"request": request},  many=True)
            return self.get_paginated_response(serializer.data)


class GoalActivitiesList(generics.ListAPIView):
    """ List all activities of a specific goal """
    authentication_classes =( authentication.TokenAuthentication, authentication.SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Activities.objects.all()
    pagination_class = PageNumberPagination
    serializer_class = ActivitiesListSerializer
    

    def get(self, request, format=None):
        # check user permission group
        checkAdministratorEmployeeGroupMixin(self)
        
        enterprise_name = request.GET.get('enterprise_name', "").upper()
        goal_id = request.GET.get("goal_id", "")

        try:
            enterprise = Enterprise.objects.get(name=enterprise_name)
            if check_user_enterprise_status(request.user, enterprise) not in [Status.ACTIVE]:
                raise PermissionDenied
        except Enterprise.DoesNotExist:
            content = {"detail": _(f"Enterprise '{enterprise_name}' des not exists.")}
            return Response(content, status.HTTP_400_BAD_REQUEST)
        
        try:
            goal = Goal.objects.get(enterprise=enterprise, id= goal_id)
            if not is_user_in_charge_of_goal(request.user, goal):
                raise PermissionDenied
        except Goal.DoesNotExist:
            content = {"detail": _(f"This goal is not a goal of enterprise '{enterprise_name}'.")}
            return Response(content, status.HTTP_400_BAD_REQUEST)
        
        # get and serialize the all activities of the goal
        queryset = Activities.objects.filter(goal=goal)
        list = [a.id for a in queryset if is_user_in_charge_of_activity(request.user, a)]

        queryset = Activities.objects.filter(id__in=list)

        page = self.paginate_queryset(queryset)  # Apply pagination logic

        if page is not None:
            serializer = self.serializer_class(page, context={"request": request},  many=True)
            return self.get_paginated_response(serializer.data)     


class ActivitiesDetails( generics.RetrieveAPIView):
    """
    Retrieve activities after authenticating the user.
    """
    authentication_classes =( authentication.TokenAuthentication, authentication.SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Activities.objects.all()
    serializer_class = ActivitiesListSerializer
    lookup_field ="pk"

    def get(self, request, *args, **kwargs):
        # check user permission group
        checkAdministratorEmployeeGroupMixin(self)
        
        activity = self.get_object()

        if not is_user_in_charge_of_activity(request.user, activity):
            raise PermissionDenied
        

        return super().get(request, format=None)


class ActivitiesMulUpdate( generics.RetrieveUpdateAPIView):
    """ Update activity assigned to many users """
    authentication_classes =( authentication.TokenAuthentication, authentication.SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Activities.objects.all()
    serializer_class = ActivityMulUpdateSerializer
    lookup_field = "pk"

    def perform_update(self, serializer):
        # check user permission group
        check = checkEmployeeAdminGroupMixin(self)
        
        obj = self.get_object()
        if check_user_enterprise_status(self.request.user, obj.get_activity_enterprise()) not in [Status.ACTIVE]:
            raise PermissionDenied
        
        title = serializer.validated_data["title"].upper()
        description = serializer.validated_data.get("description")
        starting_date = serializer.validated_data.get("starting_date")
        ending_date = serializer.validated_data.get("ending_date")
        attached_file = serializer.validated_data.get("attached_file")
        attached_file1 = serializer.validated_data.get("attached_file1")
        attached_file2 = serializer.validated_data.get("attached_file2")
        bonus = serializer.validated_data.get("bonus")
        repeat = serializer.validated_data.get("repeat")

        for u in obj.get_employees():
            create_notification( 
                user = u,
                message =  _(f"Activity updated."),
                enterprise=obj.get_activity_enterprise(),
                target = obj.get_absolute_url()
            )
        
        return serializer.save(title= title.upper())


class ActivityAddUserInCharge(APIView):
    """ Add users to activity employees (user in charge of activity)  """
    authentication_classes =( authentication.TokenAuthentication, authentication.SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Activities.objects.all()
    serializer_class = ActivityAddUserInChargeSerializer
    lookup_field = "pk"

    def post(self, request, format=None):
        checkEmployeeAdminGroupMixin(self)

        serializer = self.serializer_class(data= request.data)
        if not serializer.is_valid():
            return Response(serializer.errors,  status.HTTP_400_BAD_REQUEST)
        
        activity_id = serializer.data["activity_id"]
        users = serializer.data["users"]

        try:
            activity = Activities.objects.get(id=activity_id)
        except Activities.DoesNotExist:
            return Response(
                {
                    "detail":_("Invalid activity id"),
                },
                status.HTTP_400_BAD_REQUEST
            )
        try:    
            employee_ids_list = extract_numbers(users)
            employee_list = []

            if len(employee_ids_list) == 0:
                return Response({
                    "detail": _("Enter valid users ids"),
                    "status": _("FAILED")
                    },
                    status.HTTP_400_BAD_REQUEST
                )

            employee_list = [get_user_model().objects.get(id=e) for e in employee_ids_list if get_user_model().objects.filter(id=e).exists()]
            if len(employee_list) == 0:
                return Response({
                    "detail": _("Enter valid users ids"),
                    "status": _("FAILED")
                    },
                    status.HTTP_400_BAD_REQUEST
                )
            
            to_add = [e for e in employee_list if check_user_enterprise_status(e, activity.goal.enterprise) == Status.ACTIVE and e not in activity.employees.all()]
            
            # avoid one by one iteration 
            activity.employees.add(*to_add)
            activity.save()
            for u in to_add:
                create_notification( 
                    user = u,
                    message =  _(f"Activity {activity.title} added."),
                    enterprise=activity.goal.enterprise,
                    target = activity.get_absolute_url()
                )
            return Response(
                {
                    "detail": _(f"successfully added {[e.id for e in to_add]}")
                },
                status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"detail":_("An error occur while extracting or adding users to activity employees field")}, 
                status.HTTP_400_BAD_REQUEST
            )


class ActivityRemoveUserInCharge(APIView):
    """ remove user from activity employees (user in charge)  """
    authentication_classes =( authentication.TokenAuthentication, authentication.SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Activities.objects.all()
    serializer_class = ActivityAddUserInChargeSerializer
    lookup_field = "pk"

    def post(self, request, format=None):
        checkEmployeeAdminGroupMixin(self)

        serializer = self.serializer_class(data= request.data)
        if not serializer.is_valid():
            return Response(serializer.errors,  status.HTTP_400_BAD_REQUEST)
        
        activity_id = serializer.data["activity_id"]
        users = serializer.data["users"]

        try:
            activity = Activities.objects.get(id=activity_id)
        except Activities.DoesNotExist:
            return Response(
                {
                    "detail":_("Invalid activity id"),
                },
                status.HTTP_400_BAD_REQUEST
            )
        try:    
            employee_ids_list = extract_numbers(users)
            employee_list = []

            if len(employee_ids_list) == 0:
                return Response({
                    "detail": _("Enter valid users ids"),
                    "status": _("FAILED")
                    },
                    status.HTTP_400_BAD_REQUEST
                )

            employee_list = [get_user_model().objects.get(id=e) for e in employee_ids_list if get_user_model().objects.filter(id=e).exists()]
            if len(employee_list) == 0:
                return Response({
                    "detail": _("Enter valid users ids"),
                    "status": _("FAILED")
                    },
                    status.HTTP_400_BAD_REQUEST
                )
            to_remove = [e for e in employee_list if check_user_enterprise_status(e, activity.goal.enterprise) == Status.ACTIVE and e in activity.employees.all()]
            
            # avoid one by one iteration 
            activity.employees.remove(*to_remove)
            activity.save()

            for u in to_remove:
                create_notification( 
                    user = u,
                    message =  _(f"Activity {activity.title} removed."),
                    enterprise=activity.goal.enterprise,
                    target = activity.get_absolute_url()
                )
            return Response(
                {
                    "detail": _(f"successfully removed {[e.id for e in to_remove]}")
                },
                status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"detail":_("An error occur while extracting or adding users to activity employees field")}, 
                status.HTTP_400_BAD_REQUEST
            )



class ActivitiesDelete( generics.RetrieveUpdateAPIView):
    """ Change activity status  """
    authentication_classes =( authentication.TokenAuthentication, authentication.SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Activities.objects.all()
    serializer_class = ActivitiesDeleteSerializer
    lookup_field = "pk"

    def perform_update(self, serializer):
        # check user permission group
        checkAdministratorGroupMixin(self)

        obj = self .get_object()
        enterprise = obj.get_report_enterprise()
        if not user_belong_to_enterprise(self.request.user, enterprise):
            raise PermissionDenied
        if check_user_enterprise_status(self.request.user, enterprise) not in [Status.ACTIVE]:
            raise PermissionDenied

        is_deleted = serializer.validated_data('is_deleted')

        return serializer.save(is_deleted=True)



"""
    \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
    Report VIEW SECTION
"""

class ReportGoalCreateView( generics.CreateAPIView):
    """ Creating a GOAL report  """
    authentication_classes =( authentication.TokenAuthentication, authentication.SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Report.objects.all()
    serializer_class = ReportGoalCreateSerializer
    lookup_field = 'pk'


    def post(self, request, format=None):
        # check user permission group
        checkAdministratorEmployeeGroupMixin(self)

        serializer = self.serializer_class(data = request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)
        
        report = serializer.validated_data["report"]
        # date_of_submission = serializer.validated_data.get("date_of_submission")
        # option = serializer.validated_data.get("option")
        # submit_by = serializer.validated_data.get("submit_by")
        goal = serializer.validated_data.get("goal")
        # repeat = serializer.validated_data.get("repeat")
        # repetition_num = serializer.validated_data.get("repetition_num")
        
        # Initialize submit late status to false
        submit_late = False

        
        if check_user_enterprise_status(self.request.user, goal.enterprise) not in [Status.ACTIVE]:
            raise PermissionDenied
        
        if goal.goal_manager is None and self.request.user in goal.users_in_charge.all():
            goal.goal_manager = self.request.user
            goal.save()
        if self.request.user != goal.goal_manager:
            raise PermissionDenied
        
        # make sure the you can only create one report for one target
        if Report.objects.filter(option=GOAL, goal=goal, submit_by=self.request.user).exists():
            return Response(
                {
                    "detail": _(f"You can not submit more than one(1) report for a single target.")
                },
                status.HTTP_200_OK
            )
        
        try:
            # get submit late value
            end = goal.ending_date
            today = timezone.now()
            submit_late = today > end
            
            # update target completion status
            goal.is_done = TaskCompletionStatus.SUBMIT
            goal.save()

            report, created = Report.objects.get_or_create(
                report = report,   
                submit_late= submit_late, 
                submit_by= self.request.user, 
                option=GOAL, 
                repeat_option = goal.repeat,
                repetition_num = goal.repetition_num
            )

            return Response(
                {
                    "detail": _("Report crated."),
                    "status": _("SUCCESS")
                },
                status.HTTP_400_BAD_REQUEST
            )
        
        except Exception as e:
            return Response({"detail": e}, status.HTTP_400_BAD_REQUEST)
            

class ReportActivityCreateView(APIView):
    """ Creating An ACTIVITY report """
    authentication_classes =( authentication.TokenAuthentication, authentication.SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Report.objects.all()
    serializer_class = ReportActivityCreateSerializer
    lookup_field = 'pk'


    def post(self, request, format=None):
        # check user permission group
        checkAdministratorEmployeeGroupMixin(self)
        
        serializer = self.serializer_class(data = request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)

        report = serializer.validated_data["report"] # report file
        # option = serializer.validated_data["option"] # option ("A")
        activity = serializer.validated_data["activity"] # activity object

        submit_late = False

        if not user_belong_to_enterprise(request.user, activity.goal.enterprise):
            raise PermissionDenied
        if check_user_enterprise_status(request.user, activity.goal.enterprise) not in [Status.ACTIVE]:
            raise PermissionDenied
        
        if activity:
            if request.user not in activity.employees.all():
                raise PermissionDenied
        
        # make sure the you can only create one report for one target
        if Report.objects.filter(option=ACTIVITY, activity=activity, submit_by=request.user).exists():
            return Response(
                {
                    "detail": _(f"You can not submit more than one(1) report for a single target.")
                },
                status.HTTP_200_OK
            )
            
        # check if the report was submitted late
        begin = activity.starting_date
        end = activity.ending_date
        today = timezone.now()
        submit_late = today > end
        
        if request.user in activity.employees.all() and request.user not in activity.submit_employees.all():
            activity.submit_employees.add(request.user)
            activity.save()

        try:
            obj = Report.objects.create(
            report = report,
            option = ACTIVITY,
            activity = activity,
            submit_late = submit_late,
            submit_by = request.user,
            repeat_option = activity.repeat,
            repetition_num = activity.repetition_num
            )
            return Response(
                {
                    "status": _("SUCCESS"),
                    "detail": _("Report CREATED"),
                } ,status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"detail":_(f"An error occur: {e}")}, status.HTTP_400_BAD_REQUEST)
        

class ReportList(generics.ListAPIView):
    """ Get Enterprise report list """
    authentication_classes =( authentication.TokenAuthentication, authentication.SessionAuthentication)
    permission_classes = (permissions.IsAdminUser ,permissions.IsAuthenticated,)
    queryset = Report.objects.all()
    serializer_class = ReportListSerializer
    pagination_class = PageNumberPagination
    lookup_field ="pk"

    def get(self, request, format=None):
        # check user permission group
        check = checkEmployeeAdminGroupMixin(self)
        
        enterprise_name = request.GET.get("enterprise_name", '').upper()

        try:
            enterprise = Enterprise.objects.get(name= enterprise_name)
        except Enterprise.DoesNotExist:
            return Response({"detail": _("Invalid enterprise name")}, status.HTTP_400_BAD_REQUEST)
        if check == IS_EMPLOYEE_ADMIN and request.user not in enterprise.employee_admins.all():
            raise PermissionDenied
        if not user_belong_to_enterprise(request.user, enterprise):
            raise PermissionDenied
        if check_user_enterprise_status(request.user, enterprise) not in [Status.ACTIVE]:
            raise PermissionDenied
        
        list_a = []
        list_g = []
        reports =  Report.objects.filter(
            (Q(option=ACTIVITY) & Q(activity__goal__enterprise=enterprise)) | (Q(option=GOAL) & Q(goal__enterprise=enterprise))
        )

        if reports:
            list_a = [r.id for r in reports if r.option==ACTIVITY and is_user_in_charge_of_activity(request.user, r.activity) == True]
            list_g = [i.d for i in reports if i.option==GOAL and is_user_in_charge_of_goal(request.user, i.goal) == True]
        
        list_a.extend(list_g)
        queryset = Report.objects.filter(id__in=list_a)

        page = self.paginate_queryset(queryset)  # Apply pagination logic

        if page is not None:
            serializer = self.serializer_class(page, context={"request": request},  many=True)
            return self.get_paginated_response(serializer.data)
            
        
class ReportDetails(generics.RetrieveAPIView):
    """ Retrieve report detail"""
    authentication_classes =( authentication.TokenAuthentication, authentication.SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Report.objects.all()
    serializer_class = ReportListSerializer
    lookup_field ="pk"

    def get(self, request, *args, **kwargs):
        # check user permission group
        checkAdministratorEmployeeGroupMixin(self)

        instance = self.get_object()
        if instance.activity != None:
            if check_user_enterprise_status(request.user, instance.activity.goal.enterprise) not in [ACTIVE]:
                raise PermissionDenied
            if not is_user_in_charge_of_activity(request.user, instance.activity):
                raise PermissionDenied
        if instance.goal != None:
            if check_user_enterprise_status(request.user, instance.goal.enterprise) not in [ACTIVE]:
                       raise PermissionDenied
            if not is_user_in_charge_of_goal(request.user, instance.goal):
                raise PermissionDenied
        
        return super().get(request, *args, **kwargs)


class ReportUpdate(generics.RetrieveUpdateAPIView):
    """ 
    Perform a report file change.
    Retrieve and update an existing report objects.
    only for user who created a report
    """
    authentication_classes =( authentication.TokenAuthentication, authentication.SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Report.objects.all()
    serializer_class = ReportEmployeeUpdateSerializer
    lookup_field = "pk"


    def perform_update(self, serializer):
        # check user permission group
        checkAdministratorEmployeeGroupMixin(self)

        # get report object form url pk
        obj = self.get_object()
        # get report enterprise belonging
        enterprise = obj.get_report_enterprise()
        # authenticate the user
        if not user_belong_to_enterprise(self.request.user, enterprise):
            raise PermissionDenied
        if check_user_enterprise_status(self.request.user, enterprise) not in [Status.ACTIVE]:
            raise PermissionDenied
        if self.request.user != obj.get_report_submit_by():
            raise PermissionDenied
        
        # get report
        report = serializer.validated_data.get("report")
        submit_late = serializer.validated_data.get("submit_late")
        # update submit late
        target = obj.get_report_task()
        today = timezone.now()

        submit_late = today > target.ending_date  # Check only once for late submission

        return serializer.save(submit_late=submit_late)
    

class ReportDelete( generics.RetrieveUpdateAPIView):
    authentication_classes =( authentication.TokenAuthentication, authentication.SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Report.objects.all()
    serializer_class = ReportDeleteSerializer
    lookup_field = "pk"

    def perform_update(self, serializer):
        # check user permission group
        checkAdministratorGroupMixin(self)

        obj = self.get_object()
        enterprise = obj.get_report_enterprise()
        if not user_belong_to_enterprise(self.request.user, enterprise):
            raise PermissionDenied
        if check_user_enterprise_status(self.request.user, enterprise) not in [Status.ACTIVE]:
            raise PermissionDenied
        is_deleted = serializer.validated_data.get("is_deleted")

        return serializer.save(is_deleted=True)
        

class Tasks(generics.ListAPIView):
    """ List all the non completed tasks of the enterprise """
    authentication_classes =( authentication.TokenAuthentication, authentication.SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Report.objects.all()
    serializer_class = ReportListSerializer
    pagination_class = PageNumberPagination
    lookup_field = "pk"

    def get(self, request, format=None):
        # check user permission group
        check = checkEmployeeAdminGroupMixin(self)

        enterprise_name  = request.GET.get("enterprise_name", '').upper()

        try:
            enterprise = Enterprise.objects.get(name=enterprise_name)
        except Enterprise.DoesNotExist:
            content= {"detail": _(f"Enterprise {enterprise_name} does not exists.")}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)
        
        # authenticate the user
        if check == IS_EMPLOYEE_ADMIN and request.user not in enterprise.employee_admins.all():
            raise PermissionDenied
        if not user_belong_to_enterprise(request.user, enterprise):
            raise PermissionDenied
        if check_user_enterprise_status(request.user, enterprise) not in [Status.ACTIVE]:
            raise PermissionDenied
        
        tasks = []

        # get the list of non rated reports
        activity_reports = Report.objects.filter(
            rate=None,
            option=ACTIVITY,
            activity__goal__enterprise = enterprise,
        )
        goal_reports = Report.objects.filter(
            rate=None,
            option=GOAL,
            goal__enterprise = enterprise,
        )

        task1 = [r.id for r in activity_reports if is_user_in_charge_of_activity(request.user, r.activity)]

        task2 = [r.id for r in goal_reports if is_goal_managers(request.user, r.goal)]
        task2.extend(task1)

        queryset = Report.objects.filter(id__in=task2)

        page = self.paginate_queryset(queryset)  # Apply pagination logic

        if page is not None:
            serializer = self.serializer_class(page, context={"request": request},  many=True)
            return self.get_paginated_response(serializer.data)
        

 
class TasksCompleted(generics.ListAPIView): 
    """ List enterprise administrator completed tasks """
    authentication_classes =(authentication.TokenAuthentication, authentication.SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Report.objects.all()
    serializer_class = ReportListSerializer
    pagination_class = PageNumberPagination
    lookup_field = "pk"

    def get(self, request, format=None):
        # check user permission group
        check = checkEmployeeAdminGroupMixin(self)
            
        enterprise_name  = request.GET.get("enterprise_name", '').upper()

        try:
            enterprise = Enterprise.objects.get(name=enterprise_name)
        except Enterprise.DoesNotExist:
            content= {"detail": _(f"Enterprise {enterprise_name} does not exists.")}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)
        
        # authenticate the user
        if check == IS_EMPLOYEE_ADMIN and request.user not in enterprise.employee_admins.all():
            raise PermissionDenied
        if not user_belong_to_enterprise(request.user, enterprise):
            raise PermissionDenied
        if check_user_enterprise_status(request.user, enterprise) not in [Status.ACTIVE]:
            raise PermissionDenied
        
        tasks = []
        allowed_rate= [100, 200, 300, 400, 500]
        # get the list of non rated reports
        activity_reports = Report.objects.filter(
            option=ACTIVITY,
            activity__goal__enterprise = enterprise,
        ).exclude(rate=None)

        task1 = [r.id for r in activity_reports if is_user_in_charge_of_activity(request.user, r.activity)]

        goal_reports = Report.objects.filter(
            option=GOAL,
            goal__enterprise = enterprise,
        ).exclude(rate=None)


        task2 = [r.id for r in goal_reports if is_user_in_charge_of_goal(request.user, r.goal)]

        task2.extend(task1)
        
        queryset = Report.objects.filter(id__in=task2)

        page = self.paginate_queryset(queryset)  # Apply pagination logic

        if page is not None:
            serializer = self.serializer_class(page, context={"request": request},  many=True)
            return self.get_paginated_response(serializer.data)


class TaskUpdate(APIView):
    """ 
    Set activity or goal rate including a comment about the target result.    
    """
    authentication_classes =(authentication.TokenAuthentication, authentication.SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Report.objects.all()
    serializer_class =    TaskUpdate2Serializer
    lookup_field = "pk"


    def post(self, request, format=None):
        # check user permission group
        check = checkEmployeeAdminGroupMixin(self)
        #  validate the serializer
        serializer = self.serializer_class(data = request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)
        pk = serializer.validated_data["pk"]
        rate = serializer.validated_data["rate"]
        comment = serializer.validated_data["comment"]
        try:
            obj  = Report.objects.get(id = pk)
        except Report.DoesNotExist:
            return Response(
                {
                    "detail": _("Invalid report id.")
                },
                status.HTTP_404_NOT_FOUND
            )
        enterprise = obj.get_report_enterprise()
        # check user authorizations
        if check == IS_EMPLOYEE_ADMIN and request.user not in enterprise.employee_admins.all():
            raise PermissionDenied
        if not user_belong_to_enterprise(request.user, enterprise):
            raise PermissionDenied
        if check_user_enterprise_status(request.user, enterprise) not in [Status.ACTIVE]:
                raise PermissionDenied
        
        #  Validate rate value
        allow_rate = [0, 100, 200, 300, 400, 500]
        if rate not in allow_rate:
                return Response(
                    {
                        "detail":_("Invalid rate value. Allowed rate values are: 0, 100, 200, 300, 400 and 500.")
                    }, 
                    status.HTTP_400_BAD_REQUEST
                )   
            
        # try:    
        target = obj.get_report_task()
        is_goal = True if obj.option==GOAL else False
        submit_late = obj.get_report_submit_late() 
        report_status_list = [ReportStatus.ACCEPTED, ReportStatus.PENDING, ReportStatus.PAID]
        preview_report_status = obj.get_report_status() # get the current report status
        a = _("Target completed and the completion bonus was assigned.")
        b = _("Target completed.")

        if is_goal:
            """ for activities with single employee and goals """
            if preview_report_status in [ReportStatus.PAID] and target.is_done in [TaskCompletionStatus.SUBMIT] and obj.transaction_id != None:
                """ For report that was aet to retry after a report review """
                obj.rate = rate
                obj.comment = comment
                obj.rated_by = request.user
                obj.save()
                if rate in [100, 200, 300, 400, 500]:
                    target.is_done = TaskCompletionStatus.COMPLETED
                    target.save()
                return Response(
                        {
                            "detail": _("Report rate updated"),
                            "status": _("SUCCESS")
                        },
                        status.HTTP_200_OK
                    )

            elif preview_report_status in [ReportStatus.REJECTED] and target.is_done in [TaskCompletionStatus.COMPLETED] and obj.transaction_id != None and obj.rate == Rate.NULL:
                #  FOR REPORT THAT WAS REVIEWED AND the target bonus was refunded
                return Response(
                    {
                        "detail": _("This target is done. you can not perform any operation on it"),
                        "status": _('FAILED')
                    },
                    status.HTTP_200_OK
                )
            
            elif submit_late == False and rate not in [Rate.NULL, None] and preview_report_status not in report_status_list:
                """ For user that completed the task with the required rate and within the required time """
                # update report instance
                obj.rate = rate
                obj.comment = comment
                obj.rated_by = request.user
                obj.report_status = ReportStatus.ACCEPTED
                obj.save()
                target.status = ReportStatus.ACCEPTED
                target.is_done= TaskCompletionStatus.COMPLETED
                target.save()
                if tasks_bonus_management(obj): 
                    """ task completed and completion bonus assigned."""
                    # success bonus credited
                    # notify the user
                    
                    x = a if obj.get_bonus() > 0.0 else b
                    return Response(
                        {
                            "detail": x,
                            "status": _("SUCCESS")
                        },
                        status.HTTP_200_OK
                    )
                else:
                    #  Task completed
                    # notify the user
                    return Response(
                        {
                            "detail": b,
                            "status": _("SUCCESS")
                        },
                        status.HTTP_200_OK
                    )
                
            elif submit_late == True and rate not in [Rate.NULL, None] and preview_report_status not in report_status_list:
                obj.rate = rate
                obj.comment = comment
                obj.rated_by = request.user
                obj.report_status = ReportStatus.REJECTED
                obj.save()
                target.status = ReportStatus.REJECTED
                target.is_done = TaskCompletionStatus.COMPLETED
                target.save()
                
                return Response(
                    {
                        "detail": _("Task successfully updated."),
                        "status": _("SUCCESS")
                    },
                    status = status.HTTP_200_OK
                )

            elif submit_late == False and rate not in [Rate.NULL, None] and preview_report_status in [ReportStatus.ACCEPTED]:
                """ For users who completed the task and have a report rate update """
                obj.rate = rate
                obj.comment = comment
                obj.rated_by = request.user
                obj.save()
                state = tasks_bonus_management(obj)
                if state: # to avoid negative bonus
                    """ task completed and completion bonus assigned."""
                    # success bonus credited
                    # notify the user
                    
                    x = a if obj.get_bonus() > 0.0 else b
                    return Response(
                        {
                            "detail": x,
                            "status": _("SUCCESS")
                        },
                        status.HTTP_200_OK
                    )

                # NOTIFY THE USER
                return Response(
                        {
                            "detail": _("Target evaluation updated successfully"),
                            "status": _("SUCCESS")
                        },
                        status.HTTP_200_OK
                )
        
            elif submit_late == False and rate in [Rate.NULL, None] and preview_report_status in [ReportStatus.ACCEPTED]:
                """ For users who completed the task but did not request for the target completion  bonus withdrawal"""
                target.status = ReportStatus.REJECTED
                target.save()
                # update report instance
                obj.rate = rate
                obj.comment = comment
                obj.rated_by = request.user
                obj.report_status = ReportStatus.REJECTED
                obj.save()
                
                try:
                    if tasks_bonus_subtraction_management(obj):
                        # notify the user
                        return Response(
                                {
                                    "detail": _("Target evaluation updated successfully"),
                                    "status": _("SUCCESS")
                                },
                                status.HTTP_200_OK
                        )
                    return Response(
                                {
                                    "detail": _("Target evaluation updated failed."),
                                    "status": _("FAILED")
                                },
                                status.HTTP_200_OK
                        )
                except Exception as e:
                    return Response(
                        {
                            "detail": _(f"An error occur: {e}"),
                            "status": _("FAILED")
                        },
                        status.HTTP_400_BAD_REQUEST
                    )
                
            elif submit_late == False and rate in [Rate.NULL, None] and preview_report_status in [ReportStatus.PENDING, ReportStatus.PAID]:
                """ This for people that completed the task and got paid and after a review, the report is rejected """
                return Response(
                    {
                        "detail": _("This operation can not be perform using the update operation. Instead apply for a report review operation."),
                        "status": _("FAILED")
                    },
                    status.HTTP_200_OK
                )

            elif submit_late == False and rate not in [Rate.NULL, None] and preview_report_status in [ReportStatus.PENDING, ReportStatus.PAID] and target.is_done not in [TaskCompletionStatus.COMPLETED]:
                obj.rate = rate
                obj.comment = comment
                obj.rated_by = request.user
                obj.save()
                target.is_done = TaskCompletionStatus.COMPLETED
                target.status = preview_report_status
                target.save()

                return Response(
                        {
                            "detail": _(f"Task completed."),
                            "status": _("SUCCESS")
                        },
                        status.HTTP_200_OK
                )
                
            else:
                # update report rate
                obj.rate = rate
                obj.comment = comment
                obj.rated_by = request.user
                obj.report_status = ReportStatus.REJECTED
                obj.save()
                # update ta
                target.status = ReportStatus.REJECTED
                target.save()
                # NOTIFY THE USER
                return Response(
                    {
                        "detail": _("Target evaluation updated successfully"),
                        "status": _("SUCCESS")
                    },
                    status.HTTP_200_OK
                )           
                
        else:
            """ for activities with multiple users """
            submit_by = obj.get_report_submit_by()
            is_activity =isinstance(target, Activities) # check if the target if actually and activity
            s_num = target.submit_employees.all().count() # number of user who submit their target report
            e_num = target.employees.all().count() # number of user in charge of the target
            submit_employees = target.submit_employees.all() # employees that submit the target report


            if is_activity and submit_by in submit_employees:

                if preview_report_status in [ReportStatus.PAID] and obj.rate in [Rate.NULL] and submit_by in target.sold_to.all() and obj.transaction_id != None:
                    """ For report that was set to retry after a report review """
                    obj.rate = rate
                    obj.comment = comment
                    obj.rated_by = request.user
                    obj.save()

                    return Response(
                            {
                                "detail": _("Report rate updated"),
                                "status": _("SUCCESS")
                            },
                            status.HTTP_200_OK
                        )

                elif preview_report_status in [ReportStatus.REJECTED] and obj.rate in [Rate.NULL] and submit_by not in target.sold_to.all() and obj.transaction_id != None:
                    return Response(
                        {
                            "detail": _("This target is done. you can not perform any operation on it"),
                            "status": _('FAILED')
                        },
                        status.HTTP_400_BAD_REQUEST
                    )

                elif submit_late == False and rate not in [Rate.NULL, None] and preview_report_status not in report_status_list:
                    """ for user that have not yet completed the task """
                    # update report
                    obj.rate = rate
                    obj.comment = comment
                    obj.rated_by = request.user
                    obj.report_status = ReportStatus.ACCEPTED
                    obj.save()
                    # update target
                    target.status= ReportStatus.ACCEPTED
                    target.save()

                    try:
                        # assign bonus completion
                        if tasks_bonus_management(obj): # to avoid negative bonus
                            """ task completed and completion bonus assigned."""
                            # success bonus credited
                            # notify the user
                            a = _("Target completed and the completion bonus was assigned.")
                            b = _("Target completed.")
                            x = a if obj.get_bonus() > 0 else b
                            return Response(
                                {
                                    "detail": x,
                                    "status": _("SUCCESS")
                                },
                                status.HTTP_200_OK
                            )
                        else:
                            # notify the user
                            return Response(
                                {
                                    "detail": b,
                                    "status": _("SUCCESS")
                                },
                                status.HTTP_200_OK
                            )
                    
                    except Exception as e:
                        return Response(
                            {
                                "detail": _(f"An error occur {e}"),
                                "status": _("FAILED")
                            },
                            status = status.HTTP_400_BAD_REQUEST
                        )

                elif submit_late == False and rate in [Rate.NULL, None] and preview_report_status in [ReportStatus.PENDING, ReportStatus.PAID]:
                    """ This for people that completed the task and got paid and after a review, the report is rejected """
                    return Response(
                        {
                            "detail": _("This operation can not be perform using the update operation. Instead apply a report review"),
                            "status": _("FAILED")
                        },
                        status.HTTP_200_OK
                    )
                
                elif submit_late == False and rate not in [Rate.NULL, None] and preview_report_status in [ReportStatus.PENDING, ReportStatus.PAID]:
                    """ Since after a report review the report and target status remain non-change but the target is set as non-finish """
                    obj.rate = rate
                    obj.comment = comment
                    obj.rated_by = request.user
                    obj.save()
                    target.submit_employees.add(submit_by)
                    target.save()

                    return Response(
                        {
                            "detail": _("UPDATED."),
                            "status": _("SUCCESS")
                        },
                        status.HTTP_200_OK
                    )

                elif submit_late == False and rate not in [Rate.NULL, None] and preview_report_status in [ReportStatus.ACCEPTED]:
                    """" This is for user which completed the target and has not initiated a completion bonus completion and have a good rate update """
                    obj.rate = rate
                    obj.comment = comment
                    obj.rated_by = request.user
                    obj.report_status = ReportStatus.ACCEPTED
                    obj.save()

                    return Response(
                        {
                            "detail": _(f"Tasks rate updated."),
                            "status": _("SUCCESS")
                        },
                        status = status.HTTP_200_OK
                    )

                elif submit_late == False and rate in [Rate.NULL, None] and preview_report_status in [ReportStatus.ACCEPTED]:
                    """ This is for user which completed the target and has not initiated a completion bonus completion and have a bad rate update """
                    target.status = ReportStatus.REJECTED
                    target.save()
                    # update report instance
                    report_status =  ReportStatus.REJECTED# change the status of the task to non complete
                    obj.rate = rate
                    obj.comment = comment
                    obj.rated_by = request.user
                    obj.report_status = ReportStatus.REJECTED
                    obj.save()
                    
                    try:
                        if tasks_bonus_subtraction_management(obj):
                            # notify the user
                            return Response(
                                    {
                                        "detail": _("Target evaluation updated updated successfully"),
                                        "status": _("SUCCESS")
                                    },
                                    status.HTTP_200_OK
                            )
                    except Exception as e:
                        return Response(
                            {
                                "detail": _(f"An error occur: {e}"),
                                "status": _("FAILED")
                            },
                            status.HTTP_400_BAD_REQUEST
                        )
                    
                elif submit_late == True and rate not in [Rate.NULL, None] and preview_report_status not in report_status_list:
                    """ For user who submit the report late and have a good result """
                    report_status = ReportStatus.REJECTED
                    obj.rate = rate
                    obj.comment = comment
                    obj.rated_by = request.user
                    obj.report_status = ReportStatus.REJECTED
                    obj.save()
                    target.status = ReportStatus.REJECTED
                    if s_num == e_num:
                        target.is_done = TaskCompletionStatus.COMPLETED
                    target.save()
                    
                    return Response(
                        {
                            "detail": _("Task successfully updated."),
                            "status": _("SUCCESS")
                        },
                        status = status.HTTP_200_OK
                    )
                
                else:
                    """ For users who submit late and have bad grade """
                    report_status = ReportStatus.REJECTED
                    obj.rate = rate
                    obj.comment = comment
                    obj.rated_by = request.user
                    obj.report_status = ReportStatus.REJECTED
                    obj.save()
                    target.status = ReportStatus.REJECTED
                    target.status.save()

                    return Response(
                        {
                            "detail": _("Task successfully updated."),
                            "status": _("SUCCESS")
                        },
                        status = status.HTTP_200_OK
                    )
            
            return Response(
                {
                    "detail": _("This target have and issue."),
                    "status": _('FAILED')
                },
                status.HTTP_400_BAD_REQUEST
            )
            
        
class TaskRateReset(APIView):
    """ 
    Set activity or goal rate including a comment about the target result.
    And handle task bonus completion once.

    This view operate only on reports with PENDING AND PAID status.
    And is use to set task as non-finish and and reject the report result(on the target instance),
    if retry is set to true. 

    And, to reject report status(on the task instance) and refund the target completion bonus
    (
    target.is_done= TaskCompletionStatus.COMPLETED
    target.status = None
    )

    Note: Retry field (boolean) indicate if the task should be assigned back to the user or not
    """
    authentication_classes =( authentication.TokenAuthentication, authentication.SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Report.objects.all()
    serializer_class = TasksRateResetSerializer

    lookup_field = "pk"

    def post(self, request, format=None):
        # check user permission group
        checkAdministratorGroupMixin(self)
        
        serializer = self.serializer_class(data = request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, Status.HTTP_400_BAD_REQUEST)
        
        report_id = serializer.validated_data["report_id"]
        rate = serializer.validated_data["rate"]
        comment = serializer.validated_data["comment"]
        retry = serializer.validated_data['retry']

        try:
            obj = Report.objects.get(id= report_id)
        except Report.DoesNotExist:
            return Response({"detail":_("Report does not exists.")}, status.HTTP_400_BAD_REQUEST)
        
        # get report enterprise belonging
        enterprise = obj.get_report_enterprise()

        if not user_belong_to_enterprise(request.user, enterprise):
            raise PermissionDenied
        if check_user_enterprise_status(request.user, enterprise) not in [Status.ACTIVE]:
            raise PermissionDenied
        
        allow_rate = [0, 100, 200, 300, 400, 500]
        if rate not in allow_rate:
            return Response(
                {
                    "detail":_("Invalid rate value. Allowed rate values are: 0, 100, 200, 300, 400 and 500.")
                }, 
                status.HTTP_400_BAD_REQUEST
            )
        
        try:    
            target = obj.get_report_task()
            is_goal = True if obj.option==GOAL else False
            submit_late = obj.get_report_submit_late() 
            user_profile = _get_user_profile(obj.get_report_submit_by())
            preview_report_status = obj.get_report_status() # get the current report status
            a = _("Target completed and the completion bonus was assigned.")
            b = _("Target completed.")

            if is_goal:
                """ for activities with single employee and goals """
                if preview_report_status in [ReportStatus.PENDING]:
                    return Response(
                            {
                                "detail": _("Can not perform any operation on this target now, try later."),
                                "status": _('FAILED')
                            },
                            status.HTTP_400_BAD_REQUEST
                        )
                
                elif submit_late == False and rate in [Rate.NULL, None] and preview_report_status in [ReportStatus.PAID] and target.status in [ReportStatus.PAID]:
                    """ This for people that completed the task and got paid and after a review, the report is rejected """
                    if retry: # then mark the task as non-finish target to allow the user to correct his mistake
                        # update report instance
                        obj.rate = rate
                        obj.comment = comment
                        obj.save()
                        target.is_done= TaskCompletionStatus.SUBMIT
                        target.save()
                        #  notify the user
                        return Response(
                            {
                            "detail": _("Successful! The target had set to non-finish and the target completion bonus was not refunded."),
                            "status": _("SUCCESS")
                            },
                            status.HTTP_200_OK
                        )

                    """ 
                    Otherwise refund the target bonus and:
                    - set reject both report and target
                    - set the target is_done to completed but with 0 performance
                    """
                    state = _subtract_completion_bonus(user_profile, obj)
                    if state== True:
                        obj.rate = rate
                        obj.comment = comment
                        obj.report_status = ReportStatus.REJECTED
                        obj.save()
                        target.is_done= TaskCompletionStatus.COMPLETED
                        target.status = ReportStatus.REJECTED
                        target.save()
                        
                        return Response(
                            {
                                "detail": _("Successful! The completion bonus was refunded and the target had set as non-completed with Null as performance."),
                                "status": _("SUCCESS")
                            },
                            status.HTTP_200_OK
                        )
                    else:
                        return Response(
                            {
                                "detail": _(f"An error occur: {state}"),
                                "status": _("FAILED")
                            },
                            status.HTTP_400_BAD_REQUEST
                        )
                
                elif preview_report_status in [ ReportStatus.PAID] and target.is_done in [TaskCompletionStatus.SUBMIT]:
                    """ For task that was set to retry"""
                    obj.rate = rate
                    obj.comment = comment
                    obj.rated_by = request.user
                    obj.save()
                    if rate not in [Rate.NULL, None]:
                        target.is_done = TaskCompletionStatus.COMPLETED
                        target.save()
                    return Response(
                            {
                                "detail": _(f"Report rate updated."),
                                "status": _("SUCCESS")
                            },
                            status.HTTP_400_BAD_REQUEST
                    )
                
                elif preview_report_status in [ReportStatus.REJECTED] and target.status in [ReportStatus.REJECTED] and target.is_done in [TaskCompletionStatus.COMPLETED] and obj.transaction_id != None:
                    #  FOR REPORT THAT WAS REVIEWED AND SET AS COMPLETED NULL RATE (the money was refunded but the task cannot be evaluated)
                    return Response(
                        {
                            "detail": _("This target is done. you can not perform any operation on it"),
                            "status": _('FAILED')
                        },
                        status.HTTP_200_OK
                    )
                
                else:
                    return Response(
                        {
                            "detail": _("Invalid report! This report don't meet the requirements to perform a review on it."),
                            "status": _("FAILED")
                        },
                        status.HTTP_200_OK
                    )           
                
            else:
                """ for activities with multiple users """
                submit_by = obj.get_report_submit_by()
                is_activity =isinstance(target, Activities) # check if the target if actually and activity
                s_num = target.submit_employees.all().count() # number of user who submit their target report
                e_num = target.employees.all().count() # number of user in charge of the target
                submit_employees = target.submit_employees.all() # employees that submit the target report

                if is_activity and submit_by in submit_employees:

                    if preview_report_status in [ReportStatus.PENDING]:
                        return Response(
                            {
                                "detail": _("Can not perform any operation on this target now, try later."),
                                "status": _('FAILED')
                            },
                            status.HTTP_400_BAD_REQUEST
                        )
                    
                    elif submit_late == False and rate in [Rate.NULL, None] and preview_report_status in [ReportStatus.PAID] and submit_by in target.sold_to.all():
                        """ This for people that completed the task and got paid and after a review, the report was rejected """
                        # update report instance
                        if retry: 
                            obj.rate = Rate.NULL
                            obj.comment = comment
                            obj.save()
                            #  notify the user
                            return Response(
                                {
                                "detail": _("Successful! The target had set to non-finish and the target completion bonus was not refunded."),
                                "status": _("SUCCESS")
                                },
                                status.HTTP_200_OK
                            )

                        # Otherwise refund the target bonus
                        state = _subtract_completion_bonus(user_profile, obj)
                        if state == True:
                            obj.rate = Rate.NULL
                            obj.comment = comment
                            obj.save()
                            target.sold_to.remove(submit_by)
                            target.save()
                            obj.report_status = ReportStatus.REJECTED
                            obj.save()
                            # notify the user
                            return Response(
                                {
                                    "detail": _("Successful! The completion bonus was refunded and the target had set as non-completed with Null as performance."),
                                    "status": _("SUCCESS")
                                },
                                status.HTTP_200_OK
                            )
                        else:
                            return Response(
                                {
                                    "detail": _(f"An error occur: {state}"),
                                    "status": _("FAILED")
                                },
                                status.HTTP_400_BAD_REQUEST
                            )

                    elif preview_report_status in [ReportStatus.PAID] and obj.rate in [Rate.NULL] and submit_by in target.sold_to.all() and obj.transaction_id != None:
                        """ For report that was set to retry after a report review """
                        obj.rate = rate
                        obj.comment = comment
                        obj.rated_by = request.user
                        obj.save()

                        return Response(
                                {
                                    "detail": _("Report rate updated"),
                                    "status": _("SUCCESS")
                                },
                                status.HTTP_200_OK
                            )
                  
                    elif preview_report_status in [ReportStatus.REJECTED] and target.status in [ReportStatus.REJECTED] and obj.transaction_id != None and submit_by not in target.sold_to.all() and obj.rate == Rate.NULL:
                        #  FOR REPORT THAT WAS REVIEWED AND SET AS COMPLETED NULL RATE (the money was refunded but the task cannot be evaluated)
                        return Response(
                            {
                                "detail": _("This target is done. you can not perform any operation on it"),
                                "status": _('FAILED')
                            },
                            status.HTTP_200_OK
                        )               
                    
                    else:
                        return Response(
                            {
                                "detail": _("Invalid report! This report don't meet the requirements to perform a review on it."),
                                "status": _("FAILED")
                            },
                            status.HTTP_200_OK
                        )
                
                # otherwise there is an issue with the report
                return Response(
                    {
                        "detail": _("There is an issue with the report."),
                        "status": _("FAILED")
                    },
                    status.HTTP_400_BAD_REQUEST
                )
            
        except Exception as e:
            return Response({
                "detail":  _(f"An error occur: {e}")}, status.HTTP_400_BAD_REQUEST)            
              

class GoalReportList(generics.ListAPIView):
    """ Get the goal report including all report  updates """
    authentication_classes =( authentication.TokenAuthentication, authentication.SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Report.objects.all()
    serializer_class = ReportListSerializer
    pagination_class = PageNumberPagination
    lookup_field = "pk"


    def get(self, request, format=None):
        # check user permission group
        checkAdministratorEmployeeGroupMixin(self)
        
        goal_id =request.GET.get("target_id", "")
        enterprise_name =request.GET.get("enterprise_name", "").upper()

        try:
            goal = Goal.objects.get(id=goal_id)
        except Goal.DoesNotExist:
            content = {"detail": _("This goal does not exists.")}
            return Response(content, status.HTTP_400_BAD_REQUEST)
        try:
            enterprise = Enterprise.objects.get(name=  enterprise_name)
        except Enterprise.DoesNotExist:
            content = {"detail": _("This enterprise does not exists.")}
            return Response(content, status.HTTP_400_BAD_REQUEST)
        
        # authenticate the user
        if not user_belong_to_enterprise(request.user, enterprise):
            raise PermissionDenied
        if check_user_enterprise_status(request.user, enterprise) not in [Status.ACTIVE]:
            raise PermissionDenied
        if not is_user_in_charge_of_goal(request.user, goal):
            raise PermissionDenied
        
        #  get goal reports list
        queryset = Report.objects.filter(
            option=GOAL,
            goal= goal,
            goal__enterprise = enterprise
        )

        page = self.paginate_queryset(queryset)  # Apply pagination logic

        if page is not None:
            serializer = self.serializer_class(page, context={"request": request},  many=True)
            return self.get_paginated_response(serializer.data)


class ActivityReportList(generics.ListAPIView):
    """ Get all the report of the selected activity """
    authentication_classes =( authentication.TokenAuthentication, authentication.SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Report.objects.all()
    serializer_class = ReportListSerializer
    pagination_class = PageNumberPagination

    def get(self, request, format=None):
        # check user permission group
        checkAdministratorEmployeeGroupMixin(self)
        
        activity_id =request.GET.get("target_id", "")
        enterprise_name =request.GET.get("enterprise_name", "").upper()

        try:
            activity = Activities.objects.get(id=activity_id)
        except Activities.DoesNotExist:
            content = {"detail": _("This activity does not exists.")}
            return Response(content, status.HTTP_400_BAD_REQUEST)
        try:
            enterprise = Enterprise.objects.get(name=  enterprise_name)
        except Enterprise.DoesNotExist:
            content = {"detail": _("This enterprise does not exists.")}
            return Response(content, status.HTTP_400_BAD_REQUEST)
        
        # authenticate the user
        if not user_belong_to_enterprise(request.user, enterprise):
            raise PermissionDenied
        if check_user_enterprise_status(request.user, enterprise) not in [Status.ACTIVE]:
            raise PermissionDenied
        if not is_user_in_charge_of_activity(request.user, activity):
            raise PermissionDenied
        
        #  get goal reports list
        queryset = Report.objects.filter(
            option=ACTIVITY,
            activity= activity,
            activity__goal__enterprise = enterprise
        )

        page = self.paginate_queryset(queryset)  # Apply pagination logic

        if page is not None:
            serializer = self.serializer_class(page, context={"request": request},  many=True)
            return self.get_paginated_response(serializer.data)


from django.urls import path

# Goal views
from .views import (
    GoalCreateView, 
    GoalList, 
    GoalDetails, 
    GoalUpdate, 
    GoalDelete,
    GoalSetUserInCharge,
    GoalRemoveUserInCharge,
    GoalSetGoalManager,
    GoalActivitiesList,


    ActivityCreateView,
    ActivitiesList, 
    ActivitiesDetails, 
    ActivitiesMulUpdate,
    ActivitiesDelete,
    ActivityAddUserInCharge,
    ActivityRemoveUserInCharge,


    ReportActivityCreateView,
    ReportGoalCreateView,
    ReportList,
    GoalReportList,
    ActivityReportList, 
    ReportDetails, 
    ReportUpdate, 
    ReportDelete,


    Tasks,
    TasksCompleted,
    TaskUpdate,
    TaskRateReset,

    

)


urlpatterns = [
     # Goal
    path("goal/create/", GoalCreateView.as_view(), name="create Goal"),
    path("goal/list/", GoalList.as_view(), name="list of all Goal"),
    path("goal/<int:pk>/detail/", GoalDetails.as_view(), name="goal-detail"),
    path("goal/<int:pk>/update/", GoalUpdate.as_view(), name="update Goal"),
    path("goal/delete/<int:pk>/delete/", GoalDelete.as_view(), name="delete Goal"),
    path('goal/add/user_in_charge/', GoalSetUserInCharge.as_view(), name="goal-add-user-in-charge"),
    path('goal/remove/user_in_charge/', GoalRemoveUserInCharge.as_view(), name="goal-remove-user-in-charge"),
    path("goal/set/goal_manager/", GoalSetGoalManager.as_view(), name="goal-set-goal_manager"),
    path("goal/activities/list/", GoalActivitiesList.as_view(), name="goal-activities-list"),
    # Activities
    path("activity/create/", ActivityCreateView.as_view(), name="create-activity"),
    path("activity/list/", ActivitiesList.as_view(), name="list-of-all-Activities"),
    path("activity/<int:pk>/detail/", ActivitiesDetails.as_view(), name="activities-detail"),
    # path("activity/<int:pk>/detail/", ActivitiesDetails.as_view(), name="activity-detail"),
    path("activity/<int:pk>/update/", ActivitiesMulUpdate.as_view(), name="update-activity"),
    path("activity/<int:pk>/delete/", ActivitiesDelete.as_view(), name="delete-Activity"),
    path("activity/add_users/", ActivityAddUserInCharge.as_view(), name="add-activity-users"),
    path("activity/remove_users/", ActivityRemoveUserInCharge.as_view(), name="remove-activity-users"),
    # Report
    path("report/goal/create/", ReportGoalCreateView.as_view(), name="create-goal-Report"),
    path("report/activity/create/", ReportActivityCreateView.as_view(), name="create-activity-Report"),
    path("report/list/", ReportList.as_view(), name="list of all Report"),
    path("report/<int:pk>/detail/", ReportDetails.as_view(), name="report-detail"),
    path("report/<int:pk>/update/", ReportUpdate.as_view(), name="update-Report"),
    path("report/<int:pk>/delete/", ReportDelete.as_view(), name="delete-Report"),
    path("goal/reports/list/", GoalReportList.as_view(), name="goal-reports-list"),
    path("activity/reports/list/", ActivityReportList.as_view(), name="activity-reports-list"),
   
    #  tasks
    path("list/", Tasks.as_view(), name="tasks-list"),
    path("completed/", TasksCompleted.as_view(), name="tasks-completed"),
    # path("<int:pk>/rating/", TaskUpdate.as_view(), name="tasks-rating"),
    path("report/rating/", TaskUpdate.as_view(), name="task-rating1"),
    path("report/rate_review/", TaskRateReset.as_view(), name="task-review-update"),


]

from django.urls import path

# WeekStatistic views
from .views import (
    DayFinishActivities,
    DayUnFinishActivities,
    DayFinishGoals,
    DayUnFinishGoals,
    DayActivitiesStatistic,
    DayGoalsStatistic,

    WeekActivitiesStatistic,
    WeekGoalsStatistic,
    WeekActivitiesDayEvaluation,
    WeekGoalDayEvaluation,

    MonthActivitiesStatistic,
    MonthGoalsStatistic,
    MonthWeeksActivitiesEvaluation,
    MonthWeeksGoalsEvaluation,

    YearActivitiesStatistic,
    YearGoalsStatistic,
    YearMonthsActivitiesEvaluation,
    YearMonthsGoalsEvaluation,

    GoalProgress,
    GoalWeekStatistic,
    GoalMonthStatistic,
    GoalYearStatistic,
    AllGoalProgress,

    UserStatistic,
    UserWeekStatistic,
    UserMonthStatistic,
    UserYearStatistic,


)



urlpatterns = [
    # DayStatistic
    path("day/finish/activities/", DayFinishActivities.as_view(), name="day-list-of-all-finish-activities"),
    path("day/un-finish/activities/", DayUnFinishActivities.as_view(), name="day-list-of-all-un-finish-activities"),
    path("day/finish/goals/", DayFinishGoals.as_view(), name="day-list-of-all-finish-goals"),
    path("day/un-finish/goals/", DayUnFinishGoals.as_view(), name="day-list-of-all-un-finish-goals"),
    path("day/activities/statistic/", DayActivitiesStatistic.as_view(), name="day-activities-statistic"),
    path("day/goals/statistic/", DayGoalsStatistic.as_view(), name="day-goals-statistic"),
    # WeekStatistic
    path("week/activity/statistics/", WeekActivitiesStatistic.as_view(), name="week-activity-statistics"),
    path("week/goal/statistics/", WeekGoalsStatistic.as_view(), name="week-goal-statistics"),
    path("week/days/activity/performance/", WeekActivitiesDayEvaluation.as_view(), name="week-activity-day-performance"),
    path("week/days/goal/performance/", WeekGoalDayEvaluation.as_view(), name="week-goal-day-performance"),
    # MonthStatistic
    path("month/activity/statistics/", MonthActivitiesStatistic.as_view(), name="month-activity-statistics"),
    path("month/goal/statistics/", MonthGoalsStatistic.as_view(), name="month-goal-statistics"),
    path("month/weeks/activities/performance/", MonthWeeksActivitiesEvaluation.as_view(), name="month-weeks-activity-performance"),
    path("month/weeks/goals/performance/", MonthWeeksGoalsEvaluation.as_view(), name="month-weeks-activity-performance"),
    # year evaluation
    path("year/activity/statistics/", YearActivitiesStatistic.as_view(), name="year-activity-statistics"),
    path("year/goal/statistics/", YearGoalsStatistic.as_view(), name="year-goal-statistics"),
    path("year/months/activities/performance/", YearMonthsActivitiesEvaluation.as_view(), name="year-month-activities-performance"),
    path("year/months/goals/performance/", YearMonthsGoalsEvaluation.as_view(), name="year-months-goals-performance"),
    # goal Statistic
    path("goal/<int:pk>/progress/", GoalProgress.as_view(), name="goal-progress"),
    path("goals/week/progress/", GoalWeekStatistic.as_view(), name="goals-week-progress"),
    path("goals/month/progress/", GoalMonthStatistic.as_view(), name="goals-month-progress"),
    path("goals/year/progress/", GoalYearStatistic.as_view(), name="goals-year-progress"),
    path("goals/progress/", AllGoalProgress.as_view(), name="all-goals-progress"),
    # UserStatistic
    path("user/statistics/", UserStatistic.as_view(), name="user-statistic"),
    path("user/week/statistics/", UserWeekStatistic.as_view(), name="user-week-statistics"),
    path("user/month/statistics/", UserMonthStatistic.as_view(), name="user-month-statistics"),
    path("user/year/statistics/", UserYearStatistic.as_view(), name="user-year-statistics"),
    
]

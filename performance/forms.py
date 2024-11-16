from django import forms
from .models import WeekStatistic, MonthStatistic, YearStatistic, UserStatistic, GoalStatistic



"""
\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
    WeekStatistic, MonthStatistic, YearStatistic, UserStatistic, GoalStatistic
"""
# weekStatistic
class WeekStatisticForm(forms.ModelForm):
    class Meta:
        model = WeekStatistic
        fields = ("statistic", "week")

# monthStatistic
class MonthStatisticForm(forms.ModelForm):
    class Meta:
        model = MonthStatistic
        fields = ("statistic", "month")


# YearStatistic
class YearStatisticForm(forms.ModelForm):
    class Meta:
        model = YearStatistic
        fields = ("statistic", "year")

# UserStatistic
class UserStatisticForm(forms.ModelForm):
    class Meta:
        model = UserStatistic
        fields = ("statistic", "employee")

# GoalStatistic
class GoalStatisticForm(forms.ModelForm):
    class Meta:
        model = GoalStatistic
        fields = ("statistic", "goal")

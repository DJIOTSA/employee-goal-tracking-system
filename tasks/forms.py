from django import forms
from .models import Goal, Activities, Report


"""
\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
    GOAL, ACTIVITIES, REPORT
"""

# Goal
class GoalForm(forms.ModelForm):
    class Meta:
        model = Goal
        fields = ("created_by", "title", "description", "starting_date", "ending_date", "attached_file", "attached_file1", "attached_file2", "rate", "bonus", "dateOfRegistration", "is_deleted")

# Activities
class ActivitiesForm(forms.ModelForm):
    class Meta:
        model = Activities
        fields = ("goal", "employee", "title", "description", "starting_date", "ending_date", "attached_file", "attached_file1", "attached_file2", "rate", "bonus", "dateOfRegistration", "is_deleted")

# Report
class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ("report", "date_of_submission", "option", "goal", "activity", "rate" )

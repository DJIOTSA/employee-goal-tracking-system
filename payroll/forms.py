from django import forms
from .models import Payroll

"""
\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\
    PAYROLL
"""
# payroll
class PayrollForm(forms.ModelForm):
    class Meta:
        model = Payroll
        fields = ("username", "salary")
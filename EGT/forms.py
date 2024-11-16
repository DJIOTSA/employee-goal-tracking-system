from django import forms
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.forms import UserChangeForm

from .models import (
    MyUser, 
    EmployeeProfile, 
    AdministratorProfile, 
    Enterprise,
    Category,
    )
from django.contrib.auth import get_user_model

class MyUserCreationForm(forms.ModelForm):
    """
    A form that creates a user, with no privileges, from the given email and
    password.
    """
    password1 = forms.CharField(label=_('Password'),
                                widget=forms.PasswordInput)
    password2 = forms.CharField(label=_('Password confirmation'),
                                widget=forms.PasswordInput,
                                help_text=_('Enter the same password as '
                                'above, for verification.'))

    class Meta:
        model = get_user_model()
        fields = ('email',)

    def clean_email(self):
        email = self.cleaned_data.get('email')
        try:
            get_user_model().objects.get(email=email)
        except get_user_model().DoesNotExist:
            return email
        raise forms.ValidationError(_('A user with that email already exists.'))

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(
                _('The two password fields did not match.'))
        return password2

    def save(self, commit=True):
        user = super(MyUserCreationForm, self).save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user

class MyUserChangeForm(UserChangeForm):
    class Meta:
        model = get_user_model()
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(MyUserChangeForm, self).__init__(*args, **kwargs)
        if 'username' in self.fields:
            del self.fields['username']


# class MyUserChangeForm(UserChangeForm):
#     class Meta:
#         model = MyUser
#         fields = ('email', )

class AddEmployeeForm(forms.Form):
    enterprise_name = forms.CharField(max_length=255)
    email = forms.EmailField(max_length=255)
    first_name = forms.CharField(max_length=255)
    last_name = forms.CharField(max_length=255)
    
class EmployeeProfileForm(forms.ModelForm):
    class Meta:
        model = EmployeeProfile
        fields = "__all__"

class AdministratorProfileForm(forms.ModelForm):
    class Meta:
        model = AdministratorProfile
        fields = "__all__"


class EnterpriseForm(forms.ModelForm):
    class Meta:
        model = Enterprise
        fields = "__all__"

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = "__all__"


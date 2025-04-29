#importing relavent extensions
from django import forms
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import JOB_TITLE_CHOICES, Department

class BaseFormMixin:
    """Common styling for all forms"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({
                'class': 'form-control',
                'autocomplete': 'off'
            })

#this creates the form for the signup page
class RegisterForm(UserCreationForm):
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    email = forms.EmailField(required=True)
    job_title = forms.ChoiceField(choices=JOB_TITLE_CHOICES, required=True)
    department = forms.ModelChoiceField(
        queryset=Department.objects.all(),
        empty_label="Select your team",
        required=True
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'job_title', 'department', 'username', 'password1', 'password2']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("This email is already taken")
        return email
    

class LoginForm(forms.Form):
    identifier = forms.CharField(
        label='Username or Email',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your username or email'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password'
        })
    )






###############################################################################
#Reference:
#Tech With Tim (2019). Django Tutorial - User Registration & Sign Up Page. 
#[online] YouTube. 
#Available at: https://www.youtube.com/watch?v=Ev5xgwndmfc 
#[Accessed 20 Apr. 2025]
#
############################################################################
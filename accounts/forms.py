from django import forms
from django.contrib.auth.models import User
from .models import UserProfile


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'username']
        widgets = {
            'email': forms.EmailInput(attrs={'readonly': False}),
        }


class ProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['display_name', 'phone', 'avatar', 'role']
        widgets = {
            'role': forms.Select(attrs={'disabled': False}),
        }

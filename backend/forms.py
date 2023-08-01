from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from backend.models import CustomUser
from rest_framework.response import Response
from django.core.exceptions import ValidationError

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ('username', 'email')

class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = ('username', 'email')
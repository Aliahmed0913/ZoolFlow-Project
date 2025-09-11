from django import forms
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.contrib.auth.password_validation import validate_password
from users.models import User

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('role_management','email')
    
    def clean_password2(self):
        password = self.cleaned_data.get('password1')
        validate_password(password)
        return password
    
class CustomUserChangeForm(UserChangeForm):
    
    class Meta(UserChangeForm.Meta):
        model = User
        fields = ('role_management','email')
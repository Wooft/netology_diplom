from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from backend.forms import CustomUserCreationForm, CustomUserChangeForm
from backend.models import CustomUser


class CustomUserAdmin(BaseUserAdmin):
    model = CustomUser
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    list_display = ['email', 'username', 'type']
    add_fieldsets = (
        ("Основная информация", {
            'fields': ('username', "email" ,'first_name', 'last_name', 'surname', "type")
        }),
        (
            "Пароль",{
                'fields': ('password1', 'password2')
            }
        ),
        (
            "Работа", {
                "fields": ("company", "position")
            }
        )
    )

    fieldsets = (
        ("Основная информация", {
            'fields': ('username', "email" ,'first_name', 'last_name', 'surname', "type", "password")
        }),
        (
            "Работа", {
                "fields": ("company", "position")
            }
        )
    )

admin.site.register(CustomUser, CustomUserAdmin)
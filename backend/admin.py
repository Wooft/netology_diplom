from django.contrib import admin

from backend.models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['email', 'lastname', 'name',]
    list_filter = ['company']

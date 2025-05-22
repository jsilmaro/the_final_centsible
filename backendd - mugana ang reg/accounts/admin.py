
from django.contrib import admin
from .models import CustomUser
from api.models import Transaction, Budget

# User Admin
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ["id", "email", "name", "is_active", "is_staff"]
    search_fields = ["email", "name"]

# Register models
admin.site.register(CustomUser, CustomUserAdmin)
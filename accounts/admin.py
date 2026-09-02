from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ("username", "email", "phone", "is_driver", "is_passenger", "is_staff")
    list_filter = ("is_driver", "is_passenger", "is_staff", "is_active")
    fieldsets = UserAdmin.fieldsets + (
        ("Infos supplémentaires", {
            "fields": ("phone", "is_driver", "is_passenger", "rating_avg",
                       "is_verified_email", "is_verified_phone")
        }),
    )
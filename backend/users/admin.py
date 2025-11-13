# backend/users/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from .models import UserProfile


# === INLINE : PROFIL DANS USER ===
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profil'


# === CUSTOM USER ADMIN ===
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'photo_thumb', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name')

    inlines = (UserProfileInline,)

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Informations personnelles', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Dates', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2'),
        }),
    )

    def photo_thumb(self, obj):
        profile = UserProfile.objects.filter(user=obj).first()
        if profile and profile.photo:
            return format_html(
                '<img src="{}" width="50" height="50" style="border-radius:50%; object-fit:cover;">',
                profile.photo.url
            )
        return "Pas de photo"
    photo_thumb.short_description = 'Photo'


# === REMPLACE L'ADMIN PAR DÉFAUT ===
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
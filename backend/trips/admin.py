from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import Trip

# === AJOUTE LE CHAMP EMAIL DANS L'ADMIN (SANS DOUBLON) ===
admin.site.unregister(User)

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff')

    # On remplace les fieldsets par une version propre
    fieldsets = (
        (None, {
            'fields': ('username', 'password')
        }),
        ('Informations personnelles', {
            'fields': ('first_name', 'last_name', 'email')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Dates importantes', {
            'fields': ('last_login', 'date_joined')
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2'),
        }),
    )

# === TRIPS (inchangé) ===
@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = ('departure', 'arrival', 'date', 'driver', 'seats_available', 'price')
    list_filter = ('date', 'departure')
    search_fields = ('departure', 'arrival')
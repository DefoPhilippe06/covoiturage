from django.contrib import admin
from .models import Trip

@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = ("origin_city", "destination_city", "departure_datetime", "driver", "seats_available", "status")
    list_filter = ("status", "departure_datetime")
    search_fields = ("origin_city", "destination_city")
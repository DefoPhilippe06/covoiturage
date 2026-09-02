from django.contrib import admin
from .models import Vehicle

@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ("brand", "model", "plate_number", "owner", "seats")
    list_filter = ("brand",)
    search_fields = ("plate_number", "brand", "model")
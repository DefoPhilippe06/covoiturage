from rest_framework import serializers
from .models import Trip

class TripSerializer(serializers.ModelSerializer):
    driver_username = serializers.CharField(source="driver.username", read_only=True)
    vehicle_info = serializers.StringRelatedField(source="vehicle", read_only=True)

    class Meta:
        model = Trip
        fields = "__all__"
        read_only_fields = ("driver", "seats_available", "status")
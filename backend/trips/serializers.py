# backend/trips/serializers.py
from rest_framework import serializers
from .models import Trip, Booking, Payment
from users.serializers import UserSerializer  # Import unique


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['id', 'amount', 'commission', 'driver_earnings', 'paid']
        read_only_fields = ['commission', 'driver_earnings', 'paid']


class BookingSerializer(serializers.ModelSerializer):
    trip_departure = serializers.CharField(source='trip.departure', read_only=True)
    trip_arrival = serializers.CharField(source='trip.arrival', read_only=True)
    trip_driver = serializers.CharField(source='trip.driver.username', read_only=True)
    trip_date = serializers.DateTimeField(source='trip.date', read_only=True)
    passenger = serializers.CharField(source='passenger.username', read_only=True)
    payment = PaymentSerializer(read_only=True)

    class Meta:
        model = Booking
        fields = [
            'id', 'trip_departure', 'trip_arrival', 'trip_driver', 'trip_date',
            'passenger', 'booked_at', 'payment'
        ]


class TripSerializer(serializers.ModelSerializer):
    driver = serializers.CharField(source='driver.username', read_only=True)
    driver_email = serializers.CharField(source='driver.email', read_only=True)
    bookings = BookingSerializer(many=True, read_only=True)

    class Meta:
        model = Trip
        fields = [
            'id', 'driver', 'driver_email', 'departure', 'arrival', 'date',
            'seats_available', 'price', 'bookings'
        ]
        # meeting_point supprimé
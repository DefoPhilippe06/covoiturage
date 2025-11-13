# backend/trips/models.py
from django.db import models
from django.contrib.auth.models import User
from users.models import UserProfile  # Import du profil


class Trip(models.Model):
    driver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='trips')
    departure = models.CharField(max_length=100)
    arrival = models.CharField(max_length=100)
    date = models.DateTimeField()
    seats_available = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.departure} to {self.arrival} - {self.driver.username}"


class Booking(models.Model):
    passenger = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='bookings')
    booked_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.passenger.username} - {self.trip}"


class Payment(models.Model):
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='payment')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    commission = models.DecimalField(max_digits=10, decimal_places=2)
    driver_earnings = models.DecimalField(max_digits=10, decimal_places=2)
    paid = models.BooleanField(default=False)

    def __str__(self):
        return f"Paiement {self.booking.id} - {self.amount} FCFA"
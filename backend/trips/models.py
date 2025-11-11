from django.contrib.auth.models import User
from django.db import models

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    photo = models.ImageField(upload_to='avatars/', null=True, blank=True, default='avatars/default.png')

    def __str__(self):
        return f"{self.user.username}'s profile"

class Trip(models.Model):
    driver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='trips_as_driver')
    departure = models.CharField(max_length=200)
    arrival = models.CharField(max_length=200)
    date = models.DateTimeField()
    seats_available = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=6, decimal_places=2)
    meeting_point = models.CharField(max_length=300, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.departure} → {self.arrival} ({self.date})"

class Booking(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='bookings')
    passenger = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    booked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('trip', 'passenger')  # 1 réservation par trajet

    def __str__(self):
        return f"{self.passenger} → {self.trip}"

class Payment(models.Model):
    booking = models.OneToOneField('Booking', on_delete=models.CASCADE, related_name='payment')
    amount = models.DecimalField(max_digits=10, decimal_places=2)  # Total payé
    commission = models.DecimalField(max_digits=10, decimal_places=2)  # 5% pour toi
    driver_earnings = models.DecimalField(max_digits=10, decimal_places=2)  # 95% pour conducteur
    stripe_charge_id = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    paid = models.BooleanField(default=False)

    def __str__(self):
        return f"Paiement {self.booking.id} - {self.amount}€"
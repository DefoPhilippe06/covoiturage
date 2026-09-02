from django.db import models
from django.conf import settings

class Notification(models.Model):
    class Type(models.TextChoices):
        BOOKING = "BOOKING", "Réservation"
        TRIP = "TRIP", "Trajet"
        PAYMENT = "PAYMENT", "Paiement"
        REVIEW = "REVIEW", "Avis"
        SYSTEM = "SYSTEM", "Système"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications"
    )
    type = models.CharField(max_length=20, choices=Type.choices, default=Type.SYSTEM)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    link = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} — {self.title}"
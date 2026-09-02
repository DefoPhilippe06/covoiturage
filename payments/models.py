from django.db import models
from django.conf import settings
from decimal import Decimal

class Payment(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "En attente"
        SUCCESS = "SUCCESS", "Réussi"
        FAILED = "FAILED", "Échoué"
        REFUNDED = "REFUNDED", "Remboursé"

    class Provider(models.TextChoices):
        ORANGE_MONEY = "ORANGE_MONEY", "Orange Money"
        MTN_MOMO = "MTN_MOMO", "MTN MoMo"
        CARD = "CARD", "Carte bancaire"
        CASH = "CASH", "Espèces"

    booking = models.OneToOneField(
        "bookings.Booking",
        on_delete=models.CASCADE,
        related_name="payment"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="payments"
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default="XAF")
    provider = models.CharField(max_length=20, choices=Provider.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    transaction_id = models.CharField(max_length=100, blank=True)
    provider_response = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} — {self.amount} {self.currency} ({self.status})"
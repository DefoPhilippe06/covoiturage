from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from decimal import Decimal

class Trip(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Brouillon"
        PUBLISHED = "PUBLISHED", "Publié"
        STARTED = "STARTED", "Démarré"
        COMPLETED = "COMPLETED", "Terminé"
        CANCELLED = "CANCELLED", "Annulé"

    driver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="trips_as_driver"
    )
    vehicle = models.ForeignKey(
        "vehicles.Vehicle",
        on_delete=models.PROTECT,
        related_name="trips"
    )
    origin_city = models.CharField(max_length=100)
    origin_lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    origin_lng = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    destination_city = models.CharField(max_length=100)
    destination_lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    destination_lng = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    departure_datetime = models.DateTimeField()
    seats_total = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])
    seats_available = models.PositiveSmallIntegerField()
    price_per_seat = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))]
    )
    currency = models.CharField(max_length=3, default="XAF")
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["departure_datetime"]

    def __str__(self):
        return f"{self.origin_city} → {self.destination_city} ({self.departure_datetime})"

    def save(self, *args, **kwargs):
        if not self.pk:  # nouveau trajet
            self.seats_available = self.seats_total
        super().save(*args, **kwargs)
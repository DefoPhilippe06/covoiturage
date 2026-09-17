from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings


@shared_task(name="trips.tasks.send_booking_notification")
def send_booking_notification(
    driver_email,
    passenger_name,
    trip_id,
    seats_left,
    amount,
    commission,
):
    """Email au conducteur après une réservation."""
    if not driver_email:
        return "Pas d'email conducteur"

    subject = f"Nouvelle réservation — trajet #{trip_id}"
    message = (
        f"Bonjour,\n\n"
        f"{passenger_name} a réservé sur votre trajet #{trip_id}.\n"
        f"Montant : {amount} XAF\n"
        f"Commission : {commission} XAF\n"
        f"Places restantes : {seats_left}\n\n"
        f"— Covoiturage"
    )

    send_mail(
        subject=subject,
        message=message,
        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@covoiturage.local"),
        recipient_list=[driver_email],
        fail_silently=True,
    )
    return f"Email envoyé à {driver_email}"


@shared_task(name="trips.tasks.send_booking_cancelled_notification")
def send_booking_cancelled_notification(
    driver_email,
    passenger_email,
    passenger_name,
    trip_id,
    origin_city,
    destination_city,
    seats,
):
    """Emails conducteur + passager après annulation."""
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@covoiturage.local")
    results = []

    if driver_email:
        send_mail(
            subject=f"Réservation annulée — trajet #{trip_id}",
            message=(
                f"Bonjour,\n\n"
                f"{passenger_name} a annulé sa réservation "
                f"({seats} place(s)) sur {origin_city} → {destination_city}.\n\n"
                f"— Covoiturage"
            ),
            from_email=from_email,
            recipient_list=[driver_email],
            fail_silently=True,
        )
        results.append(f"driver:{driver_email}")

    if passenger_email:
        send_mail(
            subject=f"Votre réservation a été annulée — trajet #{trip_id}",
            message=(
                f"Bonjour,\n\n"
                f"Votre réservation pour {origin_city} → {destination_city} "
                f"a bien été annulée.\n\n"
                f"— Covoiturage"
            ),
            from_email=from_email,
            recipient_list=[passenger_email],
            fail_silently=True,
        )
        results.append(f"passenger:{passenger_email}")

    return ", ".join(results) if results else "Aucun email"

from celery import shared_task
from django.utils import timezone
from .models import Trip


@shared_task
def expire_past_trips():
    n = Trip.objects.filter(
        status=Trip.Status.PUBLISHED,
        departure_datetime__lt=timezone.now(),
    ).update(status=Trip.Status.COMPLETED)  # ou CANCELLED selon ta règle
    return f"{n} trajets expirés"
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from .models import Trip  # ← IMPORTANT

@shared_task
def send_payment_email(user_email, trip_title, amount):
    subject = f"Paiement confirmé - {trip_title}"
    message = f"""
    Bonjour,

    Votre paiement de {amount} € pour le trajet "{trip_title}" a été confirmé !

    Merci d'utiliser Covoiturage App.
    """
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user_email],
        fail_silently=False,
    )

@shared_task
def send_booking_notification(driver_email, passenger_name, trip_id, seats_left, amount, commission):
    trip = Trip.objects.get(id=trip_id)  # ← RÉCUPÈRE LE TRIP

    html_message = render_to_string('emails/booking_notification.html', {
        'driver_name': trip.driver.username,
        'passenger_name': passenger_name,
        'trip': trip,
        'seats_left': seats_left,
        'amount': amount,
        'commission': commission
    })

    send_mail(
        subject=f"Nouvelle réservation : {trip.departure} to {trip.arrival}",
        message=f"{passenger_name} a réservé une place.",
        html_message=html_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[driver_email],
        fail_silently=False,
    )
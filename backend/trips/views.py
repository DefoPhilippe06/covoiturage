from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from .models import Trip, Booking, Payment, UserProfile
from .serializers import TripSerializer, BookingSerializer, PaymentSerializer
from django.db.models import Q
from datetime import datetime
from django.conf import settings
from django.db import transaction
from django.template.loader import render_to_string
from django.urls import reverse
from django.views.generic import TemplateView
from decimal import Decimal
import stripe
import json
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from .tasks import send_payment_email, send_booking_notification

# IMPORT LOCAL
from .stripe_config import stripe

# === CELERY TASKS ===
from .tasks import send_payment_email, send_booking_notification  # ← AJOUTÉ send_booking_notification


class TripViewSet(viewsets.ModelViewSet):
    queryset = Trip.objects.all().order_by('-date')
    serializer_class = TripSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        queryset = Trip.objects.all().order_by('-date').prefetch_related('bookings__payment')
        departure = self.request.query_params.get('departure')
        arrival = self.request.query_params.get('arrival')
        date = self.request.query_params.get('date')

        if departure:
            queryset = queryset.filter(departure__icontains=departure)
        if arrival:
            queryset = queryset.filter(arrival__icontains=arrival)
        if date:
            try:
                filter_date = datetime.strptime(date, '%Y-%m-%d')
                queryset = queryset.filter(date__date=filter_date.date())
            except:
                pass

        return queryset

    def perform_create(self, serializer):
        serializer.save(driver=self.request.user)

    # === RÉSERVER SANS PAYER ===
    @action(detail=True, methods=['post'])
    def book(self, request, pk=None):
        trip = self.get_object()

        with transaction.atomic():
            trip.refresh_from_db()

            if Booking.objects.filter(trip=trip, passenger=request.user).exists():
                return Response({'status': 'Vous avez déjà réservé ce trajet'}, status=400)

            if trip.seats_available <= 0:
                return Response({'status': 'Plus de places disponibles'}, status=400)

            trip.seats_available -= 1
            trip.save()

            booking = Booking.objects.create(trip=trip, passenger=request.user)

            total_amount = trip.price
            commission = total_amount * Decimal('0.05')
            driver_earnings = total_amount - commission

            payment = Payment.objects.create(
                booking=booking,
                amount=total_amount,
                commission=commission,
                driver_earnings=driver_earnings,
                paid=False
            )

            if trip.driver.email:
             send_booking_notification.delay(
                driver_email=trip.driver.email,
                passenger_name=request.user.username,
                trip_id=trip.id,  # ← SEULEMENT L'ID
                seats_left=trip.seats_available,
                amount=float(total_amount),
                commission=float(commission)
            )

            return Response({
                'status': 'Réservé ! Paiement en attente.',
                'payment_id': payment.id,
                'booking_id': booking.id
            })

    # === PAYER (APRÈS RÉSERVATION) ===
    @action(detail=True, methods=['post'])
    def pay(self, request, pk=None):
        trip = self.get_object()

        try:
            booking = Booking.objects.get(trip=trip, passenger=request.user)
            payment = Payment.objects.get(booking=booking, paid=False)
        except (Booking.DoesNotExist, Payment.DoesNotExist):
            return Response({'error': 'Aucune réservation trouvée'}, status=400)

        try:
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'eur',
                        'product_data': {
                            'name': f'Trajet {trip.departure} → {trip.arrival}',
                        },
                        'unit_amount': int(payment.amount * 100),
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url=request.build_absolute_uri(reverse('payment_success')) + '?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=request.build_absolute_uri(reverse('payment_cancel')),
                metadata={'payment_id': str(payment.id)},
            )
            return Response({'id': session.id})
        except Exception as e:
            return Response({'error': str(e)}, status=400)


class BookingViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Booking.objects.filter(passenger=self.request.user).select_related('trip', 'payment')


# === VUES DE PAIEMENT ===
class PaymentSuccessView(TemplateView):
    template_name = 'payment_success.html'

class PaymentCancelView(TemplateView):
    template_name = 'payment_cancel.html'


# === WEBHOOK STRIPE : MARQUE LE PAIEMENT + ENVOI MAIL ASYNCHRONE ===
@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET  # ← UTILISE .env

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError:
        print("Payload invalide")
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        print("Signature invalide:", e)
        return HttpResponse(status=400)

    if event.type == 'checkout.session.completed':
        session = event.data.object
        payment_id = session.metadata.get('payment_id')
        if payment_id:
            try:
                payment = Payment.objects.get(id=payment_id)
                payment.paid = True
                payment.save()

                # === ENVOI MAIL DE CONFIRMATION EN ARRIÈRE-PLAN ===
                send_payment_email.delay(
                    user_email=payment.booking.passenger.email,
                    trip_title=f"{payment.booking.trip.departure} to {payment.booking.trip.arrival}",
                    amount=payment.amount
                )

                print(f"PAIEMENT {payment_id} MARQUÉ COMME PAYÉ + MAIL ENVOYÉ !")
            except Payment.DoesNotExist:
                print("Payment non trouvé:", payment_id)

    return HttpResponse(status=200)


# === UPLOAD PHOTO DE PROFIL ===
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_photo(request):
    user = request.user
    photo = request.FILES.get('photo')
    if photo:
        profile, created = UserProfile.objects.get_or_create(user=user)
        profile.photo = photo
        profile.save()
        return Response({'photo': profile.photo.url})
    return Response({'error': 'Aucune photo'}, status=400)
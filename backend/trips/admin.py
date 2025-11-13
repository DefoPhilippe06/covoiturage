# backend/trips/admin.py
from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import Trip, Booking, Payment


# === TRIP ADMIN ===
@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = ['departure', 'arrival', 'driver_link', 'date', 'price', 'seats_available', 'bookings_count']
    list_filter = ['date', 'departure', 'arrival']
    search_fields = ['departure', 'arrival', 'driver__username']

    def driver_link(self, obj):
        url = reverse("admin:auth_user_change", args=[obj.driver.id])
        return format_html('<a href="{}">{}</a>', url, obj.driver.username)
    driver_link.short_description = 'Conducteur'

    def bookings_count(self, obj):
        return obj.bookings.count()
    bookings_count.short_description = 'Réservations'


# === BOOKING ADMIN ===
@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['passenger_link', 'trip_link', 'booked_at', 'payment_status']
    list_filter = ['booked_at']
    search_fields = ['passenger__username', 'trip__departure']

    def passenger_link(self, obj):
        url = reverse("admin:auth_user_change", args=[obj.passenger.id])
        return format_html('<a href="{}">{}</a>', url, obj.passenger.username)
    passenger_link.short_description = 'Passager'

    def trip_link(self, obj):
        url = reverse("admin:trips_trip_change", args=[obj.trip.id])
        return format_html('<a href="{}">{}</a>', url, f"{obj.trip.departure} to {obj.trip.arrival}")
    trip_link.short_description = 'Trajet'

    def payment_status(self, obj):
        if obj.payment:
            color = 'green' if obj.payment.paid else 'orange'
            status = 'Payé' if obj.payment.paid else 'En attente'
            return format_html('<span style="color:{}"><b>{}</b></span>', color, status)
        return "—"
    payment_status.short_description = 'Paiement'


# === PAYMENT ADMIN ===
@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['booking_link', 'amount', 'commission', 'driver_earnings', 'paid_colored']
    list_filter = ['paid']
    search_fields = ['booking__passenger__username']
    readonly_fields = ['amount', 'commission', 'driver_earnings']

    def booking_link(self, obj):
        url = reverse("admin:trips_booking_change", args=[obj.booking.id])
        return format_html('<a href="{}">Réservation #{}</a>', url, obj.booking.id)
    booking_link.short_description = 'Réservation'

    def paid_colored(self, obj):
        color = 'green' if obj.paid else 'red'
        status = 'PAYÉ' if obj.paid else 'NON PAYÉ'
        return format_html('<b style="color:{}">{}</b>', color, status)
    paid_colored.short_description = 'Statut'

    actions = ['mark_as_paid']

    def mark_as_paid(self, request, queryset):
        updated = queryset.update(paid=True)
        self.message_user(request, f"{updated} paiement(s) marqué(s) comme payé(s).")
    mark_as_paid.short_description = "Marquer comme payé"
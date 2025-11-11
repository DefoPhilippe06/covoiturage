from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TripViewSet, BookingViewSet, upload_photo, stripe_webhook

router = DefaultRouter()
router.register(r'trips', TripViewSet)
router.register(r'bookings', BookingViewSet, basename='booking')  # AJOUTÉ basename

urlpatterns = [
    path('', include(router.urls)),
    path('upload-photo/', upload_photo, name='upload_photo'),
    path('webhook/stripe/', stripe_webhook, name='stripe_webhook'),
]
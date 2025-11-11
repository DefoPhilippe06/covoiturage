from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.conf import settings
from django.conf.urls.static import static
from trips.views import PaymentSuccessView, PaymentCancelView
from trips.views import stripe_webhook

# === SWAGGER AVEC TOKEN AUTH (FORCÉ) ===
schema_view = get_schema_view(
    openapi.Info(
        title="Covoiturage API",
        default_version='v1',
        description="API sécurisée pour le covoiturage",
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
    authentication_classes=()  # ← VIDE = PAS DE BASIC
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('trips.urls')),
    path('api/users/', include('users.urls')),
    path('api-auth/', include('rest_framework.urls')),
    path('api-auth/token/', obtain_auth_token, name='api_token_auth'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('', TemplateView.as_view(template_name='index.html'), name='home'),
    path('payment/success/', PaymentSuccessView.as_view(), name='payment_success'),
    path('payment/cancel/', PaymentCancelView.as_view(), name='payment_cancel'),
    path('webhook/stripe/', stripe_webhook, name='stripe_webhook'),
]

# === SERVE MEDIA EN DEV ===
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
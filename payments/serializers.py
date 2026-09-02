from rest_framework import serializers
from .models import Payment

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = "__all__"
        read_only_fields = (
            "user",
            "amount",
            "currency",
            "status",
            "transaction_id",
            "provider_response",
        )
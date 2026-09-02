from rest_framework import serializers
from .models import Review

class ReviewSerializer(serializers.ModelSerializer):
    reviewer_username = serializers.CharField(source="reviewer.username", read_only=True)
    reviewed_username = serializers.CharField(source="reviewed_user.username", read_only=True)

    class Meta:
        model = Review
        fields = "__all__"
        read_only_fields = ("reviewer",)
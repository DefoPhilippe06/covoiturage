from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Avg
from .models import Review

def update_user_rating(user):
    avg = Review.objects.filter(reviewed_user=user).aggregate(Avg("rating"))["rating__avg"]
    user.rating_avg = round(avg or 0, 2)
    user.save(update_fields=["rating_avg"])

@receiver(post_save, sender=Review)
def review_saved(sender, instance, **kwargs):
    update_user_rating(instance.reviewed_user)

@receiver(post_delete, sender=Review)
def review_deleted(sender, instance, **kwargs):
    update_user_rating(instance.reviewed_user)
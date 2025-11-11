from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin

admin.site.unregister(User)

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'photo_thumb', 'is_staff')
    
    def photo_thumb(self, obj):
        if obj.photo:
            return f'<img src="{obj.photo.url}" width="50" height="50" style="border-radius:50%; object-fit:cover;">'
        return "Pas de photo"
    photo_thumb.allow_tags = True
    photo_thumb.short_description = 'Photo'
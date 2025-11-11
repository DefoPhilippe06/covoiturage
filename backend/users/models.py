from django.contrib.auth.models import User
from django.db import models

# Étend le modèle User
User.add_to_class('photo', models.ImageField(upload_to='profiles/', null=True, blank=True))
from django.db import models
from core.models import Player
import uuid

class LoginToken(models.Model):
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='login_tokens')
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    def __str__(self):
        return f"Login token for {self.player} ({'Used' if self.is_used else 'Active'})"

class RegistrationToken(models.Model):
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    telegram_id = models.TextField()
    telegram_username = models.TextField(null=True, blank=True)
    telegram_first_name = models.TextField(null=True, blank=True)
    telegram_last_name = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    def __str__(self):
        return f"Registration token for TG user {self.telegram_username or self.telegram_id} ({'Used' if self.is_used else 'Active'})"

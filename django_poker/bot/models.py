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

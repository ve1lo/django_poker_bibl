from django.contrib import admin
from .models import LoginToken, RegistrationToken

@admin.register(LoginToken)
class LoginTokenAdmin(admin.ModelAdmin):
    list_display = ('player', 'created_at', 'is_used')
    list_filter = ('is_used', 'created_at')
    search_fields = ('player__username', 'player__first_name', 'player__telegram_id')
    readonly_fields = ('token', 'created_at')

@admin.register(RegistrationToken)
class RegistrationTokenAdmin(admin.ModelAdmin):
    list_display = ('telegram_username', 'telegram_id', 'created_at', 'is_used')
    list_filter = ('is_used', 'created_at')
    search_fields = ('telegram_username', 'telegram_id', 'telegram_first_name', 'telegram_last_name')
    readonly_fields = ('token', 'created_at')

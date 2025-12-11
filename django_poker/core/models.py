from django.db import models
from django.utils import timezone

class Player(models.Model):
    telegram_id = models.TextField(unique=True)
    username = models.TextField(null=True, blank=True)
    first_name = models.TextField(null=True, blank=True)
    last_name = models.TextField(null=True, blank=True)
    phone = models.TextField(null=True, blank=True)
    is_admin = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.username or self.first_name or str(self.id)

class TournamentTemplate(models.Model):
    name = models.TextField()
    description = models.TextField(null=True, blank=True)
    type = models.TextField()  # "PAID" | "FREE"
    buy_in = models.IntegerField(null=True, blank=True)
    stack = models.IntegerField(default=10000)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class TemplateLevel(models.Model):
    template = models.ForeignKey(TournamentTemplate, related_name='levels', on_delete=models.CASCADE)
    level_number = models.IntegerField()
    small_blind = models.IntegerField()
    big_blind = models.IntegerField()
    ante = models.IntegerField(default=0)
    duration = models.IntegerField()  # in minutes
    is_break = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.template.name} - Level {self.level_number}"

class Tournament(models.Model):
    STATUS_CHOICES = [
        ('SCHEDULED', 'Scheduled'),
        ('RUNNING', 'Running'),
        ('PAUSED', 'Paused'),
        ('FINISHED', 'Finished'),
        ('BREAK', 'Break'),
    ]

    name = models.TextField()
    date = models.DateTimeField()
    type = models.TextField()  # "PAID" | "FREE"
    status = models.TextField(choices=STATUS_CHOICES, default='SCHEDULED')
    
    break_start_time = models.DateTimeField(null=True, blank=True)
    break_duration_minutes = models.IntegerField(null=True, blank=True)
    
    season = models.TextField(null=True, blank=True)
    buy_in = models.IntegerField(null=True, blank=True)
    stack = models.IntegerField(default=10000)
    config = models.TextField(default='{}')  # JSON string
    
    # Timer State
    current_level_index = models.IntegerField(default=0)
    level_started_at = models.DateTimeField(null=True, blank=True)
    timer_paused_at = models.DateTimeField(null=True, blank=True)
    timer_seconds = models.IntegerField(null=True, blank=True)
    
    registration_closed = models.BooleanField(default=False)
    display_settings = models.TextField(null=True, blank=True)  # JSON string
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.date.date()})"

class TournamentLevel(models.Model):
    tournament = models.ForeignKey(Tournament, related_name='levels', on_delete=models.CASCADE)
    level_number = models.IntegerField()
    small_blind = models.IntegerField()
    big_blind = models.IntegerField()
    ante = models.IntegerField(default=0)
    duration = models.IntegerField()  # in minutes
    is_break = models.BooleanField(default=False)

    class Meta:
        ordering = ['level_number']

class Table(models.Model):
    tournament = models.ForeignKey(Tournament, related_name='tables', on_delete=models.CASCADE)
    table_number = models.IntegerField()
    max_seats = models.IntegerField(default=9)

    class Meta:
        ordering = ['table_number']

    def __str__(self):
        return f"Table {self.table_number}"

class Registration(models.Model):
    STATUS_CHOICES = [
        ('REGISTERED', 'Registered'),
        ('ELIMINATED', 'Eliminated'),
    ]

    player = models.ForeignKey(Player, related_name='registrations', on_delete=models.CASCADE)
    tournament = models.ForeignKey(Tournament, related_name='registrations', on_delete=models.CASCADE)
    table = models.ForeignKey(Table, related_name='registrations', on_delete=models.SET_NULL, null=True, blank=True)
    
    status = models.TextField(choices=STATUS_CHOICES, default='REGISTERED')
    rebuys = models.IntegerField(default=0)
    addons = models.IntegerField(default=0)
    
    place = models.IntegerField(null=True, blank=True)
    bounty_count = models.IntegerField(default=0)
    points = models.IntegerField(null=True, blank=True)
    seat_number = models.IntegerField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['player', 'tournament']

class GameEvent(models.Model):
    tournament = models.ForeignKey(Tournament, related_name='events', on_delete=models.CASCADE)
    type = models.TextField()
    description = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

class Payout(models.Model):
    tournament = models.ForeignKey(Tournament, related_name='payouts', on_delete=models.CASCADE)
    player = models.ForeignKey(Player, null=True, blank=True, on_delete=models.SET_NULL)
    amount = models.IntegerField()
    place = models.IntegerField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)

class SystemSettings(models.Model):
    theme = models.TextField(default='default')
    updated_at = models.DateTimeField(auto_now=True)

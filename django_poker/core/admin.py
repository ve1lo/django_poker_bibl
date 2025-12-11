from django.contrib import admin
from .models import Player, Tournament, TournamentTemplate, Registration, Table, Payout, SystemSettings

admin.site.register(Player)
admin.site.register(Tournament)
admin.site.register(TournamentTemplate)
admin.site.register(Registration)
admin.site.register(Table)
admin.site.register(Payout)
admin.site.register(SystemSettings)

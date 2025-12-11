from .models import Player

def player_context(request):
    """
    Add current player to template context for all views
    """
    player = None
    if 'player_id' in request.session:
        try:
            player = Player.objects.get(id=request.session['player_id'])
        except Player.DoesNotExist:
            del request.session['player_id']

    is_admin = False
    if player:
        is_admin = player.is_admin

    return {
        'player': player,
        'is_admin': is_admin,
    }

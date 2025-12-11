from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.db import models
from .models import Tournament, Player
import json
import random
import math

@csrf_exempt
def start_timer(request, tournament_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
        
    tournament = get_object_or_404(Tournament, id=tournament_id)
    
    if tournament.status == 'RUNNING':
        return JsonResponse({'status': 'already_running'})
    
    # If starting for the first time or from a fresh state
    if tournament.timer_seconds is None:
        current_level = tournament.levels.order_by('level_number')[tournament.current_level_index]
        tournament.timer_seconds = current_level.duration * 60
        
    tournament.level_started_at = timezone.now()
    tournament.status = 'RUNNING'
    tournament.save()
    
    return JsonResponse({'status': 'started'})

@csrf_exempt
def pause_timer(request, tournament_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
        
    tournament = get_object_or_404(Tournament, id=tournament_id)
    
    if tournament.status != 'RUNNING':
        return JsonResponse({'status': 'not_running'})
        
    now = timezone.now()
    elapsed = (now - tournament.level_started_at).total_seconds()
    tournament.timer_seconds = max(0, int(tournament.timer_seconds - elapsed))
    tournament.level_started_at = None
    tournament.status = 'PAUSED'
    tournament.save()
    
    return JsonResponse({'status': 'paused', 'remaining': tournament.timer_seconds})

@csrf_exempt
def next_level(request, tournament_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
        
    tournament = get_object_or_404(Tournament, id=tournament_id)
    levels = tournament.levels.order_by('level_number')
    
    if tournament.current_level_index < levels.count() - 1:
        tournament.current_level_index += 1
        next_lvl = levels[tournament.current_level_index]
        
        # Reset timer for new level
        tournament.timer_seconds = next_lvl.duration * 60
        
        if tournament.status == 'RUNNING':
            tournament.level_started_at = timezone.now()
            
        tournament.save()
        return JsonResponse({'status': 'level_advanced', 'level': next_lvl.level_number})
    
    return JsonResponse({'status': 'max_level_reached'})

@csrf_exempt
def prev_level(request, tournament_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    tournament = get_object_or_404(Tournament, id=tournament_id)
    levels = tournament.levels.order_by('level_number')

    if tournament.current_level_index > 0:
        tournament.current_level_index -= 1
        prev_lvl = levels[tournament.current_level_index]

        # Reset timer for previous level
        tournament.timer_seconds = prev_lvl.duration * 60

        if tournament.status == 'RUNNING':
            tournament.level_started_at = timezone.now()

        tournament.save()
        return JsonResponse({'status': 'level_decreased', 'level': prev_lvl.level_number})

    return JsonResponse({'status': 'min_level_reached'})

@csrf_exempt
def start_break(request, tournament_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    tournament = get_object_or_404(Tournament, id=tournament_id)
    data = json.loads(request.body)
    duration = data.get('duration', 15)  # Default 15 minutes

    # Save break info
    tournament.break_start_time = timezone.now()
    tournament.break_duration_minutes = duration
    tournament.timer_seconds = duration * 60
    tournament.level_started_at = timezone.now()
    tournament.status = 'BREAK'
    tournament.save()

    return JsonResponse({
        'status': 'break_started',
        'duration': duration,
        'break_start_time': tournament.break_start_time.isoformat()
    })

@csrf_exempt
def set_timer(request, tournament_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
        
    tournament = get_object_or_404(Tournament, id=tournament_id)
    data = json.loads(request.body)
    
    minutes = int(data.get('minutes', 0))
    seconds = int(data.get('seconds', 0))
    
    tournament.timer_seconds = (minutes * 60) + seconds
    
    # If unpausing or running, update start time
    if tournament.status == 'RUNNING':
        tournament.level_started_at = timezone.now()
        
    tournament.save()

    return JsonResponse({'status': 'timer_set', 'timer_seconds': tournament.timer_seconds})

@csrf_exempt
def finish_tournament(request, tournament_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    tournament = get_object_or_404(Tournament, id=tournament_id)

    # Set tournament status to FINISHED
    tournament.status = 'FINISHED'
    tournament.save()

    return JsonResponse({
        'status': 'tournament_finished',
        'tournament_id': tournament_id
    })

def get_status(request, tournament_id):
    tournament = get_object_or_404(Tournament, id=tournament_id)
    levels = tournament.levels.order_by('level_number')
    
    remaining = 0
    if tournament.status == 'RUNNING' and tournament.level_started_at:
        elapsed = (timezone.now() - tournament.level_started_at).total_seconds()
        remaining = max(0, int(tournament.timer_seconds - elapsed))
    elif tournament.timer_seconds is not None:
        remaining = tournament.timer_seconds
    else:
        # Fallback if timer_seconds is None (e.g. not started yet)
        if levels.exists():
            remaining = levels[tournament.current_level_index].duration * 60
            
    current_level = levels[tournament.current_level_index] if levels.exists() else None

    # Get next level
    next_level = None
    if levels.exists() and tournament.current_level_index < levels.count() - 1:
        next_level = levels[tournament.current_level_index + 1]

    # Calculate stats
    registrations = tournament.registrations.all()
    players_remaining = registrations.filter(status='REGISTERED').count()
    total_entries = registrations.count() # Includes rebuys/addons in aggregation logic below if needed, but for now strict entries
    
    total_rebuys = registrations.aggregate(models.Sum('rebuys'))['rebuys__sum'] or 0
    total_addons = registrations.aggregate(models.Sum('addons'))['addons__sum'] or 0
    
    # Total chip count
    total_chips = (registrations.count() * tournament.stack) + \
                  (total_rebuys * tournament.stack) + \
                  (total_addons * tournament.stack)
                  
    average_stack = total_chips / players_remaining if players_remaining > 0 else 0

    data = {
        'status': tournament.status,
        'remaining_seconds': remaining,
        'level': {
            'number': current_level.level_number if current_level else 0,
            'small_blind': current_level.small_blind if current_level else 0,
            'big_blind': current_level.big_blind if current_level else 0,
            'ante': current_level.ante if current_level else 0,
            'is_break': current_level.is_break if current_level else False,
        } if current_level else None,
        'next_level': {
            'number': next_level.level_number if next_level else 0,
            'small_blind': next_level.small_blind if next_level else 0,
            'big_blind': next_level.big_blind if next_level else 0,
            'ante': next_level.ante if next_level else 0,
            'is_break': next_level.is_break if next_level else False,
        } if next_level else None,
        'players_remaining': players_remaining,
        'total_entries': total_entries + total_rebuys + total_addons, # Total logical entries
        'average_stack': round(average_stack),
        'prize_pool': (total_entries + total_rebuys + total_addons) * (tournament.buy_in or 0)
    }
    
    return JsonResponse(data)

@csrf_exempt
def get_players(request, tournament_id):
    from django.db.models import Case, When, Value, IntegerField, Q

    tournament = get_object_or_404(Tournament, id=tournament_id)

    # Custom sorting:
    # 1. REGISTERED players with table and seat (actively playing)
    # 2. REGISTERED players without table/seat (waiting to be seated)
    # 3. ELIMINATED players (ordered by place, best to worst)
    registrations = tournament.registrations.select_related('player', 'table').annotate(
        sort_priority=Case(
            # Priority 1: Active players at tables
            When(
                Q(status='REGISTERED') &
                Q(table__isnull=False) &
                Q(seat_number__isnull=False),
                then=Value(1)
            ),
            # Priority 2: Registered but not seated
            When(
                Q(status='REGISTERED') &
                (Q(table__isnull=True) | Q(seat_number__isnull=True)),
                then=Value(2)
            ),
            # Priority 3: Eliminated
            When(status='ELIMINATED', then=Value(3)),
            default=Value(4),
            output_field=IntegerField()
        )
    ).order_by('sort_priority', 'place', 'created_at')

    data = []
    for reg in registrations:
        data.append({
            'id': reg.id,
            'player_id': reg.player.id,
            'name': str(reg.player),
            'username': reg.player.username,
            'phone': reg.player.phone,
            'status': reg.status,
            'rebuys': reg.rebuys,
            'addons': reg.addons,
            'table': reg.table.table_number if reg.table else None,
            'seat_number': reg.seat_number,  # Changed from 'seat' to match frontend
            'place': reg.place,
            'bounty_count': reg.bounty_count,
            'points': reg.points or 0,
        })

    return JsonResponse({'players': data})

@csrf_exempt
def search_players(request):
    query = request.GET.get('q', '')
    tournament_id = request.GET.get('tournament_id')

    if len(query) < 2:
        return JsonResponse({'results': []})

    players = Player.objects.filter(
        models.Q(username__icontains=query) |
        models.Q(first_name__icontains=query) |
        models.Q(last_name__icontains=query)
    )

    # Exclude players already registered in this tournament
    if tournament_id:
        from .models import Registration
        registered_player_ids = list(Registration.objects.filter(
            tournament_id=tournament_id
        ).values_list('player_id', flat=True))

        print(f"DEBUG: Tournament ID: {tournament_id}")
        print(f"DEBUG: Registered player IDs: {registered_player_ids}")

        players = players.exclude(id__in=registered_player_ids)

    players = players[:10]

    print(f"DEBUG: Found players: {[p.id for p in players]}")

    results = [{'id': p.id, 'name': str(p)} for p in players]
    return JsonResponse({'results': results})

@csrf_exempt
def register_player(request, tournament_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    tournament = get_object_or_404(Tournament, id=tournament_id)
    data = json.loads(request.body)

    player_id = data.get('player_id')
    name = data.get('name')
    username = data.get('username')
    phone = data.get('phone')

    if player_id:
        player = get_object_or_404(Player, id=player_id)
    elif name:
        # Create new player
        # Use name as telegram_id for now if not provided, or generate one
        import uuid
        player = Player.objects.create(
            first_name=name,
            username=username if username else None,
            phone=phone if phone else None,
            telegram_id=str(uuid.uuid4()) # Placeholder
        )
    else:
        return JsonResponse({'error': 'Player name is required'}, status=400)

    # Check if already registered
    if tournament.registrations.filter(player=player).exists():
        return JsonResponse({'error': 'Player already registered'}, status=400)

    from .models import Registration
    reg = Registration.objects.create(
        tournament=tournament,
        player=player,
        status='REGISTERED'
    )

    return JsonResponse({
        'status': 'registered',
        'registration_id': reg.id,
        'player': {
            'id': player.id,
            'name': str(player)
        }
    })

def check_table_balance(tournament):
    """
    Check if tables need rebalancing or breaking after player elimination.
    Returns suggestions for player movements or table breaking.
    """
    from .models import Registration, Table

    tables = list(tournament.tables.all().order_by('table_number'))

    if len(tables) <= 1:
        return None  # Only one table, no balancing needed

    # Count players at each table
    table_data = []
    for table in tables:
        players = Registration.objects.filter(
            tournament=tournament,
            table=table,
            status='REGISTERED'
        ).exclude(seat_number__isnull=True).select_related('player')

        table_data.append({
            'table': table,
            'count': players.count(),
            'players': list(players)
        })

    # Sort by player count
    table_data.sort(key=lambda x: x['count'])

    min_table_data = table_data[0]
    max_table_data = table_data[-1]

    min_count = min_table_data['count']
    max_count = max_table_data['count']
    total_players = sum(t['count'] for t in table_data)

    # Check if we can break a table
    max_seats = tables[0].max_seats
    min_tables_needed = math.ceil(total_players / max_seats)

    if len(tables) > min_tables_needed and min_count > 0:
        # We can break the smallest table
        table_to_break = min_table_data['table']
        players_to_move = min_table_data['players']

        # Calculate where players should go
        movements = []
        remaining_tables = [t for t in table_data if t['table'].id != table_to_break.id]
        remaining_tables.sort(key=lambda x: x['count'])  # Start with emptiest tables

        for i, player_reg in enumerate(players_to_move):
            target_table = remaining_tables[i % len(remaining_tables)]['table']
            movements.append({
                'player_name': str(player_reg.player),
                'registration_id': player_reg.id,
                'from_table': table_to_break.table_number,
                'to_table': target_table.table_number,
            })
            # Update count for next iteration
            for t in remaining_tables:
                if t['table'].id == target_table.id:
                    t['count'] += 1
                    break

        return {
            'type': 'break_table',
            'table_number': table_to_break.table_number,
            'table_id': table_to_break.id,
            'movements': movements,
            'message': f'Table {table_to_break.table_number} can be broken. Move {len(movements)} player(s).'
        }

    # Check if tables are unbalanced (difference > 1)
    if max_count - min_count > 1:
        # Need to balance - move player(s) from max to min table
        max_table = max_table_data['table']
        min_table = min_table_data['table']

        # Calculate how many players need to be moved
        players_to_move = (max_count - min_count) // 2

        return {
            'type': 'balance',
            'from_table': max_table.table_number,
            'to_table': min_table.table_number,
            'players_count': players_to_move,
            'from_table_count': max_count,
            'to_table_count': min_count,
            'message': f'Move {players_to_move} player(s) from Table {max_table.table_number} to Table {min_table.table_number}'
        }

    return None  # Tables are balanced

@csrf_exempt
def eliminate_player(request, tournament_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    data = json.loads(request.body)
    registration_id = data.get('registration_id')
    bounty_count = data.get('bounty_count', 0)  # Number of players eliminated by this player

    from .models import Registration, Tournament
    reg = get_object_or_404(Registration, id=registration_id, tournament_id=tournament_id)
    tournament = get_object_or_404(Tournament, id=tournament_id)

    # Calculate place BEFORE changing status
    # Count players currently registered (including this one)
    remaining = Registration.objects.filter(tournament_id=tournament_id, status='REGISTERED').count()
    reg.place = remaining  # This player's place is equal to the number of registered players

    reg.status = 'ELIMINATED'
    reg.table = None
    reg.seat_number = None
    reg.bounty_count = int(bounty_count)

    # Calculate points for FREE tournaments
    if tournament.type == 'FREE':
        total_players = Registration.objects.filter(tournament_id=tournament_id).count()
        place = reg.place

        # Points calculation logic:
        # Last place (total_players) gets 1 point
        # Second to last gets 2 points, etc.
        # 3rd place gets 4th place + 3
        # 2nd place gets 3rd place + 3
        # 1st place gets 4th place * 2

        if place == total_players:
            # Last place
            base_points = 1
        elif place == total_players - 1:
            # Second to last
            base_points = 2
        elif place == 3:
            # Third place: 4th place points + 3
            fourth_place_points = total_players - 4 + 1  # Simple calculation for 4th
            base_points = fourth_place_points + 3
        elif place == 2:
            # Second place: 3rd place points + 3
            fourth_place_points = total_players - 4 + 1
            third_place_points = fourth_place_points + 3
            base_points = third_place_points + 3
        elif place == 1:
            # First place: 4th place * 2
            fourth_place_points = total_players - 4 + 1
            base_points = fourth_place_points * 2
        else:
            # For places 4 and below: (total_players - place + 1)
            base_points = total_players - place + 1

        # Add bounty points
        reg.points = base_points + reg.bounty_count
    else:
        reg.points = 0

    reg.save()

    # Check if player finished in a prize-paying position
    from .models import Payout
    payout_entry = Payout.objects.filter(tournament=tournament, place=reg.place).first()
    payout_amount = None

    print(f"DEBUG: Player eliminated at place {reg.place}")
    print(f"DEBUG: Looking for payout for place {reg.place}")
    print(f"DEBUG: Payout entry found: {payout_entry}")

    if payout_entry:
        # Assign player to this payout
        payout_entry.player = reg.player
        payout_entry.save()
        payout_amount = payout_entry.amount
        print(f"DEBUG: Assigned payout of ${payout_amount} to player {reg.player}")

    # For FREE tournaments, automatically advance to next level while preserving timer
    level_advanced = False
    if tournament.type == 'FREE':
        levels = tournament.levels.order_by('level_number')
        if tournament.current_level_index < levels.count() - 1:
            # Calculate current remaining time
            remaining_seconds = 0
            if tournament.status == 'RUNNING' and tournament.level_started_at:
                elapsed = (timezone.now() - tournament.level_started_at).total_seconds()
                remaining_seconds = max(0, int(tournament.timer_seconds - elapsed))
            elif tournament.timer_seconds is not None:
                remaining_seconds = tournament.timer_seconds

            # Advance to next level
            tournament.current_level_index += 1

            # Preserve the remaining time
            tournament.timer_seconds = remaining_seconds

            # Reset level start time if tournament is running
            if tournament.status == 'RUNNING':
                tournament.level_started_at = timezone.now()

            tournament.save()
            level_advanced = True

    # Check table balance after elimination
    balance_suggestion = check_table_balance(tournament)

    return JsonResponse({
        'status': 'eliminated',
        'place': reg.place,
        'bounty_count': reg.bounty_count,
        'points': reg.points,
        'payout_amount': payout_amount,
        'level_advanced': level_advanced,
        'new_level': tournament.current_level_index + 1 if level_advanced else None,
        'balance_suggestion': balance_suggestion
    })

@csrf_exempt
def rebuy_player(request, tournament_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
        
    data = json.loads(request.body)
    registration_id = data.get('registration_id')
    
    from .models import Registration
    reg = get_object_or_404(Registration, id=registration_id, tournament_id=tournament_id)
    
    reg.rebuys += 1
    reg.save()
    
    return JsonResponse({'status': 'rebuy_added', 'rebuys': reg.rebuys})

@csrf_exempt
def addon_player(request, tournament_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    data = json.loads(request.body)
    registration_id = data.get('registration_id')

    from .models import Registration
    reg = get_object_or_404(Registration, id=registration_id, tournament_id=tournament_id)

    reg.addons += 1
    reg.save()

    return JsonResponse({'status': 'addon_added', 'addons': reg.addons})

@csrf_exempt
def unregister_player(request, tournament_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    data = json.loads(request.body)
    registration_id = data.get('registration_id')

    from .models import Registration
    reg = get_object_or_404(Registration, id=registration_id, tournament_id=tournament_id)

    # Don't allow unregistering eliminated players
    if reg.status == 'ELIMINATED':
        return JsonResponse({'error': 'Cannot unregister eliminated player'}, status=400)

    # Store player name for response
    player_name = str(reg.player)

    # Delete the registration
    reg.delete()

    return JsonResponse({'status': 'unregistered', 'player_name': player_name})

# --- Table Management API ---

@csrf_exempt
def generate_tables(request, tournament_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
        
    tournament = get_object_or_404(Tournament, id=tournament_id)
    
    # 1. Clear existing tables
    tournament.tables.all().delete()
    
    # 2. Get registered players
    registrations = list(tournament.registrations.filter(status='REGISTERED'))
    player_count = len(registrations)
    
    if player_count == 0:
        return JsonResponse({'status': 'no_players'})
        
    # 3. Calculate tables needed
    # Assuming max 9 players per table for now (can be configurable later)
    MAX_SEATS = 9
    table_count = math.ceil(player_count / MAX_SEATS)
    
    # 4. Create tables
    from .models import Table
    tables = []
    for i in range(1, table_count + 1):
        tables.append(Table.objects.create(
            tournament=tournament,
            table_number=i,
            max_seats=MAX_SEATS
        ))
        
    # 5. Shuffle players
    random.shuffle(registrations)
    
    # 6. Assign players to tables (balancing logic with random seat assignment)
    # Simple distribution: fill tables evenly
    # e.g. 10 players, 2 tables -> 5 and 5

    base_players_per_table = player_count // table_count
    extra_players = player_count % table_count

    current_player_idx = 0

    for i, table in enumerate(tables):
        # Determine how many players on this table
        count = base_players_per_table + (1 if i < extra_players else 0)

        # Create list of all possible seat numbers for this table
        available_seats = list(range(1, MAX_SEATS + 1))
        random.shuffle(available_seats)  # Randomize seat order

        for seat_idx in range(count):
            if current_player_idx < player_count:
                reg = registrations[current_player_idx]
                reg.table = table
                reg.seat_number = available_seats[seat_idx]  # Random seat
                reg.save()
                current_player_idx += 1
                
    return JsonResponse({'status': 'tables_generated', 'table_count': table_count})

@csrf_exempt
def get_tables(request, tournament_id):
    tournament = get_object_or_404(Tournament, id=tournament_id)
    tables = tournament.tables.prefetch_related('registrations__player').all()
    
    data = []
    for table in tables:
        seats = []
        for reg in table.registrations.all():
            seats.append({
                'seat_number': reg.seat_number,
                'player_name': str(reg.player),
                'player_id': reg.player.id,
                'registration_id': reg.id,
                'stack': tournament.stack + (reg.rebuys * tournament.stack) + (reg.addons * tournament.stack) # Estimate stack
            })
        
        # Sort seats by number
        seats.sort(key=lambda x: x['seat_number'])
        
        data.append({
            'id': table.id,
            'number': table.table_number,
            'max_seats': table.max_seats,
            'seats': seats
        })
        
    return JsonResponse({'tables': data})

@csrf_exempt
def clear_tables(request, tournament_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    tournament = get_object_or_404(Tournament, id=tournament_id)

    # Clear assignments
    tournament.registrations.update(table=None, seat_number=None)

    # Delete tables
    tournament.tables.all().delete()

    return JsonResponse({'status': 'tables_cleared'})

@csrf_exempt
def add_table(request, tournament_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    data = json.loads(request.body)
    max_seats = data.get('max_seats', 9)

    tournament = get_object_or_404(Tournament, id=tournament_id)

    # Find next table number
    existing_tables = tournament.tables.all()
    if existing_tables.exists():
        next_number = existing_tables.order_by('-table_number').first().table_number + 1
    else:
        next_number = 1

    # Create new table
    from .models import Table
    table = Table.objects.create(
        tournament=tournament,
        table_number=next_number,
        max_seats=max_seats
    )

    return JsonResponse({
        'status': 'table_added',
        'table': {
            'id': table.id,
            'number': table.table_number,
            'max_seats': table.max_seats
        }
    })

@csrf_exempt
def delete_table(request, tournament_id, table_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    from .models import Table, Registration

    tournament = get_object_or_404(Tournament, id=tournament_id)
    table = get_object_or_404(Table, id=table_id, tournament=tournament)

    # Check if table has any seated players
    seated_players = Registration.objects.filter(
        tournament=tournament,
        table=table,
        status='REGISTERED'
    ).exclude(seat_number__isnull=True).count()

    if seated_players > 0:
        return JsonResponse({
            'error': f'Cannot delete table with {seated_players} seated player(s). Move them first.'
        }, status=400)

    # Delete the table
    table_number = table.table_number
    table.delete()

    return JsonResponse({
        'status': 'table_deleted',
        'table_number': table_number
    })

@csrf_exempt
def seat_selected_players(request, tournament_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    data = json.loads(request.body)
    registration_ids = data.get('registration_ids', [])

    if not registration_ids:
        return JsonResponse({'error': 'No players selected'}, status=400)

    tournament = get_object_or_404(Tournament, id=tournament_id)

    # Get available tables
    from .models import Table, Registration
    tables = list(tournament.tables.all().order_by('table_number'))

    if not tables:
        return JsonResponse({'status': 'no_tables'})

    # DEBUG: Check all selected registrations first
    all_selected = Registration.objects.filter(
        id__in=registration_ids,
        tournament=tournament,
        status='REGISTERED'
    )

    print(f"\n=== SEATING DEBUG ===")
    print(f"Selected registration IDs: {registration_ids}")
    print(f"Found {all_selected.count()} REGISTERED players")

    for reg in all_selected:
        print(f"  Player: {reg.player}, table={reg.table}, seat_number={reg.seat_number}")

    # Get selected registrations (only those without seats)
    # A player is considered unseated if they don't have a seat_number
    # (matching the frontend logic in tables.js)
    registrations = Registration.objects.filter(
        id__in=registration_ids,
        tournament=tournament,
        status='REGISTERED',
        seat_number__isnull=True  # Only players without a seat number
    ).order_by('?')  # Random order

    print(f"After filtering by seat_number__isnull=True: {registrations.count()} players")

    # Clean up any players with table but no seat_number (invalid state)
    # This ensures clean seating assignment
    registrations.update(table=None)

    if not registrations.exists():
        print("ERROR: No unseated players found!")
        return JsonResponse({
            'status': 'players_seated',
            'seated_count': 0,
            'message': 'All selected players are already seated'
        })

    # BALANCED SEATING ALGORITHM
    # Calculate current occupancy for each table
    table_occupancy = {}
    table_occupied_seats = {}

    for table in tables:
        occupied_seats = set(
            Registration.objects.filter(
                tournament=tournament,
                table=table,
                status='REGISTERED'
            ).exclude(seat_number__isnull=True)
            .values_list('seat_number', flat=True)
        )
        table_occupancy[table.id] = len(occupied_seats)
        table_occupied_seats[table.id] = occupied_seats

    print(f"Initial table occupancy: {table_occupancy}")

    # Shuffle players for randomness
    registrations_list = list(registrations)
    random.shuffle(registrations_list)

    # Seat players with balanced distribution
    seated_count = 0
    for reg in registrations_list:
        # Find table with least players that has space
        available_tables = [
            (table, table_occupancy[table.id])
            for table in tables
            if table_occupancy[table.id] < table.max_seats
        ]

        if not available_tables:
            # No more space in any table
            break

        # Sort by occupancy (least occupied first)
        available_tables.sort(key=lambda x: x[1])
        selected_table = available_tables[0][0]

        # Find available seats at this table
        occupied_seats = table_occupied_seats[selected_table.id]
        available_seat_numbers = [
            seat_num for seat_num in range(1, selected_table.max_seats + 1)
            if seat_num not in occupied_seats
        ]

        if available_seat_numbers:
            # Choose random seat from available seats
            seat_num = random.choice(available_seat_numbers)

            # Assign seat
            reg.table = selected_table
            reg.seat_number = seat_num
            reg.save()

            # Update occupancy tracking
            table_occupancy[selected_table.id] += 1
            table_occupied_seats[selected_table.id].add(seat_num)

            seated_count += 1
            print(f"Seated {reg.player} at Table {selected_table.table_number}, Seat {seat_num}")

    if seated_count == 0:
        # Debug info
        total_capacity = sum(t.max_seats for t in tables)
        currently_seated = Registration.objects.filter(
            tournament=tournament,
            status='REGISTERED',
            table__isnull=False
        ).count()

        return JsonResponse({
            'status': 'no_space',
            'debug': {
                'total_capacity': total_capacity,
                'currently_seated': currently_seated,
                'tables_count': len(tables),
                'players_to_seat': len(registration_ids)
            }
        })

    return JsonResponse({
        'status': 'players_seated',
        'seated_count': seated_count
    })

@csrf_exempt
def move_player(request, tournament_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    data = json.loads(request.body)
    registration_id = data.get('registration_id')
    table_id = data.get('table_id')
    seat_number = data.get('seat_number')

    from .models import Registration, Table

    reg = get_object_or_404(Registration, id=registration_id, tournament_id=tournament_id)

    if table_id:
        table = get_object_or_404(Table, id=table_id, tournament_id=tournament_id)

        # Check if seat is taken
        if table.registrations.filter(seat_number=seat_number).exclude(id=registration_id).exists():
             return JsonResponse({'error': 'Seat already taken'}, status=400)

        reg.table = table
        reg.seat_number = seat_number
    else:
        # Unseat player
        reg.table = None
        reg.seat_number = None

    reg.save()

    return JsonResponse({'status': 'moved'})

# --- Blind Structure Management API ---

def get_levels(request, tournament_id):
    tournament = get_object_or_404(Tournament, id=tournament_id)
    levels = tournament.levels.order_by('level_number').all()

    data = []
    for level in levels:
        data.append({
            'id': level.id,
            'level_number': level.level_number,
            'small_blind': level.small_blind,
            'big_blind': level.big_blind,
            'ante': level.ante,
            'duration': level.duration,
            'is_break': level.is_break,
        })

    return JsonResponse({'levels': data})

@csrf_exempt
def add_level(request, tournament_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    tournament = get_object_or_404(Tournament, id=tournament_id)
    data = json.loads(request.body)

    from .models import TournamentLevel
    level = TournamentLevel.objects.create(
        tournament=tournament,
        level_number=data.get('level_number'),
        small_blind=data.get('small_blind', 0),
        big_blind=data.get('big_blind', 0),
        ante=data.get('ante', 0),
        duration=data.get('duration', 15),
        is_break=data.get('is_break', False),
    )

    return JsonResponse({
        'status': 'level_added',
        'level_id': level.id
    })

@csrf_exempt
def update_level(request, tournament_id, level_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    from .models import TournamentLevel
    level = get_object_or_404(TournamentLevel, id=level_id, tournament_id=tournament_id)
    data = json.loads(request.body)

    level.level_number = data.get('level_number', level.level_number)
    level.small_blind = data.get('small_blind', level.small_blind)
    level.big_blind = data.get('big_blind', level.big_blind)
    level.ante = data.get('ante', level.ante)
    level.duration = data.get('duration', level.duration)
    level.is_break = data.get('is_break', level.is_break)
    level.save()

    return JsonResponse({'status': 'level_updated'})

@csrf_exempt
def delete_level(request, tournament_id, level_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    from .models import TournamentLevel
    level = get_object_or_404(TournamentLevel, id=level_id, tournament_id=tournament_id)
    level.delete()

    return JsonResponse({'status': 'level_deleted'})

# --- Payout Management API ---

def get_payouts(request, tournament_id):
    tournament = get_object_or_404(Tournament, id=tournament_id)
    payouts = tournament.payouts.select_related('player').order_by('place')

    data = []
    for payout in payouts:
        data.append({
            'id': payout.id,
            'place': payout.place,
            'amount': payout.amount,
            'player_name': str(payout.player) if payout.player else None,
            'description': payout.description,
        })

    # Calculate total prize pool
    registrations = tournament.registrations.all()
    total_rebuys = registrations.aggregate(models.Sum('rebuys'))['rebuys__sum'] or 0
    total_addons = registrations.aggregate(models.Sum('addons'))['addons__sum'] or 0
    total_entries = registrations.count() + total_rebuys + total_addons
    prize_pool = total_entries * (tournament.buy_in or 0)

    return JsonResponse({
        'payouts': data,
        'prize_pool': prize_pool,
        'places_paid': len(data)
    })

@csrf_exempt
def generate_payouts(request, tournament_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    tournament = get_object_or_404(Tournament, id=tournament_id)

    # Clear existing payouts
    tournament.payouts.all().delete()

    # Calculate prize pool
    registrations = tournament.registrations.all()
    total_rebuys = registrations.aggregate(models.Sum('rebuys'))['rebuys__sum'] or 0
    total_addons = registrations.aggregate(models.Sum('addons'))['addons__sum'] or 0
    total_entries = registrations.count() + total_rebuys + total_addons
    prize_pool = total_entries * (tournament.buy_in or 0)

    if prize_pool == 0:
        return JsonResponse({'error': 'Prize pool is zero. Cannot generate payouts.'}, status=400)

    # Standard payout structure based on player count
    # This is a common structure used in poker tournaments
    from .models import Payout

    if total_entries <= 10:
        # 1-10 players: Top 2 places paid
        places_paid = min(2, total_entries)
        payout_percentages = [0.70, 0.30]  # 70% / 30%
    elif total_entries <= 20:
        # 11-20 players: Top 3 places paid
        places_paid = 3
        payout_percentages = [0.50, 0.30, 0.20]  # 50% / 30% / 20%
    elif total_entries <= 30:
        # 21-30 players: Top 4 places paid
        places_paid = 4
        payout_percentages = [0.45, 0.27, 0.18, 0.10]  # 45% / 27% / 18% / 10%
    else:
        # 31+ players: Top 5 places paid
        places_paid = 5
        payout_percentages = [0.40, 0.25, 0.17, 0.11, 0.07]  # 40% / 25% / 17% / 11% / 7%

    # Create payout entries
    for place in range(1, places_paid + 1):
        amount = int(prize_pool * payout_percentages[place - 1])
        # Round to nearest 10
        amount = round(amount / 10) * 10
        Payout.objects.create(
            tournament=tournament,
            place=place,
            amount=amount,
            description=f"Place {place}"
        )

    return JsonResponse({
        'status': 'payouts_generated',
        'places_paid': places_paid,
        'prize_pool': prize_pool
    })

@csrf_exempt
def add_payout(request, tournament_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    tournament = get_object_or_404(Tournament, id=tournament_id)
    data = json.loads(request.body)

    place = data.get('place')
    amount = data.get('amount')

    if not place or not amount:
        return JsonResponse({'error': 'Place and amount are required'}, status=400)

    from .models import Payout
    payout = Payout.objects.create(
        tournament=tournament,
        place=place,
        amount=amount,
        description=data.get('description', f"Place {place}")
    )

    return JsonResponse({
        'status': 'payout_added',
        'payout': {
            'id': payout.id,
            'place': payout.place,
            'amount': payout.amount,
            'description': payout.description
        }
    })

@csrf_exempt
def update_payout(request, tournament_id, payout_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    from .models import Payout
    payout = get_object_or_404(Payout, id=payout_id, tournament_id=tournament_id)
    data = json.loads(request.body)

    if 'place' in data:
        payout.place = data['place']
    if 'amount' in data:
        payout.amount = data['amount']
    if 'description' in data:
        payout.description = data['description']

    payout.save()

    return JsonResponse({
        'status': 'payout_updated',
        'payout': {
            'id': payout.id,
            'place': payout.place,
            'amount': payout.amount,
            'description': payout.description
        }
    })

@csrf_exempt
def delete_payout(request, tournament_id, payout_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    from .models import Payout
    payout = get_object_or_404(Payout, id=payout_id, tournament_id=tournament_id)
    payout.delete()

    return JsonResponse({'status': 'payout_deleted'})

# --- Statistics API ---

def paid_tournament_results(request):
    """
    Returns tournament results matrix for PAID tournaments.
    Shows player placements across all finished PAID tournaments.
    """
    from .models import Registration

    # Get all finished PAID tournaments
    tournaments = Tournament.objects.filter(
        type='PAID',
        status='FINISHED'
    )

    # Apply date filters if provided
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    if date_from:
        tournaments = tournaments.filter(date__gte=date_from)
    if date_to:
        tournaments = tournaments.filter(date__lte=date_to)

    tournaments = tournaments.order_by('date')

    if not tournaments.exists():
        return JsonResponse({'players': [], 'tournaments': []})

    # Get all players who participated in any PAID tournament
    player_ids = Registration.objects.filter(
        tournament__type='PAID',
        tournament__status='FINISHED'
    ).values_list('player_id', flat=True).distinct()

    players = Player.objects.filter(id__in=player_ids).order_by('first_name', 'last_name')

    # Build tournament list
    tournaments_data = []
    for t in tournaments:
        tournaments_data.append({
            'id': t.id,
            'name': t.name,
            'date': t.date.isoformat() if t.date else None
        })

    # Build players data with results matrix
    players_data = []
    for player in players:
        results = {}

        # Get all registrations for this player in PAID tournaments
        registrations = Registration.objects.filter(
            player=player,
            tournament__type='PAID',
            tournament__status='FINISHED'
        ).select_related('tournament')

        for reg in registrations:
            results[reg.tournament_id] = {
                'place': reg.place
            }

        players_data.append({
            'player_id': player.id,
            'player_name': str(player),
            'results': results
        })

    return JsonResponse({
        'tournaments': tournaments_data,
        'players': players_data
    })

def paid_payout_leaders(request):
    """
    Returns leaderboard of players by total winnings in PAID tournaments.
    """
    from .models import Payout, Registration
    from django.db.models import Sum, Count, Q

    # Apply date filters if provided
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    # Get all players who have received payouts
    payouts_query = Payout.objects.filter(
        tournament__type='PAID',
        tournament__status='FINISHED',
        player__isnull=False
    )

    if date_from:
        payouts_query = payouts_query.filter(tournament__date__gte=date_from)
    if date_to:
        payouts_query = payouts_query.filter(tournament__date__lte=date_to)

    players_with_payouts = payouts_query.values('player_id').distinct()

    leaders = []

    for p in players_with_payouts:
        player = Player.objects.get(id=p['player_id'])

        # Calculate total winnings
        winnings_query = Payout.objects.filter(
            player=player,
            tournament__type='PAID',
            tournament__status='FINISHED'
        )
        if date_from:
            winnings_query = winnings_query.filter(tournament__date__gte=date_from)
        if date_to:
            winnings_query = winnings_query.filter(tournament__date__lte=date_to)
        total_winnings = winnings_query.aggregate(total=Sum('amount'))['total'] or 0

        # Count tournaments played
        tournaments_query = Registration.objects.filter(
            player=player,
            tournament__type='PAID',
            tournament__status='FINISHED'
        )
        if date_from:
            tournaments_query = tournaments_query.filter(tournament__date__gte=date_from)
        if date_to:
            tournaments_query = tournaments_query.filter(tournament__date__lte=date_to)
        tournaments_played = tournaments_query.count()

        # Count first places
        first_places_query = Registration.objects.filter(
            player=player,
            tournament__type='PAID',
            tournament__status='FINISHED',
            place=1
        )
        if date_from:
            first_places_query = first_places_query.filter(tournament__date__gte=date_from)
        if date_to:
            first_places_query = first_places_query.filter(tournament__date__lte=date_to)
        first_places = first_places_query.count()

        leaders.append({
            'player_id': player.id,
            'player_name': str(player),
            'total_winnings': float(total_winnings),
            'tournaments_played': tournaments_played,
            'first_places': first_places
        })

    # Sort by total winnings (descending)
    leaders.sort(key=lambda x: x['total_winnings'], reverse=True)

    return JsonResponse({'leaders': leaders})

def paid_rebuy_leaders(request):
    """
    Returns leaderboard of players by total rebuys in PAID tournaments.
    """
    from .models import Registration
    from django.db.models import Sum, Count

    # Apply date filters if provided
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    # Get all players who participated in PAID tournaments
    rebuys_query = Registration.objects.filter(
        tournament__type='PAID',
        tournament__status='FINISHED'
    )

    if date_from:
        rebuys_query = rebuys_query.filter(tournament__date__gte=date_from)
    if date_to:
        rebuys_query = rebuys_query.filter(tournament__date__lte=date_to)

    players_with_rebuys = rebuys_query.values('player_id').annotate(
        total_rebuys=Sum('rebuys'),
        tournaments_count=Count('id')
    ).filter(total_rebuys__gt=0).order_by('-total_rebuys')

    leaders = []

    for p in players_with_rebuys:
        player = Player.objects.get(id=p['player_id'])

        total_rebuys = p['total_rebuys'] or 0
        tournaments_played = p['tournaments_count']
        avg_rebuys = total_rebuys / tournaments_played if tournaments_played > 0 else 0

        leaders.append({
            'player_id': player.id,
            'player_name': str(player),
            'total_rebuys': total_rebuys,
            'tournaments_played': tournaments_played,
            'avg_rebuys': round(avg_rebuys, 2)
        })

    return JsonResponse({'leaders': leaders})

def free_tournament_results(request):
    """
    Returns tournament results matrix for FREE tournaments.
    Shows player placements across all finished FREE tournaments.
    """
    from .models import Registration
    from datetime import datetime

    # Get all finished FREE tournaments
    tournaments = Tournament.objects.filter(
        type='FREE',
        status='FINISHED'
    )

    # Apply date filters or season filter
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    season = request.GET.get('season')
    year = request.GET.get('year')

    if season:
        # Convert season to date range
        if year:
            season_year = int(year)
        else:
            season_year = datetime.now().year

        season_ranges = {
            'winter': (f'{season_year}-12-01', f'{season_year + 1}-02-28'),
            'spring': (f'{season_year}-03-01', f'{season_year}-05-31'),
            'summer': (f'{season_year}-06-01', f'{season_year}-08-31'),
            'autumn': (f'{season_year}-09-01', f'{season_year}-11-30'),
        }
        if season in season_ranges:
            date_from, date_to = season_ranges[season]

    if date_from:
        tournaments = tournaments.filter(date__gte=date_from)
    if date_to:
        tournaments = tournaments.filter(date__lte=date_to)

    tournaments = tournaments.order_by('date')

    if not tournaments.exists():
        return JsonResponse({'players': [], 'tournaments': []})

    # Get all players who participated in any FREE tournament
    player_ids = Registration.objects.filter(
        tournament__type='FREE',
        tournament__status='FINISHED'
    ).values_list('player_id', flat=True).distinct()

    players = Player.objects.filter(id__in=player_ids).order_by('first_name', 'last_name')

    # Build tournament list
    tournaments_data = []
    for t in tournaments:
        tournaments_data.append({
            'id': t.id,
            'name': t.name,
            'date': t.date.isoformat() if t.date else None
        })

    # Build players data with results matrix
    players_data = []
    for player in players:
        results = {}

        # Get all registrations for this player in FREE tournaments
        registrations = Registration.objects.filter(
            player=player,
            tournament__type='FREE',
            tournament__status='FINISHED'
        ).select_related('tournament')

        for reg in registrations:
            results[reg.tournament_id] = {
                'place': reg.place,
                'points': reg.points or 0
            }

        players_data.append({
            'player_id': player.id,
            'player_name': str(player),
            'results': results
        })

    return JsonResponse({
        'tournaments': tournaments_data,
        'players': players_data
    })

def free_bounty_leaders(request):
    """
    Returns leaderboard of players by total bounties in FREE tournaments.
    """
    from .models import Registration
    from django.db.models import Sum, Count
    from datetime import datetime

    # Apply date filters or season filter
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    season = request.GET.get('season')
    year = request.GET.get('year')

    if season:
        # Convert season to date range
        if year:
            season_year = int(year)
        else:
            season_year = datetime.now().year

        season_ranges = {
            'winter': (f'{season_year}-12-01', f'{season_year + 1}-02-28'),
            'spring': (f'{season_year}-03-01', f'{season_year}-05-31'),
            'summer': (f'{season_year}-06-01', f'{season_year}-08-31'),
            'autumn': (f'{season_year}-09-01', f'{season_year}-11-30'),
        }
        if season in season_ranges:
            date_from, date_to = season_ranges[season]

    # Get all players who participated in FREE tournaments
    bounties_query = Registration.objects.filter(
        tournament__type='FREE',
        tournament__status='FINISHED'
    )

    if date_from:
        bounties_query = bounties_query.filter(tournament__date__gte=date_from)
    if date_to:
        bounties_query = bounties_query.filter(tournament__date__lte=date_to)

    players_with_bounties = bounties_query.values('player_id').annotate(
        total_bounties=Sum('bounty_count'),
        tournaments_count=Count('id')
    ).filter(total_bounties__gt=0).order_by('-total_bounties')

    leaders = []

    for p in players_with_bounties:
        player = Player.objects.get(id=p['player_id'])

        total_bounties = p['total_bounties'] or 0
        tournaments_played = p['tournaments_count']
        avg_bounties = total_bounties / tournaments_played if tournaments_played > 0 else 0

        leaders.append({
            'player_id': player.id,
            'player_name': str(player),
            'total_bounties': total_bounties,
            'tournaments_played': tournaments_played,
            'avg_bounties': round(avg_bounties, 2)
        })

    return JsonResponse({'leaders': leaders})

def get_tournament_years(request):
    """
    Returns list of unique years from tournaments for season filtering.
    """
    from django.db.models.functions import ExtractYear

    tournament_type = request.GET.get('type', 'FREE')

    years = Tournament.objects.filter(
        type=tournament_type,
        status='FINISHED'
    ).annotate(
        year=ExtractYear('date')
    ).values_list('year', flat=True).distinct().order_by('-year')

    return JsonResponse({'years': list(years)})

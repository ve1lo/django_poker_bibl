from django.shortcuts import render, get_object_or_404, redirect
from django.db import models
from .models import Tournament, Player, Registration, Table, Payout, TournamentLevel, TournamentTemplate, TemplateLevel
from .forms import TournamentTemplateForm, TournamentForm, TemplateLevelFormSet

from django.contrib import messages

def dashboard(request):
    tournaments = Tournament.objects.all()

    # Get filter parameters
    tournament_type = request.GET.get('type', '')
    status = request.GET.get('status', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    # Apply filters
    if tournament_type:
        tournaments = tournaments.filter(type=tournament_type)

    if status:
        tournaments = tournaments.filter(status=status)

    if date_from:
        tournaments = tournaments.filter(date__gte=date_from)

    if date_to:
        tournaments = tournaments.filter(date__lte=date_to)

    tournaments = tournaments.order_by('-date')

    return render(request, 'core/dashboard.html', {
        'tournaments': tournaments,
        'filters': {
            'type': tournament_type,
            'status': status,
            'date_from': date_from,
            'date_to': date_to,
        }
    })

def tournament_control(request, tournament_id):
    tournament = get_object_or_404(Tournament, id=tournament_id)
    return render(request, 'core/tournament_control.html', {'tournament': tournament})

def tournament_display(request, tournament_id):
    tournament = get_object_or_404(Tournament, id=tournament_id)
    
    # Calculate stats
    registrations = Registration.objects.filter(tournament=tournament)
    players_remaining = registrations.filter(status='REGISTERED').count()
    
    total_rebuys = registrations.aggregate(models.Sum('rebuys'))['rebuys__sum'] or 0
    total_addons = registrations.aggregate(models.Sum('addons'))['addons__sum'] or 0
    
    # Total entries = unique players + rebuys + addons
    total_entries = registrations.count() + total_rebuys + total_addons
    
    prize_pool = 0
    if tournament.buy_in:
        prize_pool = total_entries * tournament.buy_in
        
    levels = tournament.levels.order_by('level_number')
    current_level = None
    if levels.exists() and tournament.current_level_index < levels.count():
        current_level = levels[tournament.current_level_index]

    context = {
        'tournament': tournament,
        'players_remaining': players_remaining,
        'total_entries': total_entries,
        'total_rebuys': total_rebuys,
        'total_addons': total_addons,
        'prize_pool': prize_pool,
        'current_level': current_level,
    }
    return render(request, 'core/tournament_display.html', context)

# --- Template Views ---

def template_list(request):
    templates = TournamentTemplate.objects.all().order_by('-created_at')
    return render(request, 'core/template_list.html', {'templates': templates})

def template_create(request):
    if request.method == 'POST':
        form = TournamentTemplateForm(request.POST)
        formset = TemplateLevelFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            template = form.save()
            formset.instance = template
            formset.save()
            messages.success(request, 'Template created successfully.')
            return redirect('template_list')
    else:
        form = TournamentTemplateForm()
        formset = TemplateLevelFormSet()
    return render(request, 'core/template_form.html', {'form': form, 'formset': formset, 'title': 'Create Template'})

def template_edit(request, template_id):
    template = get_object_or_404(TournamentTemplate, id=template_id)
    if request.method == 'POST':
        form = TournamentTemplateForm(request.POST, instance=template)
        formset = TemplateLevelFormSet(request.POST, instance=template)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, 'Template updated successfully.')
            return redirect('template_list')
    else:
        form = TournamentTemplateForm(instance=template)
        formset = TemplateLevelFormSet(instance=template)
    return render(request, 'core/template_form.html', {'form': form, 'formset': formset, 'title': 'Edit Template'})

def template_delete(request, template_id):
    template = get_object_or_404(TournamentTemplate, id=template_id)
    if request.method == 'POST':
        template.delete()
        messages.success(request, 'Template deleted successfully.')
        return redirect('template_list')
    return render(request, 'core/template_confirm_delete.html', {'template': template})

# --- Tournament Views ---

def tournament_create(request):
    if request.method == 'POST':
        form = TournamentForm(request.POST)
        if form.is_valid():
            tournament = form.save(commit=False)
            template = form.cleaned_data.get('template')
            
            if template:
                # Copy settings from template if not overridden (though form overrides)
                # Actually form fields take precedence, but we copy levels
                pass
            
            tournament.save()
            
            if template:
                # Copy levels
                for t_level in template.levels.all():
                    TournamentLevel.objects.create(
                        tournament=tournament,
                        level_number=t_level.level_number,
                        small_blind=t_level.small_blind,
                        big_blind=t_level.big_blind,
                        ante=t_level.ante,
                        duration=t_level.duration,
                        is_break=t_level.is_break
                    )
            else:
                # Create default levels if no template
                for i in range(1, 11):
                    TournamentLevel.objects.create(
                        tournament=tournament,
                        level_number=i,
                        small_blind=50 * (2**i), # Exponential structure example
                        big_blind=100 * (2**i),
                        ante=0,
                        duration=20
                    )
            
            messages.success(request, 'Tournament created successfully.')
            return redirect('dashboard')
    else:
        form = TournamentForm()
    return render(request, 'core/tournament_form.html', {'form': form})

def profile(request):
    # Player is available from context_processors
    # Check if player is logged in
    if 'player_id' not in request.session:
        return redirect('dashboard')

    player = get_object_or_404(Player, id=request.session['player_id'])

    # Calculate stats
    registrations = Registration.objects.filter(player=player)
    total_games = registrations.count()
    total_wins = registrations.filter(place=1).count()
    total_points = registrations.aggregate(models.Sum('points'))['points__sum'] or 0

    # Calculate total winnings
    from .models import Payout
    total_winnings = Payout.objects.filter(player=player).aggregate(models.Sum('amount'))['amount__sum'] or 0

    # Calculate total spent (buy-ins + rebuys + addons) for PAID tournaments only
    total_spent = 0
    paid_registrations = registrations.filter(tournament__type='PAID')
    for reg in paid_registrations:
        buy_in = reg.tournament.buy_in or 0
        # Initial buy-in + rebuys + addons
        total_spent += buy_in * (1 + reg.rebuys + reg.addons)

    # Calculate profit/loss
    profit_loss = total_winnings - total_spent

    avg_place = 0
    if total_games > 0:
        avg_place = registrations.aggregate(models.Avg('place'))['place__avg'] or 0

    # FREE tournaments history
    free_tournaments = registrations.filter(
        tournament__type='FREE'
    ).select_related('tournament').order_by('-tournament__date')

    # PAID tournaments history with payouts
    paid_tournaments_list = []
    paid_regs = registrations.filter(
        tournament__type='PAID'
    ).select_related('tournament').order_by('-tournament__date')

    # Get payouts for paid tournaments
    payouts = Payout.objects.filter(player=player).select_related('tournament')
    payouts_dict = {p.tournament_id: p.amount for p in payouts}

    # Combine registrations with payouts
    for reg in paid_regs:
        paid_tournaments_list.append({
            'registration': reg,
            'payout': payouts_dict.get(reg.tournament_id)
        })

    context = {
        'player': player,
        'stats': {
            'total_games': total_games,
            'total_wins': total_wins,
            'total_points': total_points,
            'total_winnings': total_winnings,
            'total_spent': total_spent,
            'profit_loss': profit_loss,
            'avg_place': round(avg_place, 1)
        },
        'free_tournaments': free_tournaments,
        'paid_tournaments': paid_tournaments_list
    }

    return render(request, 'core/profile.html', context)

def logout_view(request):
    """Logout user by clearing session"""
    if 'player_id' in request.session:
        del request.session['player_id']
    return redirect('dashboard')

def tournament_info(request, tournament_id):
    """Tournament information page for players"""
    tournament = get_object_or_404(Tournament, id=tournament_id)

    # Get all registrations with payouts, sorted by status then place
    # Active players first, then eliminated players sorted by place (ascending)
    registrations = tournament.registrations.select_related('player').all().order_by(
        models.Case(
            models.When(status='REGISTERED', then=0),
            models.When(status='ELIMINATED', then=1),
            default=2
        ),
        models.Case(
            models.When(place__isnull=True, then=999999),
            default='place'
        )
    )

    # Get payouts for this tournament
    payouts = Payout.objects.filter(tournament=tournament).select_related('player')
    payouts_dict = {p.player_id: p.amount for p in payouts if p.player_id}

    # Combine registrations with payout info
    players_data = []
    for reg in registrations:
        players_data.append({
            'registration': reg,
            'payout': payouts_dict.get(reg.player_id)
        })

    context = {
        'tournament': tournament,
        'players_data': players_data,
    }

    return render(request, 'core/tournament_info.html', context)

def paid_tournaments_stats(request):
    """Statistics page for PAID tournaments"""
    # Get all finished PAID tournaments
    tournaments = Tournament.objects.filter(
        type='PAID',
        status='FINISHED'
    ).order_by('-date')

    context = {
        'tournaments': tournaments,
    }

    return render(request, 'core/paid_tournaments_stats.html', context)

def free_tournaments_stats(request):
    """Statistics page for FREE tournaments"""
    # Get all finished FREE tournaments
    tournaments = Tournament.objects.filter(
        type='FREE',
        status='FINISHED'
    ).order_by('-date')

    context = {
        'tournaments': tournaments,
    }

    return render(request, 'core/free_tournaments_stats.html', context)

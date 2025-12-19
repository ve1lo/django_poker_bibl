from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from .models import LoginToken, RegistrationToken
from .forms import PlayerRegistrationForm
from core.models import Player

def bot_login(request, token):
    login_token = get_object_or_404(LoginToken, token=token)

    if login_token.is_used:
        # If already logged in as this player, just redirect
        if request.session.get('player_id') == login_token.player.id:
            messages.info(request, f'You are already logged in as {login_token.player}!')
            return redirect('profile')
        messages.error(request, 'This login link has already been used. Please request a new one from the bot.')
        return redirect('dashboard')

    # In a real app, check expiration time here

    # Log the user in by setting session
    request.session['player_id'] = login_token.player.id
    request.session.modified = True  # Force session save

    # Mark token as used
    login_token.is_used = True
    login_token.save()

    messages.success(request, f'Successfully logged in as {login_token.player}!')
    return redirect('profile')

def bot_register(request, token):
    reg_token = get_object_or_404(RegistrationToken, token=token)

    if reg_token.is_used:
        messages.error(request, 'This registration link has already been used.')
        return redirect('dashboard')

    # Check if player already exists with this telegram_id
    existing_player = Player.objects.filter(telegram_id=reg_token.telegram_id).first()
    if existing_player:
        messages.info(request, 'You are already registered! Please use the login link from the bot.')
        return redirect('dashboard')

    if request.method == 'POST':
        form = PlayerRegistrationForm(request.POST)
        if form.is_valid():
            # Create player with telegram data
            player = form.save(commit=False)
            player.telegram_id = reg_token.telegram_id
            player.username = reg_token.telegram_username
            # Override with telegram data if form fields are empty
            if not player.first_name:
                player.first_name = reg_token.telegram_first_name
            if not player.last_name:
                player.last_name = reg_token.telegram_last_name
            player.save()

            # Mark token as used
            reg_token.is_used = True
            reg_token.save()

            # Log the user in
            request.session['player_id'] = player.id
            request.session.modified = True

            messages.success(request, f'Welcome, {player.first_name}! Your account has been created.')
            return redirect('profile')
    else:
        # Pre-fill form with telegram data
        initial_data = {
            'first_name': reg_token.telegram_first_name,
            'last_name': reg_token.telegram_last_name,
        }
        form = PlayerRegistrationForm(initial=initial_data)

    return render(request, 'bot/register.html', {
        'form': form,
        'telegram_username': reg_token.telegram_username,
    })

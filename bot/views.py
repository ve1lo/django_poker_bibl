from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from .models import LoginToken

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

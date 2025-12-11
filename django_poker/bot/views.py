from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from .models import LoginToken

def bot_login(request, token):
    login_token = get_object_or_404(LoginToken, token=token)
    
    if login_token.is_used:
        messages.error(request, 'This login link has already been used.')
        return redirect('dashboard')
        
    # In a real app, check expiration time here
    
    # Log the user in by setting session
    request.session['player_id'] = login_token.player.id
    
    # Mark token as used
    login_token.is_used = True
    login_token.save()
    
    messages.success(request, f'Welcome back, {login_token.player}!')
    return redirect('dashboard')

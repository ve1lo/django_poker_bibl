from django.urls import path
from . import views

urlpatterns = [
    path('login/<uuid:token>/', views.bot_login, name='bot_login'),
]

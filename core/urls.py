from django.urls import path, include
from . import views, api

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('profile/', views.profile, name='profile'),
    path('logout/', views.logout_view, name='logout'),
    path('tournament/add/', views.tournament_create, name='tournament_create'),
    path('tournament/<int:tournament_id>/control/', views.tournament_control, name='tournament_control'),
    path('tournament/<int:tournament_id>/display/', views.tournament_display, name='tournament_display'),
    path('tournament/<int:tournament_id>/info/', views.tournament_info, name='tournament_info'),

    # Statistics
    path('stats/paid/', views.paid_tournaments_stats, name='paid_tournaments_stats'),
    path('stats/free/', views.free_tournaments_stats, name='free_tournaments_stats'),

    # Templates
    path('templates/', views.template_list, name='template_list'),
    path('templates/add/', views.template_create, name='template_create'),
    path('templates/<int:template_id>/edit/', views.template_edit, name='template_edit'),
    path('templates/<int:template_id>/delete/', views.template_delete, name='template_delete'),
    
    # API
    path('api/tournament/<int:tournament_id>/timer/start/', api.start_timer, name='api_start_timer'),
    path('api/tournament/<int:tournament_id>/timer/pause/', api.pause_timer, name='api_pause_timer'),
    path('api/tournament/<int:tournament_id>/level/next/', api.next_level, name='api_next_level'),
    path('api/tournament/<int:tournament_id>/level/prev/', api.prev_level, name='api_prev_level'),
    path('api/tournament/<int:tournament_id>/break/start/', api.start_break, name='api_start_break'),
    path('api/tournament/<int:tournament_id>/timer/set/', api.set_timer, name='api_set_timer'),
    path('api/tournament/<int:tournament_id>/finish/', api.finish_tournament, name='api_finish_tournament'),
    path('api/tournament/<int:tournament_id>/status/', api.get_status, name='api_get_status'),
    
    # Player API
    path('api/tournament/<int:tournament_id>/players/', api.get_players, name='api_get_players'),
    path('api/tournament/<int:tournament_id>/register/', api.register_player, name='api_register_player'),
    path('api/tournament/<int:tournament_id>/eliminate/', api.eliminate_player, name='api_eliminate_player'),
    path('api/tournament/<int:tournament_id>/rebuy/', api.rebuy_player, name='api_rebuy_player'),
    path('api/tournament/<int:tournament_id>/addon/', api.addon_player, name='api_addon_player'),
    path('api/tournament/<int:tournament_id>/unregister/', api.unregister_player, name='api_unregister_player'),
    path('api/players/search/', api.search_players, name='api_search_players'),
    
    # Table API
    path('api/tournament/<int:tournament_id>/tables/generate/', api.generate_tables, name='api_generate_tables'),
    path('api/tournament/<int:tournament_id>/tables/', api.get_tables, name='api_get_tables'),
    path('api/tournament/<int:tournament_id>/tables/clear/', api.clear_tables, name='api_clear_tables'),
    path('api/tournament/<int:tournament_id>/tables/add/', api.add_table, name='api_add_table'),
    path('api/tournament/<int:tournament_id>/tables/<int:table_id>/delete/', api.delete_table, name='api_delete_table'),
    path('api/tournament/<int:tournament_id>/tables/seat-selected/', api.seat_selected_players, name='api_seat_selected_players'),
    path('api/tournament/<int:tournament_id>/tables/move/', api.move_player, name='api_move_player'),

    # Blind Structure API
    path('api/tournament/<int:tournament_id>/levels/', api.get_levels, name='api_get_levels'),
    path('api/tournament/<int:tournament_id>/level/add/', api.add_level, name='api_add_level'),
    path('api/tournament/<int:tournament_id>/level/<int:level_id>/update/', api.update_level, name='api_update_level'),
    path('api/tournament/<int:tournament_id>/level/<int:level_id>/delete/', api.delete_level, name='api_delete_level'),

    # Payout API
    path('api/tournament/<int:tournament_id>/payouts/', api.get_payouts, name='api_get_payouts'),
    path('api/tournament/<int:tournament_id>/payouts/generate/', api.generate_payouts, name='api_generate_payouts'),
    path('api/tournament/<int:tournament_id>/payouts/add/', api.add_payout, name='api_add_payout'),
    path('api/tournament/<int:tournament_id>/payouts/<int:payout_id>/update/', api.update_payout, name='api_update_payout'),
    path('api/tournament/<int:tournament_id>/payouts/<int:payout_id>/delete/', api.delete_payout, name='api_delete_payout'),

    # Statistics API
    path('api/stats/paid/results/', api.paid_tournament_results, name='api_paid_tournament_results'),
    path('api/stats/paid/payouts/', api.paid_payout_leaders, name='api_paid_payout_leaders'),
    path('api/stats/paid/rebuys/', api.paid_rebuy_leaders, name='api_paid_rebuy_leaders'),
    path('api/stats/free/results/', api.free_tournament_results, name='api_free_tournament_results'),
    path('api/stats/free/bounties/', api.free_bounty_leaders, name='api_free_bounty_leaders'),
    path('api/stats/tournament-years/', api.get_tournament_years, name='api_get_tournament_years'),

    # Bot
    path('bot/', include('bot.urls')),
]

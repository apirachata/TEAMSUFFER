from django.urls import path
from . import views

urlpatterns = [
    # Tournament CRUD
    path('tournaments/', views.TournamentListCreateAPIView.as_view(), name='tournament-list-create'),
    path('tournaments/<int:pk>/', views.TournamentRetrieveUpdateDestroyAPIView.as_view(), name='tournament-detail'),

    # Tournament Registration
    path('tournament-registrations/', views.TournamentRegistrationListCreateAPIView.as_view(),
         name='tournament-registration-list-create'),
    path('tournament-registrations/<int:pk>/', views.TournamentRegistrationRetrieveUpdateDestroyAPIView.as_view(),
         name='tournament-registration-detail'),

    # Matches
    path('matches/', views.MatchListCreateAPIView.as_view(), name='match-list-create'),
    path('matches/<int:pk>/', views.MatchRetrieveUpdateDestroyAPIView.as_view(), name='match-detail'),

    # Match Results
    path('match-results/', views.MatchResultListCreateAPIView.as_view(), name='match-result-list-create'),
    path('match-results/<int:pk>/', views.MatchResultRetrieveUpdateDestroyAPIView.as_view(),
         name='match-result-detail'),

     # Frontend tournament detail + registration flows
     path('tournaments/<int:pk>/detail/', views.tournament_detail_view, name='tournament_detail_frontend'),
     path('tournaments/<int:pk>/bracket/', views.tournament_bracket_view, name='tournament_bracket'),
     path('tournaments/<int:pk>/start/', views.start_tournament_view, name='tournament_start'),
     path('tournaments/<int:pk>/standings/', views.tournament_standings_view, name='tournament_standings'),
     path('tournaments/<int:pk>/register/create-team/', views.create_team_and_register, name='tournament_create_team_register'),
     path('tournaments/<int:pk>/join-team/', views.tournament_join_team_view, name='tournament_join_team'),
     path('tournaments/<int:pk>/manage/', views.manage_matches_view, name='manage_matches'),
     path('tournaments/brackets/', views.tournament_list_bracket_view, name='tournament_list_bracket'),
     path('tournaments/random-teams/', views.random_team_generator_view, name='random_team_generator'),
]

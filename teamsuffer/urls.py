"""
URL configuration for teamsuffer project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views
from tournaments import views as tournaments_views
from teams import views as teams_views

urlpatterns = [
    path('', views.home, name='home'),
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),

    path('api/', include('accounts.urls')),
    path('api/teams/', include('teams.urls')),
    path('api/', include('tournaments.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Frontend tournament routes
urlpatterns += [
    path('tournaments/', tournaments_views.tournament_list_bracket_view, name='tournament_list'),
    path('tournaments/<int:pk>/detail/', tournaments_views.tournament_detail_view, name='tournament_detail'),
    path('tournaments/<int:pk>/register/create-team/', tournaments_views.create_team_and_register, name='tournament_create_team_register'),
    path('tournaments/create/', tournaments_views.create_tournament_view, name='create_tournament'),
    path('tournaments/<int:pk>/start/', tournaments_views.start_tournament_view, name='tournament_start'),
    path('tournaments/<int:pk>/bracket/', tournaments_views.tournament_bracket_view, name='tournament_bracket'),
    path('tournaments/<int:pk>/standings/', tournaments_views.tournament_standings_view, name='tournament_standings'),
    path('tournaments/<int:pk>/manage/', tournaments_views.manage_matches_view, name='manage_matches'),
    path('tournaments/<int:pk>/delete/', tournaments_views.delete_tournament_view, name='tournament_delete'),
    path('tournaments/<int:pk>/registrations/<int:reg_id>/approve/', tournaments_views.approve_registration_view, name='approve_registration'),
    path('tournaments/<int:pk>/registrations/<int:reg_id>/reject/', tournaments_views.reject_registration_view, name='reject_registration'),
]

# Frontend teams list and actions
urlpatterns += [
    path('teams/', teams_views.teams_frontend_list, name='teams_frontend'),
    path('teams/<int:pk>/', teams_views.team_detail_view, name='team_detail'),
    path('teams/<int:pk>/approve/', teams_views.approve_team_view, name='approve_team'),
    path('teams/<int:pk>/reject/', teams_views.reject_team_view, name='reject_team'),
    path('teams/<int:pk>/delete/', teams_views.delete_team_view, name='delete_team'),
    path('teams/leave/', teams_views.leave_team_view, name='leave_team'),
    path('teams/<int:pk>/disband/', teams_views.disband_team_view, name='disband_team'),
]


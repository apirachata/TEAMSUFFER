from django.urls import path
from . import views

urlpatterns = [
    path('teams/', views.TeamListCreateAPIView.as_view(), name='team-list-create'),
    path('teams/<int:pk>/', views.TeamRetrieveUpdateDestroyAPIView.as_view(), name='team-detail'),

    # frontend list
    path('frontend/', views.teams_frontend_list, name='teams_frontend'),

    path('team-members/', views.TeamMemberListCreateAPIView.as_view(), name='team-member-list-create'),
    path('team-members/<int:pk>/', views.TeamMemberRetrieveUpdateDestroyAPIView.as_view(), name='team-member-detail'),
    path('team-members/<int:pk>/remove/', views.remove_team_member_view, name='remove_team_member'),
]

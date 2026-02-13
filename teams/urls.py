from django.urls import path
from . import views

urlpatterns = [
    path('teams/', views.TeamListCreateAPIView.as_view(), name='team-list-create'),
    path('teams/<int:pk>/', views.TeamRetrieveUpdateDestroyAPIView.as_view(), name='team-detail'),

    # frontend list
    path('frontend/', views.teams_frontend_list, name='teams_frontend'),
    path('frontend/<int:pk>/', views.team_detail_view, name='team_detail'),

    path('team-members/', views.TeamMemberListCreateAPIView.as_view(), name='team-member-list-create'),
    path('team-members/<int:pk>/', views.TeamMemberRetrieveUpdateDestroyAPIView.as_view(), name='team-member-detail'),
    path('team-members/<int:pk>/remove/', views.remove_team_member_view, name='remove_team_member'),
    
    # Admin actions
    path('teams/<int:pk>/delete/', views.delete_team_view, name='delete_team'),
    path('teams/<int:pk>/approve/', views.approve_team_view, name='approve_team'),
    path('teams/<int:pk>/reject/', views.reject_team_view, name='reject_team'),
    path('teams/<int:pk>/upload-logo/', views.upload_team_logo_view, name='upload_team_logo'),
]

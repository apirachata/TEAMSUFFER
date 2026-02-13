from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth.models import User

from .serializers import UserSerializer, RegisterSerializer
from .models import UserProfile
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import UserForm, ProfileForm
from teams.models import TeamMember


class RegisterAPIView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class MeAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


class UserListAPIView(generics.ListAPIView):
    """
    ดูรายชื่อผู้ใช้ทั้งหมด + role (เฉพาะ admin)
    """
    queryset = User.objects.all().order_by('id')
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]


class UserRoleUpdateAPIView(APIView):
    """
    เปลี่ยน role ของ user (เฉพาะ admin)
    """
    permission_classes = [permissions.IsAdminUser]

    def patch(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({'detail': 'User not found.'}, status=404)

        role = request.data.get('role')

        valid_roles = [choice[0] for choice in UserProfile.ROLE_CHOICES]
        if role not in valid_roles:
            return Response({'detail': f'Invalid role. Must be one of {valid_roles}'}, status=400)

        profile = user.profile  # thanks to OneToOne
        profile.role = role
        profile.save()

        return Response({'detail': f'Role of {user.username} updated to {role}.'})


@login_required
def profile_view(request):
    user = request.user
    profile, _ = UserProfile.objects.get_or_create(user=user)

    if request.method == 'POST':
        # If an avatar file was uploaded, save it immediately so the image persists
        # even if other form fields are missing or invalid.
        if request.FILES.get('avatar'):
            avatar_file = request.FILES.get('avatar')
            profile.avatar = avatar_file
            try:
                profile.save()
                messages.success(request, 'Avatar uploaded successfully.')
            except Exception as e:
                messages.error(request, f'Failed to save avatar: {e}')

        uform = UserForm(request.POST, instance=user)
        pform = ProfileForm(request.POST, request.FILES, instance=profile)
        if uform.is_valid() and pform.is_valid():
            uform.save()
            pform.save()
            return redirect('account_profile')
        else:
            # surface form errors so template can show them for debugging
            if not uform.is_valid():
                messages.error(request, f"User form errors: {uform.errors.as_json()}")
            if not pform.is_valid():
                messages.error(request, f"Profile form errors: {pform.errors.as_json()}")
    else:
        uform = UserForm(instance=user)
        pform = ProfileForm(instance=profile)


    # Get team info
    user_team_member = TeamMember.objects.filter(user=user).first()
    team = None
    members = []
    team_standings = None
    all_standings = []
    if user_team_member:
        team = user_team_member.team
        members = TeamMember.objects.filter(team=team).select_related('user', 'user__profile')
        
        # Get team's tournament registration and standings
        # Get team's tournament registration and standings using service
        from tournaments.models import TournamentRegistration
        from tournaments.services import list_standings
        
        registration = TournamentRegistration.objects.filter(team=team).select_related('tournament').order_by('-registered_at').first()
        if registration:
            # Use the common service to calculate everything correctly (including manual overrides)
            standings_data = list_standings(registration.tournament, include_pending=True)
            
            # Find my team in the results
            for s in standings_data:
                if s['team'].id == team.id:
                    team_standings = {
                        'tournament_name': registration.tournament.name,
                        'tournament_id': registration.tournament.id,
                        'status': registration.status,
                        'played': s['played'],
                        'won': s['won'],
                        'lost': s['lost'],
                        'score': s['score'],
                        'points': s['points'],
                    }
                    break
            
            # Use the same data for the leaderboard list
            all_standings = []
            for s in standings_data:
                all_standings.append({
                    'rank': s['rank'],
                    'team_name': s['team'].name,
                    'is_my_team': s['team'].id == team.id,
                    'played': s['played'],
                    'won': s['won'],
                    'lost': s['lost'],
                    'score': s['score'],
                    'points': s['points'],
                })

    return render(request, 'account/profile.html', {
        'user_form': uform, 
        'profile_form': pform,
        'team': team,
        'members': members,
        'user_team_member': user_team_member,
        'team_standings': team_standings,
        'all_standings': all_standings
    })

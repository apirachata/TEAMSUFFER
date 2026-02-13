from rest_framework import generics, permissions
from .models import Team, TeamMember
from tournaments.models import Game
from .serializers import TeamSerializer, TeamMemberSerializer
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count


class TeamListCreateAPIView(generics.ListCreateAPIView):
    queryset = Team.objects.all().order_by('-created_at')
    serializer_class = TeamSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        # เวลา POST สร้างทีม → ผูกคนสร้างกับ request.user
        serializer.save(created_by=self.request.user)


class TeamRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Team.objects.all()
    serializer_class = TeamSerializer
    permission_classes = [permissions.IsAuthenticated]


class TeamMemberListCreateAPIView(generics.ListCreateAPIView):
    queryset = TeamMember.objects.all()
    serializer_class = TeamMemberSerializer
    permission_classes = [permissions.IsAuthenticated]


class TeamMemberRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = TeamMember.objects.all()
    serializer_class = TeamMemberSerializer
    permission_classes = [permissions.IsAuthenticated]


@login_required
def teams_frontend_list(request):
    """Frontend: list teams and allow joining directly (login required)."""
    teams = Team.objects.filter(status='active').annotate(member_count=Count('members')).order_by('-created_at')

    if request.method == 'POST':
        if not request.user.is_authenticated:
            messages.error(request, 'กรุณาเข้าสู่ระบบก่อนเข้าร่วมทีม')
            return redirect('account_login')

        team_id = request.POST.get('team_id')
        team = get_object_or_404(Team, pk=team_id)

        # Check if user is already in ANY team
        existing_membership = TeamMember.objects.filter(user=request.user).first()
        if existing_membership:
            messages.error(request, f'คุณอยู่ในทีม "{existing_membership.team.name}" อยู่แล้ว ไม่สามารถเข้าร่วมทีมอื่นได้')
            return redirect('teams_frontend')

        # prevent duplicate membership in same team
        if TeamMember.objects.filter(team=team, user=request.user).exists():
            messages.info(request, 'คุณเป็นสมาชิกทีมนี้อยู่แล้ว')
            return redirect('teams_frontend')

        # Check if team is full
        member_count = TeamMember.objects.filter(team=team).count()
        if member_count >= 6:
            messages.error(request, 'ทีมนี้เต็มแล้ว')
            return redirect('teams_frontend')

        TeamMember.objects.create(team=team, user=request.user, role_in_team='member', status='accepted')
        messages.success(request, f'คุณเข้าร่วมทีม {team.name} เรียบร้อยแล้ว')
        return redirect('teams_frontend')

    # distinct games for filter
    games = Game.objects.filter(teams__in=teams).distinct()
    
    # Get tournaments for filter
    from tournaments.models import Tournament, TournamentRegistration
    tournaments = Tournament.objects.filter(status__in=['open', 'ongoing']).order_by('-start_date')
    
    # Add tournament info to each team
    team_tournament_map = {}
    for reg in TournamentRegistration.objects.select_related('team', 'tournament').filter(team__in=teams):
        team_tournament_map[reg.team_id] = reg.tournament.name
    
    for team in teams:
        team.tournament_name = team_tournament_map.get(team.id, '')

    return render(request, 'teams/list.html', {'teams': teams, 'games': games, 'tournaments': tournaments})


@login_required
def remove_team_member_view(request, pk):
    """Allow team leader to remove a member (kick)."""
    member = get_object_or_404(TeamMember, pk=pk)
    team = member.team

    # Check if request.user is the leader of this team
    # Find the membership of the request.user in this team
    is_leader = TeamMember.objects.filter(team=team, user=request.user, role_in_team='leader').exists()

    if not is_leader:
        messages.error(request, 'คุณไม่ใช่หัวหน้าทีมนี้')
        return redirect('account_profile')

    # Prevent removing self (Leader cannot kick self, must disband or transfer - for now just prevent)
    if member.user == request.user:
        messages.error(request, 'ไม่สามารถลบตัวเองได้')
        return redirect('account_profile')

    # Perform deletion
    target_name = member.user.username
    member.delete()
    messages.success(request, f'ลบสมาชิก {target_name} เรียบร้อยแล้ว')
    return redirect('account_profile')


@login_required
def delete_team_view(request, pk):
    """Admin only: Delete a team."""
    if not request.user.is_superuser:
        messages.error(request, 'คุณไม่มีสิทธิ์ในการลบทีม')
        return redirect('teams_frontend')

    team = get_object_or_404(Team, pk=pk)
    team_name = team.name
    team.delete() # Hard delete
    messages.success(request, f'ลบทีม {team_name} เรียบร้อยแล้ว')
    return redirect('teams_frontend')


@login_required
def approve_team_view(request, pk):
    """Admin only: Approve a team's tournament registration."""
    from tournaments.models import TournamentRegistration
    from django.utils import timezone
    
    if not request.user.is_superuser:
        messages.error(request, 'คุณไม่มีสิทธิ์ในการอนุมัติทีม')
        return redirect('teams_frontend')

    # Find the team's pending registration
    team = get_object_or_404(Team, pk=pk)
    registration = TournamentRegistration.objects.filter(team=team, status='pending').first()
    
    if registration:
        registration.status = 'approved'
        registration.approved_by = request.user
        registration.approved_at = timezone.now()
        registration.save()
        messages.success(request, f'อนุมัติทีม {team.name} เรียบร้อยแล้ว')
    else:
        messages.info(request, f'ไม่พบการลงทะเบียนที่รอการอนุมัติสำหรับทีม {team.name}')
    
    return redirect('teams_frontend')


@login_required
def reject_team_view(request, pk):
    """Admin only: Reject a team's tournament registration."""
    from tournaments.models import TournamentRegistration
    
    if not request.user.is_superuser:
        messages.error(request, 'คุณไม่มีสิทธิ์ในการปฏิเสธทีม')
        return redirect('teams_frontend')

    team = get_object_or_404(Team, pk=pk)
    registration = TournamentRegistration.objects.filter(team=team, status='pending').first()
    
    if registration:
        registration.status = 'rejected'
        registration.save()
        messages.success(request, f'ปฏิเสธทีม {team.name} เรียบร้อยแล้ว')
    else:
        messages.info(request, f'ไม่พบการลงทะเบียนที่รอการอนุมัติสำหรับทีม {team.name}')
    
    return redirect('teams_frontend')


@login_required
def upload_team_logo_view(request, pk):
    """Team leader: Upload team logo."""
    team = get_object_or_404(Team, pk=pk)
    
    # Check if request.user is the team creator
    if team.created_by != request.user:
        messages.error(request, 'คุณไม่ใช่หัวหน้าทีมนี้')
        return redirect('account_profile')
    
    if request.method == 'POST' and request.FILES.get('team_logo'):
        team.logo = request.FILES['team_logo']
        team.save()
        messages.success(request, f'อัปโหลดโลโก้ทีม {team.name} เรียบร้อยแล้ว')
    else:
        messages.error(request, 'กรุณาเลือกไฟล์รูปภาพ')
    
    return redirect('account_profile')


@login_required
def team_detail_view(request, pk):
    """Frontend: Detail view for a specific team."""
    team = get_object_or_404(Team, pk=pk)
    
    # Check if current user is a member
    is_member = team.members.filter(user=request.user).exists()
    
    # Calculate empty slots for rendering placeholders
    current_count = team.members.count()
    empty_slots = max(0, 6 - current_count)
    empty_slots_range = range(empty_slots) 

    # Get active tournament registration
    from tournaments.models import TournamentRegistration
    registration = TournamentRegistration.objects.select_related('tournament').filter(
        team=team, 
        tournament__status__in=['open', 'ongoing']
    ).first()
    
    current_tournament = registration.tournament if registration else None

    return render(request, 'teams/detail.html', {
        'team': team,
        'is_member': is_member,
        'empty_slots_range': empty_slots_range,
        'current_tournament': current_tournament
    })

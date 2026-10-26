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


def is_admin_user(user):
    """Check if a user has admin privileges (superuser, staff, or tournament_admin role)."""
    if not user.is_authenticated:
        return False
    if user.is_superuser or user.is_staff:
        return True
    if hasattr(user, 'profile') and user.profile.role == 'tournament_admin':
        return True
    return False


def teams_frontend_list(request):
    """Frontend: list teams (public) and allow joining directly (login required for POST)."""
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
    
    # Add tournament and registration status info to each team
    team_reg_map = {}
    for reg in TournamentRegistration.objects.select_related('team', 'tournament').filter(team__in=teams).order_by('-registered_at'):
        if reg.team_id not in team_reg_map:
            team_reg_map[reg.team_id] = reg
    
    for team in teams:
        reg = team_reg_map.get(team.id)
        team.tournament_name = reg.tournament.name if reg else ''
        team.registration_status = reg.status if reg else ''
        team.registration_id = reg.id if reg else None

    is_admin = is_admin_user(request.user)

    return render(request, 'teams/list.html', {
        'teams': teams, 
        'games': games, 
        'tournaments': tournaments,
        'is_admin': is_admin
    })


@login_required
def remove_team_member_view(request, pk):
    """Allow team leader to remove a member (kick)."""
    member = get_object_or_404(TeamMember, pk=pk)
    team = member.team

    # Check if request.user is the leader of this team or admin
    is_leader = TeamMember.objects.filter(team=team, user=request.user, role_in_team='leader').exists()

    if not is_leader and not is_admin_user(request.user):
        messages.error(request, 'คุณไม่ใช่หัวหน้าทีมนี้')
        return redirect('account_profile')

    # Prevent removing self (Leader cannot kick self, must disband or transfer)
    if member.user == request.user:
        messages.error(request, 'ไม่สามารถลบตัวเองได้ กรุณาใช้ปุ่มยุบทีม')
        return redirect('account_profile')

    # Perform deletion
    target_name = member.user.username
    member.delete()
    messages.success(request, f'ลบสมาชิก {target_name} เรียบร้อยแล้ว')
    return redirect('account_profile')


@login_required
def leave_team_view(request):
    """Allow a regular member to leave their current team."""
    membership = TeamMember.objects.filter(user=request.user).first()
    if not membership:
        messages.error(request, 'คุณไม่ได้อยู่ในทีมใด')
        return redirect('account_profile')

    if membership.role_in_team == 'leader':
        messages.error(request, 'หัวหน้าทีมไม่สามารถออกจากทีมได้ กรุณายุบทีมแทน')
        return redirect('account_profile')

    team_name = membership.team.name
    membership.delete()
    messages.success(request, f'คุณออกจากทีม {team_name} เรียบร้อยแล้ว')
    return redirect('account_profile')


@login_required
def disband_team_view(request, pk):
    """Allow team leader (or admin) to disband the team."""
    team = get_object_or_404(Team, pk=pk)
    if team.created_by != request.user and not is_admin_user(request.user):
        messages.error(request, 'คุณไม่มีสิทธิ์ในการยุบทีมนี้')
        return redirect('account_profile')

    team_name = team.name
    team.delete()
    messages.success(request, f'ยุบทีม {team_name} เรียบร้อยแล้ว')
    return redirect('account_profile')


@login_required
def delete_team_view(request, pk):
    """Admin only: Delete a team."""
    if not is_admin_user(request.user):
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
    
    team = get_object_or_404(Team, pk=pk)
    
    # Find pending or rejected registration to approve
    registration = TournamentRegistration.objects.filter(team=team, status__in=['pending', 'rejected']).order_by('-registered_at').first()
    
    if not registration:
        # Check if already approved
        already_approved = TournamentRegistration.objects.filter(team=team, status='approved').first()
        if already_approved:
            messages.info(request, f'ทีม {team.name} ได้รับการอนุมัติอยู่แล้ว')
        else:
            messages.info(request, f'ไม่พบการลงทะเบียนที่รอการอนุมัติสำหรับทีม {team.name}')
        referer = request.META.get('HTTP_REFERER')
        return redirect(referer if referer else 'teams_frontend')

    # Check permission: admin or tournament creator
    if not (is_admin_user(request.user) or request.user == registration.tournament.created_by):
        messages.error(request, 'คุณไม่มีสิทธิ์ในการอนุมัติทีม')
        return redirect('teams_frontend')

    registration.status = 'approved'
    registration.approved_by = request.user
    registration.approved_at = timezone.now()
    registration.save()
    messages.success(request, f'อนุมัติทีม {team.name} เข้าร่วมการแข่งขัน {registration.tournament.name} เรียบร้อยแล้ว')
    
    referer = request.META.get('HTTP_REFERER')
    return redirect(referer if referer else 'teams_frontend')


@login_required
def reject_team_view(request, pk):
    """Admin only: Reject a team's tournament registration."""
    from tournaments.models import TournamentRegistration
    
    team = get_object_or_404(Team, pk=pk)
    registration = TournamentRegistration.objects.filter(team=team, status__in=['pending', 'approved']).order_by('-registered_at').first()
    
    if not registration:
        messages.info(request, f'ไม่พบการลงทะเบียนสำหรับทีม {team.name}')
        referer = request.META.get('HTTP_REFERER')
        return redirect(referer if referer else 'teams_frontend')

    if not (is_admin_user(request.user) or request.user == registration.tournament.created_by):
        messages.error(request, 'คุณไม่มีสิทธิ์ในการปฏิเสธทีม')
        return redirect('teams_frontend')

    registration.status = 'rejected'
    registration.save()
    messages.warning(request, f'ปฏิเสธทีม {team.name} จากการแข่งขัน {registration.tournament.name} เรียบร้อยแล้ว')
    
    referer = request.META.get('HTTP_REFERER')
    return redirect(referer if referer else 'teams_frontend')


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

from rest_framework import generics, permissions
from .models import Team, TeamMember
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
    """Frontend: list teams and allow joining by code (login required)."""
    teams = Team.objects.filter(status='active').annotate(member_count=Count('members')).order_by('-created_at')

    if request.method == 'POST':
        if not request.user.is_authenticated:
            messages.error(request, 'กรุณาเข้าสู่ระบบก่อนเข้าร่วมทีม')
            return redirect('account_login')

        team_id = request.POST.get('team_id')
        code = request.POST.get('join_code', '').strip()

        team = get_object_or_404(Team, pk=team_id)

        # prevent duplicate membership
        if TeamMember.objects.filter(team=team, user=request.user).exists():
            messages.info(request, 'คุณเป็นสมาชิกทีมนี้อยู่แล้ว')
            return redirect('teams_frontend')

        if team.join_code:
            if not code or code != team.join_code:
                messages.error(request, 'รหัสทีมไม่ถูกต้อง')
                return redirect('teams_frontend')

        TeamMember.objects.create(team=team, user=request.user, role_in_team='member', status='accepted')
        messages.success(request, f'คุณเข้าร่วมทีม {team.name} เรียบร้อยแล้ว')
        return redirect('teams_frontend')

    return render(request, 'teams/list.html', {'teams': teams})


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

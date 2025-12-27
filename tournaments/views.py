from rest_framework import generics, permissions
from .models import Tournament, TournamentRegistration, Match, MatchResult
from .serializers import (
    TournamentSerializer,
    TournamentRegistrationSerializer,
    MatchSerializer,
    MatchResultSerializer,
)
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from teams.models import Team
from django.utils import timezone
from teams.models import TeamMember
from django.contrib import messages
from django.db.models import Count


class TournamentListCreateAPIView(generics.ListCreateAPIView):
    queryset = Tournament.objects.all().order_by('-created_at')
    serializer_class = TournamentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        # เวลา create ให้ผูกคนสร้างกับ user ที่ล็อกอินอยู่
        serializer.save(created_by=self.request.user)


class TournamentRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Tournament.objects.all()
    serializer_class = TournamentSerializer
    permission_classes = [permissions.IsAuthenticated]


class TournamentRegistrationListCreateAPIView(generics.ListCreateAPIView):
    queryset = TournamentRegistration.objects.all().order_by('-registered_at')
    serializer_class = TournamentRegistrationSerializer
    permission_classes = [permissions.IsAuthenticated]


class TournamentRegistrationRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = TournamentRegistration.objects.all()
    serializer_class = TournamentRegistrationSerializer
    permission_classes = [permissions.IsAuthenticated]


class MatchListCreateAPIView(generics.ListCreateAPIView):
    queryset = Match.objects.all().order_by('tournament', 'round_no', 'match_no')
    serializer_class = MatchSerializer
    permission_classes = [permissions.IsAuthenticated]


class MatchRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Match.objects.all()
    serializer_class = MatchSerializer
    permission_classes = [permissions.IsAuthenticated]


class MatchResultListCreateAPIView(generics.ListCreateAPIView):
    queryset = MatchResult.objects.all().order_by('-reported_at')
    serializer_class = MatchResultSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(reported_by=self.request.user)


class MatchResultRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = MatchResult.objects.all()
    serializer_class = MatchResultSerializer
    permission_classes = [permissions.IsAuthenticated]


@login_required
def tournament_register_view(request, pk):
    """Frontend registration page: show details and allow creating a team and registering it."""
    tournament = get_object_or_404(Tournament, pk=pk)

    if request.method == 'POST':
        team_name = request.POST.get('team_name')
        # optionally accept uploaded logo
        logo = request.FILES.get('team_logo')

        # create or reuse a team created by this user with same name
        team, created = Team.objects.get_or_create(name=team_name, created_by=request.user)

        # if a logo file was provided, save it to media and set logo_url
        if logo:
            # save file into media under teams/logos
            from django.core.files.storage import default_storage
            from django.core.files.base import ContentFile
            path = default_storage.save(f'teams/logos/{logo.name}', ContentFile(logo.read()))
            team.logo_url = default_storage.url(path)
            team.save()

        # create registration if not already registered
        existing = TournamentRegistration.objects.filter(tournament=tournament, team=team).first()
        if not existing:
            TournamentRegistration.objects.create(tournament=tournament, team=team, status='pending')

        # redirect to home (or you can create a tournament detail page)
        return redirect('home')

    return render(request, 'tournaments/register.html', {'tournament': tournament})


def tournament_detail_view(request, pk):
    """Show tournament rules and featured description with register button."""
    tournament = get_object_or_404(Tournament, pk=pk)
    return render(request, 'tournaments/detail.html', {'tournament': tournament})


@login_required
def create_team_and_register(request, pk):
    """Show a Create Team form; on submit create the team, make the user the leader, then register for tournament."""
    tournament = get_object_or_404(Tournament, pk=pk)

    if request.method == 'POST':
        team_name = request.POST.get('team_name')
        if not team_name:
            messages.error(request, 'กรุณากรอกชื่อทีม')
            return render(request, 'tournaments/create_team.html', {'tournament': tournament})

        # Create team and mark creator
        team = Team.objects.create(name=team_name, created_by=request.user)

        # create TeamMember record with leader role
        TeamMember.objects.create(team=team, user=request.user, role_in_team='leader', status='accepted')

        # create registration
        TournamentRegistration.objects.create(tournament=tournament, team=team, status='pending')

        messages.success(request, 'สร้างทีมและสมัครเรียบร้อยแล้ว')
        return redirect('home')

    return render(request, 'tournaments/create_team.html', {'tournament': tournament})


@login_required
def tournament_join_team_view(request, pk):
    """List teams registered for the tournament and allow logged-in player to join a team.

    Behavior:
      - Shows teams that have a TournamentRegistration for this tournament.
      - Allows user to enter a team join code (if team has one) to join immediately.
      - If team has no join_code, joining will be allowed immediately (accepted).
      - Prevents duplicate membership for the same user/team.
    """
    tournament = get_object_or_404(Tournament, pk=pk)

    # teams that are registered for this tournament
    regs = TournamentRegistration.objects.filter(tournament=tournament).select_related('team')
    team_ids = [r.team_id for r in regs]
    teams = Team.objects.filter(id__in=team_ids).annotate(member_count=Count('members')).prefetch_related('members__user')

    # handle join POST
    if request.method == 'POST':
        team_id = request.POST.get('team_id')
        code = request.POST.get('join_code', '').strip()

        if not team_id:
            messages.error(request, 'ทีมไม่ถูกต้อง')
            return redirect('tournament_join_team', pk=pk)

        team = get_object_or_404(Team, pk=team_id)

        # check already a member
        if TeamMember.objects.filter(team=team, user=request.user).exists():
            messages.info(request, 'คุณเป็นสมาชิกทีมนี้อยู่แล้ว')
            return redirect('tournament_join_team', pk=pk)

        # if team has join_code and it doesn't match -> deny
        if team.join_code:
            if not code or code != team.join_code:
                messages.error(request, 'รหัสทีมไม่ถูกต้อง')
                return redirect('tournament_join_team', pk=pk)

        # join: create TeamMember as accepted
        TeamMember.objects.create(team=team, user=request.user, role_in_team='member', status='accepted')
        messages.success(request, f'คุณเข้าร่วมทีม {team.name} เรียบร้อยแล้ว')
        return redirect('tournament_detail_frontend', pk=pk)

    return render(request, 'tournaments/join_team.html', {'tournament': tournament, 'teams': teams})



from .services import generate_bracket, list_standings

@login_required
def start_tournament_view(request, pk):
    """Generates the bracket/schedule and starts the tournament."""
    tournament = get_object_or_404(Tournament, pk=pk)
    
    # Check permission
    if request.user != tournament.created_by and not request.user.is_superuser:
        messages.error(request, "คุณไม่มีสิทธิ์เริ่มการแข่งขันนี้")
        return redirect('tournament_detail_frontend', pk=pk)
        
    success, msg = generate_bracket(tournament)
    if success:
        messages.success(request, f"สร้างตารางแข่งเรียบร้อยแล้ว: {msg}")
    else:
        messages.error(request, f"เกิดข้อผิดพลาด: {msg}")
        
    return redirect('tournament_bracket', pk=pk)


def tournament_bracket_view(request, pk):
    """Show tournament bracket/matches."""
    tournament = get_object_or_404(Tournament, pk=pk)
    
    # Matches grouped by round
    matches = Match.objects.filter(tournament=tournament).order_by('round_no', 'match_no').select_related('team1', 'team2', 'result')
    
    # Group by round for the template
    rounds_data = {}
    for m in matches:
        if m.round_no not in rounds_data:
            rounds_data[m.round_no] = []
        rounds_data[m.round_no].append(m)
        
    sorted_rounds = sorted(rounds_data.items()) # List of (round_no, [matches])
    
    # Check if we should show standings (Round Robin)
    show_standings = (tournament.bracket_type == 'round_robin')
    
    return render(request, 'tournaments/bracket.html', {
        'tournament': tournament, 
        'rounds': sorted_rounds, 
        'matches': matches,
        'show_standings': show_standings
    })


def tournament_standings_view(request, pk):
    """Show standings table for the tournament."""
    tournament = get_object_or_404(Tournament, pk=pk)
    standings = list_standings(tournament)
    return render(request, 'tournaments/standings.html', {'tournament': tournament, 'standings': standings})


@login_required
def manage_matches_view(request, pk):
    """Admin view to input scores for matches."""
    tournament = get_object_or_404(Tournament, pk=pk)
    
    # Check permission
    if request.user != tournament.created_by and not request.user.is_superuser:
        messages.error(request, "คุณไม่มีสิทธิ์จัดการผลการแข่งขันนี้")
        return redirect('tournament_detail_frontend', pk=pk)

    matches = Match.objects.filter(tournament=tournament).order_by('round_no', 'match_no').select_related('team1', 'team2', 'result')

    if request.method == 'POST':
        for match in matches:
            if not match.team1 or not match.team2:
                continue

            s1 = request.POST.get(f'score_{match.id}_team1')
            s2 = request.POST.get(f'score_{match.id}_team2')

            if s1 and s2:
                try:
                    score1 = int(s1)
                    score2 = int(s2)
                except ValueError:
                    continue 

                if score1 > score2:
                    winner = match.team1
                elif score2 > score1:
                    winner = match.team2
                else: 
                     # Draw logic: if model allows null winner, set None. 
                     # But model requires winner. For now let's skip draw or force team1.
                     # Better: Let's assume no draws for now as per simple tournament rules.
                     # If score equal, do nothing/skip.
                     continue

                result, created = MatchResult.objects.get_or_create(match=match, defaults={
                    'winner_team': winner,
                    'team1_score': score1,
                    'team2_score': score2,
                    'reported_by': request.user
                })
                
                if not created:
                    result.winner_team = winner
                    result.team1_score = score1
                    result.team2_score = score2
                    result.reported_by = request.user
                    result.save()
                    
                match.status = 'finished'
                match.save()
                
                # Advance winner to next bracket
                advance_winner(match)
                
        messages.success(request, "บันทึกผลการแข่งขันเรียบร้อยแล้ว")
        return redirect('manage_matches', pk=pk)

    return render(request, 'tournaments/manage_matches.html', {'tournament': tournament, 'matches': matches})



def tournament_list_bracket_view(request):
    """List all tournaments for users to choose which bracket to view."""
    tournaments = Tournament.objects.filter(status__in=['open', 'ongoing', 'closed', 'finished']).order_by('-created_at')
    return render(request, 'tournaments/tournament_list_bracket.html', {'tournaments': tournaments})


def random_team_generator_view(request):
    """Standalone tool for randomizing teams."""
    return render(request, 'tournaments/random_team_generator.html')



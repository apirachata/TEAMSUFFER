import random
import string
from rest_framework import generics, permissions
from .models import Tournament, TournamentRegistration, Match, MatchResult, Game
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
            messages.success(request, f'ส่งคำขอสมัครทีม {team.name} เรียบร้อยแล้ว รอผู้ดูแลอนุมัติ')
        else:
            messages.info(request, f'ทีม {team.name} ได้ลงทะเบียนรายการนี้ไว้แล้ว')

        # redirect to tournament detail page
        return redirect('tournament_detail', pk=pk)

    return render(request, 'tournaments/register.html', {'tournament': tournament})


def is_tournament_admin(user, tournament=None):
    """Check if user has admin privileges for tournaments (superuser, staff, tournament_admin role, or tournament creator)."""
    if not user.is_authenticated:
        return False
    if user.is_superuser or user.is_staff:
        return True
    if hasattr(user, 'profile') and user.profile.role == 'tournament_admin':
        return True
    if tournament and tournament.created_by_id == user.id:
        return True
    return False


def tournament_detail_view(request, pk):
    """Show tournament rules and featured description with register button and registered teams list."""
    tournament = get_object_or_404(Tournament, pk=pk)
    is_admin = is_tournament_admin(request.user, tournament)

    registrations = tournament.registrations.select_related('team', 'team__created_by').prefetch_related('team__members').order_by('-registered_at')
    approved_count = registrations.filter(status='approved').count()

    return render(request, 'tournaments/detail.html', {
        'tournament': tournament,
        'is_admin': is_admin,
        'registrations': registrations,
        'approved_count': approved_count
    })


@login_required
def approve_registration_view(request, pk, reg_id):
    """Admin only: Approve a specific team's registration for this tournament."""
    from django.utils import timezone
    tournament = get_object_or_404(Tournament, pk=pk)
    if not is_tournament_admin(request.user, tournament):
        messages.error(request, 'คุณไม่มีสิทธิ์ในการอนุมัติทีม')
        return redirect('tournament_detail', pk=pk)

    registration = get_object_or_404(TournamentRegistration, pk=reg_id, tournament=tournament)
    registration.status = 'approved'
    registration.approved_by = request.user
    registration.approved_at = timezone.now()
    registration.save()
    messages.success(request, f'อนุมัติทีม {registration.team.name} เรียบร้อยแล้ว')
    return redirect('tournament_detail', pk=pk)


@login_required
def reject_registration_view(request, pk, reg_id):
    """Admin only: Reject a specific team's registration for this tournament."""
    tournament = get_object_or_404(Tournament, pk=pk)
    if not is_tournament_admin(request.user, tournament):
        messages.error(request, 'คุณไม่มีสิทธิ์ในการปฏิเสธทีม')
        return redirect('tournament_detail', pk=pk)

    registration = get_object_or_404(TournamentRegistration, pk=reg_id, tournament=tournament)
    registration.status = 'rejected'
    registration.save()
    messages.warning(request, f'ปฏิเสธทีม {registration.team.name} เรียบร้อยแล้ว')
    return redirect('tournament_detail', pk=pk)


@login_required
def delete_tournament_view(request, pk):
    """Admin view to delete a completed tournament."""
    tournament = get_object_or_404(Tournament, pk=pk)
    
    # Check permission
    is_admin = is_tournament_admin(request.user, tournament)
        
    if not is_admin:
        messages.error(request, 'คุณไม่มีสิทธิ์ลบการแข่งขัน')
        return redirect('tournament_detail', pk=pk)
        
    if request.method == 'POST':
        tournament_name = tournament.name
        tournament.delete()
        messages.success(request, f'ลบการแข่งขัน "{tournament_name}" เรียบร้อยแล้ว')
        return redirect('home')
        
    # Using the detail view as a confirmation page or you can redirect
    # Normally we do this via POST from the detail page itself.
    return redirect('tournament_detail', pk=pk)


@login_required
def create_team_and_register(request, pk):
    """Show a Create Team form; on submit create the team, make the user the leader, then register for tournament."""
    tournament = get_object_or_404(Tournament, pk=pk)

    # Check if user is already in ANY team
    from teams.models import TeamMember
    existing_membership = TeamMember.objects.filter(user=request.user).select_related('team').first()
    if existing_membership:
        messages.error(request, f'คุณอยู่ในทีม "{existing_membership.team.name}" อยู่แล้ว กรุณาออกจากทีมก่อนจึงจะสมัครแข่งได้')
        return redirect('tournament_detail', pk=pk)

    # Check if user already has a team registered in this tournament
    existing_registration = TournamentRegistration.objects.filter(
        tournament=tournament,
        team__created_by=request.user
    ).exists()
    
    if existing_registration:
        messages.error(request, 'คุณได้สร้างทีมสำหรับรายการนี้แล้ว ไม่สามารถสร้างได้มากกว่า 1 ทีมต่อรายการ')
        return redirect('tournament_detail', pk=pk)

    if request.method == 'POST':
        team_name = request.POST.get('team_name')
        if not team_name:
            messages.error(request, 'กรุณากรอกชื่อทีม')
            return render(request, 'tournaments/create_team.html', {'tournament': tournament})

        # Create team and mark creator
        # Generate random 6-digit numeric code
        join_code = ''.join(random.choices(string.digits, k=6))
        
        team = Team.objects.create(name=team_name, created_by=request.user, join_code=join_code)

        # create TeamMember record with leader role
        TeamMember.objects.create(team=team, user=request.user, role_in_team='leader', status='accepted')

        # create registration as pending for admin approval
        TournamentRegistration.objects.create(tournament=tournament, team=team, status='pending')

        messages.success(request, 'สร้างทีมและส่งคำขอสมัครเรียบร้อยแล้ว รอผู้ดูแลอนุมัติการเข้าร่วม')
        return redirect('tournament_detail', pk=pk)

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
        return redirect('tournament_detail', pk=pk)

    # get unique games from these teams (to use in filter dropdown)
    # A team might not have a game assigned, so filter none if needed or handle in template
    games = Game.objects.filter(teams__in=teams).distinct()

    return render(request, 'tournaments/join_team.html', {'tournament': tournament, 'teams': teams, 'games': games})



from .services import generate_bracket, list_standings, advance_winner

@login_required
def start_tournament_view(request, pk):
    """Generates the bracket/schedule and starts the tournament."""
    tournament = get_object_or_404(Tournament, pk=pk)
    
    # Check permission
    if not is_tournament_admin(request.user, tournament):
        messages.error(request, "คุณไม่มีสิทธิ์เริ่มการแข่งขันนี้")
        return redirect('tournament_detail', pk=pk)
        
    success, msg = generate_bracket(tournament)
    if success:
        messages.success(request, f"สร้างตารางแข่งเรียบร้อยแล้ว: {msg}")
    else:
        messages.error(request, f"เกิดข้อผิดพลาด: {msg}")
        
    return redirect('tournament_bracket', pk=pk)


@login_required
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
    
    registrations = TournamentRegistration.objects.filter(tournament=tournament, status='approved').select_related('team')
    teams = [reg.team for reg in registrations]

    return render(request, 'tournaments/bracket.html', {
        'tournament': tournament, 
        'rounds': sorted_rounds, 
        'matches': matches,
        'show_standings': show_standings,
        'teams': teams
    })


def tournament_standings_view(request, pk):
    """
    Show standings table for the tournament.
    Admins can see pending teams and update scores inline.
    """
    tournament = get_object_or_404(Tournament, pk=pk)
    
    is_admin = request.user.is_authenticated and (request.user == tournament.created_by or request.user.is_superuser)
    
    if request.method == 'POST' and is_admin:
        # Inline save logic
        registrations = TournamentRegistration.objects.filter(tournament=tournament).select_related('team')
        
        for reg in registrations:
            p_val = request.POST.get(f'played_{reg.id}')
            w_val = request.POST.get(f'won_{reg.id}')
            l_val = request.POST.get(f'lost_{reg.id}')
            pts_val = request.POST.get(f'points_{reg.id}')
            score_val = request.POST.get(f'score_{reg.id}')
            team_name_val = request.POST.get(f'team_name_{reg.id}')
            
            # Helper to convert empty string to None
            def parse_int(val):
                if val and val.strip():
                    try:
                        return int(val)
                    except ValueError:
                        return None
                return None
            
            # Only update if at least one value is present in POST for this reg
            # (Check if the field exists in request.POST to distinguish from just empty)
            if f'played_{reg.id}' in request.POST:
                reg.manual_played = parse_int(p_val)
                reg.manual_won = parse_int(w_val)
                reg.manual_lost = parse_int(l_val)
                reg.manual_points = parse_int(pts_val)
                reg.manual_score = parse_int(score_val)
                reg.save()
            
            if team_name_val and team_name_val.strip() and team_name_val != reg.team.name:
                reg.team.name = team_name_val.strip()
                reg.team.save()
        
        messages.success(request, "บันทึกตารางคะแนนเรียบร้อยแล้ว")
        return redirect('tournament_standings', pk=pk)

    standings = list_standings(tournament, include_pending=True)
    
    return render(request, 'tournaments/standings.html', {
        'tournament': tournament, 
        'standings': standings,
        'is_admin': is_admin
    })


@login_required
def manage_matches_view(request, pk):
    """Admin view to input scores for matches."""
    tournament = get_object_or_404(Tournament, pk=pk)
    
    # Check permission
    if not is_tournament_admin(request.user, tournament):
        messages.error(request, "คุณไม่มีสิทธิ์จัดการผลการแข่งขันนี้")
        return redirect('tournament_detail', pk=pk)

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


@login_required
def create_tournament_view(request):
    """Admin view to create a new tournament."""
    # Check permission - only admin/staff/tournament_admin can create tournaments
    is_admin = request.user.is_superuser or request.user.is_staff
    if hasattr(request.user, 'profile'):
        is_admin = is_admin or request.user.profile.role == 'tournament_admin'
    
    if not is_admin:
        messages.error(request, 'คุณไม่มีสิทธิ์สร้างการแข่งขัน')
        return redirect('home')
    
    games = Game.objects.all().order_by('name')
    
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        game_id = request.POST.get('game_id')
        description = request.POST.get('description', '').strip()
        rules = request.POST.get('rules', '').strip()
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        max_teams = request.POST.get('max_teams', 16)
        prize_pool = request.POST.get('prize_pool', '').strip()
        status = request.POST.get('status', 'draft')
        bracket_type = request.POST.get('bracket_type', 'single')
        
        # Validation
        if not name:
            messages.error(request, 'กรุณากรอกชื่อการแข่งขัน')
            return render(request, 'tournaments/create_tournament.html', {'games': games})
        
        if not start_date or not end_date:
            messages.error(request, 'กรุณากรอกวันที่เริ่มและสิ้นสุด')
            return render(request, 'tournaments/create_tournament.html', {'games': games})
        
        try:
            max_teams = int(max_teams)
        except ValueError:
            max_teams = 16
        
        # Get game if selected
        game = None
        if game_id:
            try:
                game = Game.objects.get(pk=game_id)
            except Game.DoesNotExist:
                pass
        
        # Create tournament
        tournament = Tournament.objects.create(
            name=name,
            game=game,
            game_title=game.name if game else '',
            description=description,
            rules=rules,
            start_date=start_date,
            end_date=end_date,
            max_teams=max_teams,
            prize_pool=prize_pool,
            status=status,
            bracket_type=bracket_type,
            created_by=request.user
        )
        
        # Handle featured image upload
        if 'featured_image' in request.FILES:
            tournament.featured_image = request.FILES['featured_image']
            tournament.save()
        
        messages.success(request, f'สร้างการแข่งขัน "{tournament.name}" เรียบร้อยแล้ว')
        return redirect('home')
    
    return render(request, 'tournaments/create_tournament.html', {'games': games})


@login_required
def manage_standings_view(request, pk):
    """Admin view to manually override standings."""
    tournament = get_object_or_404(Tournament, pk=pk)
    
    # Check permission
    is_authorized = request.user == tournament.created_by or request.user.is_superuser
    if hasattr(request.user, 'profile') and request.user.profile.role == 'tournament_admin':
        is_authorized = True

    if not is_authorized:
        messages.error(request, "คุณไม่มีสิทธิ์จัดการตารางคะแนนนี้")
        return redirect('tournament_standings', pk=pk)

    registrations = TournamentRegistration.objects.filter(tournament=tournament, status='approved').select_related('team').order_by('team__name')

    if request.method == 'POST':
        for reg in registrations:
            p_val = request.POST.get(f'played_{reg.id}')
            w_val = request.POST.get(f'won_{reg.id}')
            l_val = request.POST.get(f'lost_{reg.id}')
            pts_val = request.POST.get(f'points_{reg.id}')
            score_val = request.POST.get(f'score_{reg.id}')
            
            # Helper to convert empty string to None
            def parse_int(val):
                if val and val.strip():
                    try:
                        return int(val)
                    except ValueError:
                        return None
                return None
            
            reg.manual_played = parse_int(p_val)
            reg.manual_won = parse_int(w_val)
            reg.manual_lost = parse_int(l_val)
            reg.manual_points = parse_int(pts_val)
            reg.manual_score = parse_int(score_val)
            reg.save()
            
        messages.success(request, "บันทึกตารางคะแนนเรียบร้อยแล้ว")
        return redirect('tournament_standings', pk=pk)

    return render(request, 'tournaments/manage_standings.html', {'tournament': tournament, 'registrations': registrations})



@login_required
def swap_teams_view(request, pk):
    """
    Swap two teams in the bracket.
    This works by swapping the Team objects assigned to match slots (team1 or team2).
    """
    tournament = get_object_or_404(Tournament, pk=pk)
    
    # Check permission
    if not is_tournament_admin(request.user, tournament):
        messages.error(request, "คุณไม่มีสิทธิ์จัดการการแข่งขันนี้")
        return redirect('tournament_bracket', pk=pk)

    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'random_all':
            from .services import generate_bracket
            success, msg = generate_bracket(tournament)
            if success:
                messages.success(request, f"สุ่มตารางการแข่งขันใหม่เรียบร้อยแล้ว")
            else:
                messages.error(request, f"เกิดข้อผิดพลาดในการสุ่มสาย: {msg}")
            return redirect('tournament_bracket', pk=pk)
            
        team1_id = request.POST.get('team1_id')
        team2_id = request.POST.get('team2_id')

        if not team1_id or not team2_id:
            messages.error(request, "กรุณาเลือกทีมที่ต้องการสลับทั้ง 2 ทีม")
            return redirect('tournament_bracket', pk=pk)
            
        if team1_id == team2_id:
             messages.error(request, "ไม่สามารถสลับทีมเดียวกันได้")
             return redirect('tournament_bracket', pk=pk)

        # Strategy:
        # We need to find *where* these teams are in the bracket (specifically round 1 or current matches?).
        # Ideally, swapping implies swapping their seed positions.
        # But if the tournament is ongoing, swapping might break things if they are in different rounds.
        # Strict mode: Only allow swapping if the tournament is NOT finished? 
        # Or just swap occurrences in *scheduled* matches?
        
        # Let's implementation: Swap all occurrences in Matches where status is 'scheduled'.
        # Actually safer: Swap occurrences in Round 1?
        # If bracket is generated, teams are assigned to R1 matches.
        # Let's find R1 matches involving these teams.
        
        from django.db.models import Q
        
        # Find matches for team 1
        matches_t1 = Match.objects.filter(
            tournament=tournament,
            status__in=['scheduled', 'ongoing']
        ).filter(Q(team1_id=team1_id) | Q(team2_id=team2_id)) # Get matches for BOTH teams
        
        # This is tricky because a team might be in multiple matches if they won?
        # But we usually swap BEFORE tournament starts or early on.
        # Simplest Logic: Swap the Team IDs in R1 matches only? 
        # If we swap seeds, we should swap R1 assignments.
        
        r1_matches = Match.objects.filter(tournament=tournament, round_no=1)
        
        swapped_count = 0
        
        # We need to fetch objects to modify
        for m in r1_matches:
            changed = False
            # Check Team 1 slot
            if m.team1_id == int(team1_id):
                m.team1_id = int(team2_id)
                changed = True
            elif m.team1_id == int(team2_id):
                m.team1_id = int(team1_id)
                changed = True
                
            # Check Team 2 slot
            if m.team2_id == int(team1_id):
                m.team2_id = int(team2_id)
                changed = True
            elif m.team2_id == int(team2_id):
                m.team2_id = int(team1_id)
                changed = True
            
            if changed:
                m.save()
                swapped_count += 1
                
        if swapped_count > 0:
            messages.success(request, f"สลับตำแหน่งทีมเรียบร้อยแล้ว ({swapped_count} แมตช์)")
        else:
            messages.warning(request, "ไม่พบแมตช์รอบแรกที่สามารถสลับทีมได้")
            
    return redirect('tournament_bracket', pk=pk)

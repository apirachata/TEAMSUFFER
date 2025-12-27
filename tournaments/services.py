import random
import math
from django.db import transaction
from .models import Match, MatchResult, TournamentRegistration

def generate_bracket(tournament):
    """
    Generate matches for a tournament based on its type.
    Randomizes (shuffles) the teams before pairing.
    """
    # 1. Get approved teams
    registrations = list(TournamentRegistration.objects.filter(
        tournament=tournament, 
        status='approved'
    ).select_related('team'))
    
    if len(registrations) < 2:
        return False, "Not enough teams to start tournament (need at least 2)"

    # RANDOMIZE TEAMS
    random.shuffle(registrations)
    teams = [r.team for r in registrations]
    
    # Delete existing matches if any (full reset)
    Match.objects.filter(tournament=tournament).delete()
    
    if tournament.bracket_type == 'round_robin':
        _generate_round_robin(tournament, teams)
    elif tournament.bracket_type == 'single':
        _generate_single_elimination(tournament, teams)
    # Double elimination can be added here
    
    # Update status
    tournament.status = 'ongoing'
    tournament.save()
    
    return True, "Bracket generated successfully"

def _generate_round_robin(tournament, teams):
    """
    Create matches for everyone vs everyone.
    """
    n = len(teams)
    # Using Circle Method for scheduling rounds
    if n % 2 != 0:
        teams.append(None) # Bye
        n += 1
        
    num_rounds = n - 1
    num_matches_per_round = n // 2
    
    rotation = list(teams)
    
    match_count = 1
    
    for round_num in range(1, num_rounds + 1):
        for i in range(num_matches_per_round):
            t1 = rotation[i]
            t2 = rotation[n - 1 - i]
            
            if t1 and t2: # If neither is a Bye
                Match.objects.create(
                    tournament=tournament,
                    round_no=round_num,
                    match_no=match_count,
                    team1=t1,
                    team2=t2,
                    scheduled_at=tournament.start_date
                )
                match_count += 1
                
        rotation = [rotation[0]] + [rotation[-1]] + rotation[1:-1]

def _generate_single_elimination(tournament, teams):
    """
    Create matches for single elimination bracket.
    Generates the full tree structure with TBD matches.
    """
    n = len(teams)
    # Find next power of 2
    power_of_2 = 1
    while power_of_2 < n:
        power_of_2 *= 2
        
    # Byes
    byes = power_of_2 - n
    
    # Seeding order logic to avoid top seeds meeting early
    def get_seeding_order(num_teams):
        """Returns list of seed indices for bracket"""
        rounds = int(math.log2(num_teams))
        seeds = [1, 2]
        for r in range(rounds - 1):
            next_seeds = []
            for s in seeds:
                next_seeds.append(s)
                next_seeds.append(2**(r+2) + 1 - s)
            seeds = next_seeds
        return [s-1 for s in seeds] # 0-indexed

    # Prepare slots: Teams + Byes
    # We use our random list as the 'Seed Order' (Seed 1 = teams[0])
    seeded_slots = list(teams)
    for _ in range(byes):
        seeded_slots.append(None)
        
    # Reorder slots based on standard bracket seeding
    seed_indices = get_seeding_order(power_of_2)
    ordered_teams = [seeded_slots[i] for i in seed_indices]
    
    # Create Matches Layer by Layer
    rounds = int(math.log2(power_of_2))
    
    # We need to track matches to link winners if we were robust, 
    # but strictly we just need correct Round/MatchNo.
    # Logic: Round R, Match M feeds:
    #   Round R+1, Match ceil(M/2).
    #   If M is odd -> Team 1 slot.
    #   If M is even -> Team 2 slot.
    
    # Use a list to track the 'Winner' reference for the next round
    # Initial level: The teams themselves
    next_round_participants = ordered_teams 
    
    match_global_counter = 1
    
    for r in range(1, rounds + 1):
        num_matches = len(next_round_participants) // 2
        current_round_participants = next_round_participants
        next_round_participants = [] # Will be filled with TBD or Winners
        
        for i in range(num_matches):
            t1 = current_round_participants[2*i]
            t2 = current_round_participants[2*i + 1]
            
            # Determine status
            # For Round 1:
            #   Team vs Team -> Scheduled
            #   Team vs Bye -> Team advances (Auto-win)
            #   Bye vs Team -> Team advances
            #   Bye vs Bye -> Impossible with correct seeding
            
            # For Round > 1:
            #   If we come from a Bye match, we might have a team.
            #   Otherwise TBD.
            
            status = 'scheduled'
            winner_ref = None # Who moves to next round list?
            
            # Cases:
            # 1. Both are real teams -> Match created, Winner TBD
            if t1 and t2:
                # Check if they are actually Team objects (Round 1) 
                # or just placeholders? 
                # In R1 they are Team objects. In R2 they might be Team objects (from Bye) or None (TBD).
                pass
            elif t1 and not t2: # T2 is Bye or TBD?
                # In R1, None means Bye.
                # In R2+, None means "Winner of previous match not decided yet".
                if r == 1:
                    status = 'finished' # Auto win
                    winner_ref = t1
                pass
            elif t2 and not t1:
                if r == 1:
                    status = 'finished'
                    winner_ref = t2
                pass
            else: # Both None
                pass
                
            # If R > 1, inputs might be None (TBD).
            
            m = Match.objects.create(
                tournament=tournament,
                round_no=r,
                match_no=i + 1,
                team1=t1,
                team2=t2,
                status=status,
                scheduled_at=tournament.start_date
            )
            
            # If auto-win (Bye in R1), create result
            if status == 'finished' and winner_ref:
                MatchResult.objects.create(
                    match=m,
                    winner_team=winner_ref,
                    team1_score=0, 
                    team2_score=0,
                    reported_by=None
                )
                next_round_participants.append(winner_ref)
            else:
                next_round_participants.append(None) # TBD
                

def list_standings(tournament):
    """
    Calculate standings (won/lost/points).
    """
    from teams.models import Team
    teams = Team.objects.filter(tournament_entries__tournament=tournament, tournament_entries__status='approved')
    standings = {t.id: {'team': t, 'played': 0, 'won': 0, 'lost': 0, 'points': 0, 'gd': 0} for t in teams}
    
    results = MatchResult.objects.filter(match__tournament=tournament)
    
    for r in results:
        m = r.match
        
        # Determine loser
        if r.winner_team == m.team1:
            winner, loser = m.team1, m.team2
            w_score, l_score = r.team1_score, r.team2_score
        else:
            winner, loser = m.team2, m.team1
            w_score, l_score = r.team2_score, r.team1_score # Note: columns in MatchResult are fixed team1_score/team2_score
            
            # Wait, fields are team1_score and team2_score.
            # If Winner is Team 2, then Team 2 score is r.team2_score.
            w_score = r.team2_score
            l_score = r.team1_score

        if winner and winner.id in standings:
            s = standings[winner.id]
            s['played'] += 1
            s['won'] += 1
            s['points'] += 3
            s['gd'] += (w_score - l_score)
            
        if loser and loser.id in standings:
            s = standings[loser.id]
            s['played'] += 1
            s['lost'] += 1
            s['gd'] += (l_score - w_score)
            
    # Sort
    res = list(standings.values())
    res.sort(key=lambda x: (-x['points'], -x['gd'], -x['won']))
    
    for i, item in enumerate(res):
        item['rank'] = i + 1
        
    return res

def advance_winner(match):
    """
    When a match is finished, move the winner to the next round's bracket slot.
    Logic for Single Elimination:
    - Current: Round R, Match M
    - Next: Round R+1, Match ceil(M/2)
    - Slot: Team1 if M is odd, Team2 if M is even
    """
    if not match.result or not match.result.winner_team:
        return
        
    next_round = match.round_no + 1
    next_match_no = math.ceil(match.match_no / 2)
    
    # Try to find the next match
    try:
        next_match = Match.objects.get(
            tournament=match.tournament,
            round_no=next_round,
            match_no=next_match_no
        )
    except Match.DoesNotExist:
        # Might be the final, so no next match
        return

    # Determine slot
    if match.match_no % 2 != 0:
        # Odd -> Team 1
        next_match.team1 = match.result.winner_team
    else:
        # Even -> Team 2
        next_match.team2 = match.result.winner_team
        
    next_match.save()

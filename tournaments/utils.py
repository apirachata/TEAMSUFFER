import random
import math

from teams.models import Team
from .models import TournamentRegistration


def _team_list_for_tournament(tournament):
    # use approved registrations first; fall back to all registrations
    regs = TournamentRegistration.objects.filter(tournament=tournament, status='approved').select_related('team')
    if not regs.exists():
        regs = TournamentRegistration.objects.filter(tournament=tournament).select_related('team')
    teams = [r.team for r in regs]
    return teams


def generate_single_elimination(tournament):
    teams = _team_list_for_tournament(tournament)
    random.shuffle(teams)
    # next power of two
    n = len(teams)
    size = 1 << (n - 1).bit_length() if n > 0 else 0
    byes = size - n

    bracket = {
        'type': 'single',
        'size': size,
        'teams': [{'id': t.id, 'name': t.name} for t in teams],
        'rounds': []
    }

    # seed first round
    first_round = []
    it = iter(teams)
    while True:
        try:
            a = next(it)
        except StopIteration:
            break
        try:
            b = next(it)
        except StopIteration:
            b = None
        first_round.append({'team1': {'id': a.id, 'name': a.name}, 'team2': {'id': b.id, 'name': b.name} if b else None, 'winner': None})
    bracket['rounds'].append(first_round)

    # create placeholder subsequent rounds
    current_matches = len(first_round)
    while current_matches > 1:
        current_matches = math.ceil(current_matches / 2)
        round_matches = [{'team1': None, 'team2': None, 'winner': None} for _ in range(current_matches)]
        bracket['rounds'].append(round_matches)

    return bracket


def generate_round_robin(tournament):
    teams = _team_list_for_tournament(tournament)
    random.shuffle(teams)
    n = len(teams)
    matches = []
    for i in range(n):
        for j in range(i + 1, n):
            matches.append({'team1': {'id': teams[i].id, 'name': teams[i].name}, 'team2': {'id': teams[j].id, 'name': teams[j].name}, 'scheduled_at': None, 'result': None})
    bracket = {
        'type': 'round_robin',
        'teams': [{'id': t.id, 'name': t.name} for t in teams],
        'matches': matches
    }
    return bracket


def generate_mini_league(tournament, group_size=4):
    # split teams into groups and create round robin within groups
    teams = _team_list_for_tournament(tournament)
    random.shuffle(teams)
    groups = []
    for i in range(0, len(teams), group_size):
        group = teams[i:i + group_size]
        group_matches = []
        for a in range(len(group)):
            for b in range(a + 1, len(group)):
                group_matches.append({'team1': {'id': group[a].id, 'name': group[a].name}, 'team2': {'id': group[b].id, 'name': group[b].name}})
        groups.append({'teams': [{'id': t.id, 'name': t.name} for t in group], 'matches': group_matches})
    bracket = {
        'type': 'mini',
        'groups': groups
    }
    return bracket


def generate_double_elimination(tournament):
    # simplified double-elimination: generate winners bracket same as single, and create empty losers bracket placeholders
    teams = _team_list_for_tournament(tournament)
    random.shuffle(teams)
    n = len(teams)
    # build winners bracket (single-elim style)
    winners = generate_single_elimination(tournament)
    # build losers placeholders: same rounds as winners
    losers = []
    for rnd in winners['rounds']:
        losers.append([{'team1': None, 'team2': None, 'winner': None} for _ in range(len(rnd))])
    bracket = {
        'type': 'double',
        'teams': [{'id': t.id, 'name': t.name} for t in teams],
        'winners': winners,
        'losers': losers
    }
    return bracket

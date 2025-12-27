from rest_framework import serializers
from .models import Tournament, TournamentRegistration, Match, MatchResult
from teams.models import Team


class TournamentSerializer(serializers.ModelSerializer):
    created_by_username = serializers.ReadOnlyField(source='created_by.username')

    class Meta:
        model = Tournament
        fields = [
            'id',
            'name',
            'game_title',
            'description',
            'rules',
            'start_date',
            'end_date',
            'max_teams',
            'status',
            'created_by',
            'created_by_username',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_by', 'created_by_username', 'created_at', 'updated_at']


class TournamentRegistrationSerializer(serializers.ModelSerializer):
    tournament_name = serializers.ReadOnlyField(source='tournament.name')
    team_name = serializers.ReadOnlyField(source='team.name')

    class Meta:
        model = TournamentRegistration
        fields = [
            'id',
            'tournament',
            'tournament_name',
            'team',
            'team_name',
            'status',
            'registered_at',
            'approved_by',
            'approved_at',
        ]
        read_only_fields = ['registered_at', 'approved_by', 'approved_at']


class MatchSerializer(serializers.ModelSerializer):
    tournament_name = serializers.ReadOnlyField(source='tournament.name')
    team1_name = serializers.ReadOnlyField(source='team1.name')
    team2_name = serializers.ReadOnlyField(source='team2.name')

    class Meta:
        model = Match
        fields = [
            'id',
            'tournament',
            'tournament_name',
            'round_no',
            'match_no',
            'team1',
            'team1_name',
            'team2',
            'team2_name',
            'scheduled_at',
            'status',
        ]


class MatchResultSerializer(serializers.ModelSerializer):
    match_info = serializers.ReadOnlyField(source='match.id')
    winner_team_name = serializers.ReadOnlyField(source='winner_team.name')

    class Meta:
        model = MatchResult
        fields = [
            'id',
            'match',
            'match_info',
            'winner_team',
            'winner_team_name',
            'team1_score',
            'team2_score',
            'reported_by',
            'reported_at',
            'verified_by',
            'verified_at',
        ]
        read_only_fields = ['reported_by', 'reported_at', 'verified_by', 'verified_at']

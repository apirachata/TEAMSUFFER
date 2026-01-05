from django.contrib import admin

from .models import Tournament, TournamentRegistration, Match, MatchResult, Game
from django.utils.html import format_html
from django.urls import reverse
from django.contrib import admin


class MatchInline(admin.TabularInline):
	model = Match
	fields = ('round_no', 'match_no', 'team1', 'team2', 'scheduled_at', 'status')
	readonly_fields = ()
	extra = 0


class MatchResultInline(admin.StackedInline):
	model = MatchResult
	fields = ('winner_team', 'team1_score', 'team2_score', 'reported_by', 'verified_by', 'verified_at')
	extra = 0
	max_num = 1

@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(Tournament)
class TournamentAdmin(admin.ModelAdmin):
	list_display = ('name', 'game', 'game_title', 'status', 'start_date', 'max_teams', 'is_featured', 'view_standings', 'manage_matches_link')
	list_filter = ('status', 'game', 'game_title', 'is_featured')
	search_fields = ('name', 'game_title')
	readonly_fields = ('created_at', 'updated_at')
	inlines = [MatchInline]
	fieldsets = (
		(None, {'fields': ('name', 'game', 'game_title', 'description', 'rules', 'featured_description', 'featured_image', 'is_featured')}),
		('Schedule & Settings', {'fields': ('start_date', 'end_date', 'max_teams', 'prize_pool', 'status')}),
		('Bracket', {'fields': ('bracket_type', 'bracket')}),
		('Meta', {'fields': ('created_by', 'created_at', 'updated_at')}),
	)

	actions = ['generate_single_elimination_action', 'generate_double_elimination_action', 'generate_round_robin_action', 'generate_mini_league_action']

	def _generate_and_save(self, request, queryset, func, type_key):
		for tournament in queryset:
			bracket = func(tournament)
			# create Match objects for bracket where possible
			# remove existing matches for tournament to avoid duplicates
			Match.objects.filter(tournament=tournament).delete()
			# helper to create a Match and return id
			def _create_match(team1_id, team2_id, round_no, match_no):
				if not team1_id or not team2_id:
					return None
				try:
					team1 = Team.objects.get(pk=team1_id)
					team2 = Team.objects.get(pk=team2_id)
				except Team.DoesNotExist:
					return None
				m = Match.objects.create(
					tournament=tournament,
					round_no=round_no,
					match_no=match_no,
					team1=team1,
					team2=team2,
					scheduled_at=timezone.now(),
					status='scheduled'
				)
				return m.id

			# attach match ids into bracket structure
			if bracket.get('type') == 'single':
				for ri, rnd in enumerate(bracket.get('rounds', []), start=1):
					for mi, match in enumerate(rnd, start=1):
						# match.team1/team2 are dicts {id,name}
						t1 = match.get('team1') and match['team1'].get('id')
						t2 = match.get('team2') and match['team2'].get('id')
						mid = _create_match(t1, t2, ri, mi)
						if mid:
							match['match_id'] = mid

			elif bracket.get('type') == 'double':
				# winners bracket
				winners = bracket.get('winners', {}).get('rounds', [])
				for ri, rnd in enumerate(winners, start=1):
					for mi, match in enumerate(rnd, start=1):
						t1 = match.get('team1') and match['team1'].get('id')
						t2 = match.get('team2') and match['team2'].get('id')
						mid = _create_match(t1, t2, ri, mi)
						if mid:
							match['match_id'] = mid

			elif bracket.get('type') == 'round_robin':
				for mi, match in enumerate(bracket.get('matches', []), start=1):
					t1 = match.get('team1') and match['team1'].get('id')
					t2 = match.get('team2') and match['team2'].get('id')
					mid = _create_match(t1, t2, 1, mi)
					if mid:
						match['match_id'] = mid

			elif bracket.get('type') == 'mini':
				mi_idx = 1
				for gi, group in enumerate(bracket.get('groups', []), start=1):
					for match in group.get('matches', []):
						t1 = match.get('team1') and match['team1'].get('id')
						t2 = match.get('team2') and match['team2'].get('id')
						mid = _create_match(t1, t2, gi, mi_idx)
						if mid:
							match['match_id'] = mid
						mi_idx += 1

			# save bracket and metadata
			tournament.bracket = bracket
			tournament.bracket_type = type_key
			tournament.save()
			messages.success(request, f'Generated {type_key} bracket and created matches for "{tournament.name}"')

	def generate_single_elimination_action(self, request, queryset):
		self._generate_and_save(request, queryset, utils.generate_single_elimination, 'single')
	generate_single_elimination_action.short_description = 'Generate Single Elimination bracket'

	def generate_double_elimination_action(self, request, queryset):
		self._generate_and_save(request, queryset, utils.generate_double_elimination, 'double')
	generate_double_elimination_action.short_description = 'Generate Double Elimination bracket'

	def generate_round_robin_action(self, request, queryset):
		self._generate_and_save(request, queryset, utils.generate_round_robin, 'round_robin')
	generate_round_robin_action.short_description = 'Generate Round Robin bracket'

	def generate_mini_league_action(self, request, queryset):
		self._generate_and_save(request, queryset, utils.generate_mini_league, 'mini')
	generate_mini_league_action.short_description = 'Generate Mini League bracket'

	def view_standings(self, obj):
		url = reverse('tournament_standings', args=[obj.id])
		return format_html('<a class="button" href="{}" target="_blank">ดูตารางคะแนน</a>', url)

	view_standings.short_description = 'Standings'

	def manage_matches_link(self, obj):
		url = reverse('manage_matches', args=[obj.id])
		return format_html('<a class="button" href="{}" style="background-color: #ffd700; color: #000; font-weight: bold; padding: 5px 10px; border-radius: 4px; text-decoration: none;">บันทึกผล</a>', url)
	
	manage_matches_link.short_description = 'Score Entry'



@admin.register(TournamentRegistration)
class TournamentRegistrationAdmin(admin.ModelAdmin):
	list_display = ('tournament', 'team', 'status', 'manual_played', 'manual_won', 'manual_lost', 'manual_points', 'registered_at')
	list_filter = ('status', 'tournament')
	search_fields = ('team__name', 'tournament__name')
	list_editable = ('manual_played', 'manual_won', 'manual_lost', 'manual_points', 'status')
	fieldsets = (
		(None, {'fields': ('tournament', 'team', 'status')}),
		('Manual Overrides (Optional)', {'fields': ('manual_played', 'manual_won', 'manual_lost', 'manual_points')}),
		('Meta', {'fields': ('registered_at', 'approved_by', 'approved_at')}),
	)
	readonly_fields = ('registered_at',)


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
	list_display = ('tournament', 'round_no', 'match_no', 'team1', 'team2', 'status')
	list_filter = ('tournament', 'round_no', 'status')
	inlines = [MatchResultInline]


@admin.register(MatchResult)
class MatchResultAdmin(admin.ModelAdmin):
	list_display = ('match', 'winner_team', 'team1_score', 'team2_score', 'reported_by', 'reported_at')
	list_filter = ('reported_at', 'verified_by')

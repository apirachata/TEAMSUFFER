from django.conf import settings
from django.db import models
from teams.models import Team   # เอา Team ที่เราสร้างไว้มาใช้งาน



class Game(models.Model):
    name = models.CharField(max_length=100, unique=True)
    image = models.ImageField(upload_to='games/', blank=True, null=True)

    def __str__(self):
        return self.name


class Tournament(models.Model):
    name = models.CharField(max_length=200)   # ชื่อทัวร์นาเมนต์
    # Game link - deprecated game_title later
    game = models.ForeignKey(Game, on_delete=models.CASCADE, null=True, blank=True, related_name='tournaments')
    game_title = models.CharField(max_length=100, blank=True)  # Kept for backward compatibility momentarily
    description = models.TextField(blank=True)     # รายละเอียด
    rules = models.TextField(blank=True)           # กติกาการแข่งขัน

    start_date = models.DateTimeField()    # วันเริ่มแข่ง
    end_date = models.DateTimeField()      # วันจบแข่ง

    max_teams = models.IntegerField(default=16)    # จำนวนทีมที่รับได้
    prize_pool = models.CharField(max_length=100, blank=True, null=True)  # รางวัล เช่น "$100,000"
    # Featured banner for homepage (admin can set)
    is_featured = models.BooleanField(default=False)
    featured_image = models.ImageField(upload_to='tournaments/featured/', blank=True, null=True)
    featured_description = models.TextField(blank=True)

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('open', 'Open'),
        ('closed', 'Closed'),
        ('ongoing', 'Ongoing'),
        ('finished', 'Finished'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # ผู้สร้างทัวร์นาเมนต์
        on_delete=models.CASCADE
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Bracket storage: JSON structure generated from admin
    bracket = models.JSONField(blank=True, null=True)
    BRACKET_TYPE_CHOICES = [
        ('single', 'Single Elimination'),
        ('double', 'Double Elimination'),
        ('round_robin', 'Round Robin'),
        ('mini', 'Mini League'),
    ]
    bracket_type = models.CharField(max_length=30, choices=BRACKET_TYPE_CHOICES, blank=True, null=True)

    # Point System Configuration
    point_win = models.IntegerField(default=3, help_text="Points awarded for a win")
    point_draw = models.IntegerField(default=1, help_text="Points awarded for a draw")
    point_loss = models.IntegerField(default=0, help_text="Points awarded for a loss")

    def __str__(self):
        return self.name


class TournamentRegistration(models.Model):
    tournament = models.ForeignKey(
        Tournament,
        on_delete=models.CASCADE,
        related_name='registrations'
    )

    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name='tournament_entries'
    )

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled')
    ]

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    registered_at = models.DateTimeField(auto_now_add=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='approvals'
    )
    approved_at = models.DateTimeField(null=True, blank=True)

    # Manual Override for Standings (Optional)
    manual_played = models.IntegerField(null=True, blank=True)
    manual_won = models.IntegerField(null=True, blank=True)
    manual_lost = models.IntegerField(null=True, blank=True)
    manual_points = models.IntegerField(null=True, blank=True)
    manual_score = models.IntegerField(null=True, blank=True, help_text="Manual total Game Score/Kill Points")

    class Meta:
        unique_together = ('tournament', 'team')  # ป้องกันไม่ให้สมัครซ้ำ

    def __str__(self):
        return f"{self.team.name} -> {self.tournament.name}"


class Match(models.Model):
    tournament = models.ForeignKey(
        Tournament,
        on_delete=models.CASCADE,
        related_name='matches'
    )
    round_no = models.IntegerField()   # รอบที่เท่าไหร่ เช่น รอบแรก, รอบสอง
    match_no = models.IntegerField()   # ลำดับแมตช์ในรอบนั้น

    team1 = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name='matches_as_team1',
        null=True, blank=True
    )
    team2 = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name='matches_as_team2',
        null=True, blank=True
    )

    scheduled_at = models.DateTimeField()
    status = models.CharField(
        max_length=20,
        default='scheduled'
    )

    def __str__(self):
        return f"Match {self.match_no} (Round {self.round_no})"


class MatchResult(models.Model):
    match = models.OneToOneField(
        Match,
        on_delete=models.CASCADE,
        related_name='result'
    )

    winner_team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name='wins'
    )

    team1_score = models.IntegerField()
    team2_score = models.IntegerField()

    reported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='reported_results'
    )

    reported_at = models.DateTimeField(auto_now_add=True)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_results'
    )
    verified_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Result for Match {self.match.id}"

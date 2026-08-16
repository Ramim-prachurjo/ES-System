import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
from venues.models import Venue
from teams.models import Team


class Tournament(models.Model):

    STATUS_CHOICES = [
        ('pending',   'Pending Approval'),
        ('active',    'Active'),
        ('ongoing',   'Ongoing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    GAME_CHOICES = [
        ('valorant', 'Valorant'),
        ('pubg',     'PUBG'),
    ]

    name        = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    rules       = models.TextField(blank=True)

    organizer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='organized_tournaments',
    )

    venue = models.ForeignKey(
        Venue,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='tournaments',
    )
    needs_venue = models.BooleanField(default=True)
    venue_address = models.TextField(blank=True)

    games = models.CharField(
        max_length=50,
        help_text='Select the games for this tournament',
        default='valorant',
    )

    start_date = models.DateField()
    end_date   = models.DateField()
    registration_deadline = models.DateTimeField(null=True, blank=True)
    max_teams  = models.PositiveIntegerField(default=16)
    entry_fee  = models.DecimalField(max_digits=8,  decimal_places=2, default=0.00)
    prize_pool = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # ── NEW: Venue payment fields ──
    venue_payment_required  = models.BooleanField(default=False)
    venue_payment_amount    = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    venue_payment_code      = models.CharField(max_length=20, blank=True)
    venue_payment_confirmed = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def get_games_list(self):
        return [g.strip() for g in self.games.split(',') if g.strip()]

    def get_games_display(self):
        labels = {'valorant': 'Valorant', 'pubg': 'PUBG'}
        return ', '.join(labels.get(g, g) for g in self.get_games_list())

    def is_full(self):
        return self.applications.filter(status='approved').count() >= self.max_teams

    @property
    def enrollment_status(self):
        if self.registration_deadline:
            return 'closed' if timezone.now() >= self.registration_deadline else 'active'
        return 'closed' if timezone.localdate() >= self.start_date else 'active'

    @property
    def display_status(self):
        """Status shown to users, including automatic registration closure."""
        if self.status in {'pending', 'cancelled'}:
            return self.status
        return self.enrollment_status

    def __str__(self):
        return self.name


class TournamentApplication(models.Model):

    APPLICATION_STATUS = [
        ('pending',  'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name='applications')
    team       = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='applications')
    game       = models.CharField(max_length=20)
    status     = models.CharField(max_length=20, choices=APPLICATION_STATUS, default='pending')
    applied_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('tournament', 'team', 'game')

    def __str__(self):
        return f"{self.team.name} → {self.tournament.name} [{self.game}] ({self.status})"



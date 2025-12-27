from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import MatchResult
from .services import advance_winner

@receiver(post_save, sender=MatchResult)
def match_result_post_save(sender, instance, created, **kwargs):
    """
    When a MatchResult is saved (via Admin or Frontend),
    automatically update the Match status to finished
    and advance the winner to the next round.
    """
    match = instance.match
    if match.status != 'finished':
        match.status = 'finished'
        match.save()
    
    # Trigger logic to move winner to next bracket slot
    advance_winner(match)

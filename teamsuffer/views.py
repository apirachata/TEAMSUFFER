from django.shortcuts import render
from django.core.paginator import Paginator
from django.db import models
from tournaments.models import Tournament


def home(request):
    """หน้าหลัก - แสดงรายการทัวร์นาเมนต์"""
    # Search & Filter
    query = request.GET.get('q')
    game_filter_id = request.GET.get('game_id')
    
    tournaments = Tournament.objects.all().order_by('-created_at')
    
    if query:
        tournaments = tournaments.filter(models.Q(name__icontains=query) | models.Q(game__name__icontains=query))
        
    if game_filter_id:
        tournaments = tournaments.filter(game_id=game_filter_id)

    featured = Tournament.objects.filter(is_featured=True).order_by('-created_at').first()
    
    # Get all games for dropdown
    from tournaments.models import Game
    games = list(Game.objects.all())
    selected_id = int(game_filter_id) if game_filter_id and game_filter_id.isdigit() else None

    for g in games:
        g.is_selected = (g.id == selected_id)
    
    # Pagination
    paginator = Paginator(tournaments, 8)  # 8 tournaments per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Check permission for creating tournament safely
    can_create_tournament = False
    if request.user.is_authenticated:
        if request.user.is_superuser or request.user.is_staff:
            can_create_tournament = True
        elif hasattr(request.user, 'profile') and request.user.profile.role == 'tournament_admin':
            can_create_tournament = True

    context = {
        'tournaments': page_obj,
        'featured_tournament': featured,
        'games': games,
        'search_query': query,
        'selected_game_id': selected_id,
        'can_create_tournament': can_create_tournament
    }
    
    return render(request, 'home_fixed_v2.html', context)

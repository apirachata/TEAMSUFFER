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
    games = Game.objects.all()
    
    # Pagination
    paginator = Paginator(tournaments, 8)  # 8 tournaments per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'tournaments': page_obj,
        'featured_tournament': featured,
        'games': games,
        'search_query': query,
        'selected_game_id': int(game_filter_id) if game_filter_id else None
    }
    
    return render(request, 'home_fixed.html', context)

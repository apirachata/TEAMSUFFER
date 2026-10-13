import os
import django
from django.contrib.auth import get_user_model

# Setting up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'teamsuffer.settings')
django.setup()

from teams.models import Team, TeamMember
from tournaments.models import Game

User = get_user_model()

def create_mock_teams():
    print("Starting to create League of Legends mock teams...")

    # 1. Ensure Game exists
    lol_game, created = Game.objects.get_or_create(name="League of Legends")
    if created:
        print("Created Game: League of Legends")
    else:
        print("Found Game: League of Legends")

    # 2. Ensure a mock user exists
    mock_user, created = User.objects.get_or_create(username="lol_mock_admin", email="admin@lolmock.com")
    if created:
        mock_user.set_password("mockpassword123")
        mock_user.save()
        print("Created Mock User: lol_mock_admin")

    # 3. List of mock teams
    team_names = [
        "T1",
        "Gen.G Esports",
        "Dplus KIA",
        "Hanwha Life Esports",
        "KT Rolster",
        "G2 Esports",
        "Fnatic",
        "MAD Lions KOI",
        "Bilibili Gaming",
        "JD Gaming",
        "Weibo Gaming",
        "Top Esports",
        "Cloud9",
        "Team Liquid",
        "NRG",
        "100 Thieves"
    ]

    created_count = 0
    for name in team_names:
        team, t_created = Team.objects.get_or_create(
            name=name,
            defaults={
                'description': f"Mock team for {name}",
                'created_by': mock_user,
                'status': 'active',
                'game': lol_game
            }
        )
        
        if t_created:
            # Add the user as a leader
            TeamMember.objects.get_or_create(
                team=team,
                user=mock_user,
                role_in_team='leader',
                status='accepted'
            )
            created_count += 1
            print(f"Created Team: {name}")
        else:
            print(f"Team already exists: {name}")

    print(f"\nSuccessfully created {created_count} new mock teams.")
    print("You can now go to the tournament page and register these teams to generate the bracket.")

if __name__ == '__main__':
    create_mock_teams()

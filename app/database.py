from app.models import Game, Team
import random
from datetime import date, timedelta
from typing import List, Tuple

games: List[Game] = []
teams: List[Team] = []

# Initialize the db by generated data
def init_db():
    global teams, games
    teams = [
        Team(id=1, name="Lakers", city="Los Angeles", primary_color="Purple"),
        Team(id=2, name="Celtics", city="Boston", primary_color="Green"),
        Team(id=3, name="Warriors", city="Golden State", primary_color="Blue"),
        Team(id=4, name="Bulls", city="Chicago", primary_color="Red"),
        Team(id=5, name="Heat", city="Miami", primary_color="Black"),
    ]

    start_date = date(2024, 10, 15)
    for i in range(30):
        game_date = start_date + timedelta(days=i*2)
        home_team = random.choice(teams)
        away_team = random.choice([t for t in teams if t != home_team])
        games.append(Game(
            game_date=game_date,
            home_team_id=home_team.id,
            home_team_score=random.randint(85, 130),
            away_team_id=away_team.id,
            away_team_score=random.randint(85, 130)
        ))


def get_db() -> Tuple[List[Team], List[Game]]:
    if not teams or not games:
        init_db()
    return teams, games
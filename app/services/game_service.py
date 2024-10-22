from app.models import Game
from app.database import games

class GameService:
    def create_game(self, game: Game):
        games.append(game)
        return game

    def get_games(self):
        return games
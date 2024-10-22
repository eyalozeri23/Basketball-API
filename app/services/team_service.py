from app.models import Team
from app.database import teams

class TeamService:
    def create_team(self, team: Team):
        teams.append(team)
        return team

    def get_teams(self):
        return teams

    def get_team(self, team_id: int):
        return next((team for team in teams if team.id == team_id), None)
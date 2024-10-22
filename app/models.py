from pydantic import BaseModel
from datetime import date
from pydantic_core import to_jsonable_python
from pydantic import json



# Schema for Game table
class Game(BaseModel):
    game_date: date
    home_team_id: int
    home_team_score: int
    away_team_id: int
    away_team_score: int

# Schema for Team table
class Team(BaseModel):
    id: int
    name: str
    city: str
    primary_color: str

# Schema for User that interact with API
class User(BaseModel):
    username: str
    email: str
    full_name: str = None    

# Encrypt password of User
class UserInDB(User):
    hashed_password: str
    
def dict(self, *args, **kwargs):
    try:
        return to_jsonable_python(self, *args, **kwargs)
    except NameError:
        return json.jsonable_encoder(self, *args, **kwargs)
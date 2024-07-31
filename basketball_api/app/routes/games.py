from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from app.models import Game
from app.auth import get_current_user
from app.main import limiter
import json
from typing import List


# Import the global variables that simulate a storage db
from app.database import games, teams

router = APIRouter(prefix="/games", tags=["games"])


# For demonstration - I will create only POST and GET methods:

## Define GET method
@router.get("/", response_model=List[Game])
@limiter.limit("20/minute")
async def read_games(_=Depends(get_current_user)):
    return JSONResponse(content=json.loads(json.dumps([game.dict() for game in games])))

## Define GET method by game id
@router.get("/{game_id}", response_model=Game)
@limiter.limit("20/minute")
async def read_game(game_id: int,_=Depends(get_current_user)):
    game = next((game for game in games if game.id == game_id), None)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    return JSONResponse(content=json.loads(json.dumps(game.dict())))

## Define POST method
@router.post("/", response_model=Game)
@limiter.limit("10/minute")
async def create_game(game: Game,_=Depends(get_current_user)):
    if any(g.id == game.id for g in games):
        raise HTTPException(status_code=400, detail="Game with this ID already exists")
    if not any(t.id == game.home_team_id for t in teams) or not any(t.id == game.away_team_id for t in teams):
        raise HTTPException(status_code=400, detail="Invalid team ID")
    games.append(game)
    return JSONResponse(content=json.loads(json.dumps(game.dict())), status_code=201)
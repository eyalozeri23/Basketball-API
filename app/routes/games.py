from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from app.models import Game
from typing import List
from app.database import get_db
from app.limiter import limiter

router = APIRouter(prefix="/games", tags=["games"])

@router.get("/", response_model=List[Game])
@limiter.limit("20/minute")
async def read_games(request: Request):
    _, games = get_db()
    return games

@router.get("/{game_id}", response_model=Game)
@limiter.limit("20/minute")
async def read_game(game_id: int, request: Request):
    _, games = get_db()
    game = next((game for game in games if game.game_date.strftime("%Y%m%d") == str(game_id)), None)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    return game

@router.post("/", response_model=Game)
@limiter.limit("10/minute")
async def create_game(game: Game, request: Request):
    teams, games = get_db()
    if not any(t.id == game.home_team_id for t in teams) or not any(t.id == game.away_team_id for t in teams):
        raise HTTPException(status_code=400, detail="Invalid team ID")
    games.append(game)
    return game
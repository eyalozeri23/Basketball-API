from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from app.models import Team
from typing import List
from app.database import get_db
from app.limiter import limiter

router = APIRouter(prefix="/teams", tags=["teams"])

@router.get("/", response_model=List[Team])
@limiter.limit("20/minute")
async def read_teams(request: Request):
    teams, _ = get_db()
    return teams

@router.get("/{team_id}", response_model=Team)
@limiter.limit("20/minute")
async def read_team(team_id: int, request: Request):
    teams, _ = get_db()
    team = next((team for team in teams if team.id == team_id), None)
    if team is None:
        raise HTTPException(status_code=404, detail="Team not found")
    return team

@router.post("/", response_model=Team)
@limiter.limit("10/minute")
async def create_team(team: Team, request: Request):
    teams, _ = get_db()
    if any(t.id == team.id for t in teams):
        raise HTTPException(status_code=400, detail="Team with this ID already exists")
    teams.append(team)
    return team
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from app.models import Team
from app.auth import get_current_user
from app.main import limiter
import json
from typing import List


# Import the global variable that simulate a storage db
from app.database import teams

router = APIRouter(prefix="/teams", tags=["teams"])


# For demonstration - I will create only POST and GET methods:

## Define GET method
@router.get("/", response_model=List[Team])
@limiter.limit("20/minute")
async def read_teams(_=Depends(get_current_user)):
    return JSONResponse(content=json.loads(json.dumps([team.dict() for team in teams])))


## Define GET method by team id
@router.get("/{team_id}", response_model=Team)
@limiter.limit("20/minute")
async def read_team(team_id: int,_=Depends(get_current_user)):
    team = next((team for team in teams if team.id == team_id), None)
    if team is None:
        raise HTTPException(status_code=404, detail="Team not found")
    return JSONResponse(content=json.loads(json.dumps(team.dict())))

## Define POST method
@router.post("/", response_model=Team)
@limiter.limit("10/minute")
async def create_team(team: Team,_=Depends(get_current_user)):
    if any(t.id == team.id for t in teams):
        raise HTTPException(status_code=400, detail="Team with this ID already exists")
    teams.append(team)
    return JSONResponse(content=json.loads(json.dumps(team.dict())), status_code=201)
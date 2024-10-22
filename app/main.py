from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.routes import games, teams
from app.limiter import limiter
from app.database import init_db
import os

# Rate limit set up to limit requests based on client's IP



app = FastAPI(title="Basketball API", description="API for managing basketball games and teams", version="1.0.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Set credentials for API to be accessible for all origins (will be restricted in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "Welcome to the Basketball API"}

# Set up routers for authentication
app.include_router(games.router)
app.include_router(teams.router)


@app.on_event("startup")
async def startup_event():
    init_db()


# Start FastAPI app by running the server using unicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)), reload=True)
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.routes import games, teams, auth
import os

# Rate limit set up to limit requests based on client's IP
limiter = Limiter(key_func=get_remote_address)

# Set an instance for FastAPI
app = FastAPI()
app.state.limiter = limiter

# Set credentials for API to be accessible for all origins (will be restricted in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set up routers for authentication
app.include_router(auth.router)
app.include_router(games.router)
app.include_router(teams.router)

# Start FastAPI app by running the server using unicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)), reload=True)
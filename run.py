import uvicorn
import os
from dotenv import load_dotenv

load_dotenv()

# Start FastAPI app by running the server using uvicorn
if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)), reload=True)

    
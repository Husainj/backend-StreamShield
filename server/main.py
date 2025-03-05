from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
import os
import sys

# Add the server directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from StreamShield.api import app as streamshield_app

app = FastAPI()

# Configure CORS to allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
    expose_headers=["*"],  # Allow client to read all custom headers
    max_age=3600,  # Cache preflight requests for 1 hour
)

# Mount the StreamShield API
app.mount("/api", streamshield_app)

# Only serve static files if the dist directory exists (production mode)
client_dist = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Client", "dist")
if os.path.exists(client_dist):
    app.mount("/", StaticFiles(directory=client_dist, html=True), name="static")

if __name__ == "__main__":
    # Configure Uvicorn with increased limits
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=3000, 
        reload=True,
        timeout_keep_alive=300,  # Increase keep-alive timeout
        limit_concurrency=1000,  # Increase concurrent connections limit
        limit_max_requests=1000  # Increase max requests
    )

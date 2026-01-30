"""
AI-Buzz Tools API
A unified FastAPI microservice for AI developer tools.
"""

import os
import logging
import time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api import pricing, status, error_decoder, embed, tools_landing, analytics

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# FastAPI App Setup
# ============================================================================

app = FastAPI(
    title="AI-Buzz Tools API",
    description="Unified API for AI developer tools: pricing calculator, status monitoring, error decoder",
    version="2.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://ai-buzz.com",
        "https://www.ai-buzz.com",
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://localhost:8765",
        "http://127.0.0.1:8765",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(pricing.router, prefix="/pricing", tags=["pricing"])
app.include_router(status.router, prefix="/status", tags=["status"])
app.include_router(error_decoder.router, prefix="/error-decoder", tags=["error-decoder"])
app.include_router(tools_landing.router, prefix="/tools", tags=["tools-landing"])
app.include_router(embed.router, tags=["embed"])
app.include_router(analytics.router, prefix="/analytics", tags=["analytics"])


# ============================================================================
# Health Check Endpoint
# ============================================================================

@app.get("/")
async def root():
    """Health check endpoint."""
    start_time = getattr(app.state, "start_time", None)
    if start_time is None:
        app.state.start_time = time.time()
        start_time = app.state.start_time
    
    uptime_seconds = int(time.time() - start_time)
    uptime_hours = uptime_seconds // 3600
    uptime_minutes = (uptime_seconds % 3600) // 60
    
    return {
        "status": "healthy",
        "service": "AI-Buzz Tools API",
        "version": "2.0.0",
        "git_commit": os.getenv("RENDER_GIT_COMMIT", "local"),
        "uptime": {
            "seconds": uptime_seconds,
            "formatted": f"{uptime_hours}h {uptime_minutes}m"
        },
        "tools": {
            "pricing": "available",
            "status": "available",
            "error_decoder": "available",
            "tools_landing": "available",
            "analytics": "available"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

"""
Tools Landing API Router
Handles email subscription for the tools landing page.
"""

import logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field, EmailStr

from api.shared import subscribe_email, load_widget

logger = logging.getLogger(__name__)

router = APIRouter()

# ============================================================================
# Pydantic Models
# ============================================================================

class SubscribeRequest(BaseModel):
    """Request model for email subscription."""
    email: EmailStr = Field(..., description="Email address for tool updates")


class SubscribeResponse(BaseModel):
    """Response model for email subscription."""
    success: bool = Field(..., description="Whether subscription was successful")
    message: str = Field(..., description="Status message")
    mailchimp_synced: bool = Field(False, description="Whether synced to Mailchimp")


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/alerts/subscribe", response_model=SubscribeResponse)
async def subscribe_alerts(request: SubscribeRequest):
    """
    Subscribe to new tool launch updates.
    Integrates with Mailchimp if configured.
    """
    result = subscribe_email(
        email=request.email,
        tool_name="tools-landing",
        interest_tags=["interest:new-tools"],
        success_message="Successfully subscribed! You'll be notified when we launch new tools."
    )
    
    return SubscribeResponse(**result)


@router.get("/widget", response_class=HTMLResponse)
async def get_tools_landing_widget():
    """
    Serve the Tools Landing email signup widget HTML.
    For embedding in WordPress/Bricks.
    """
    try:
        widget_html = load_widget("tools_landing_widget.html")
        return HTMLResponse(content=widget_html, status_code=200)
    except FileNotFoundError:
        logger.error("tools_landing_widget.html not found")
        raise HTTPException(status_code=404, detail="Widget file not found")

"""
Status Page API Router
Handles all status monitoring endpoints.
"""

import logging
import asyncio
import time
from typing import Dict, Any, Optional, List
from datetime import datetime

import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field, EmailStr

from api.shared import load_json_data, subscribe_email, load_widget

logger = logging.getLogger(__name__)

router = APIRouter()

# ============================================================================
# Pydantic Models
# ============================================================================

class ProviderStatus(BaseModel):
    """Status information for a single AI provider."""
    id: str = Field(..., description="Provider ID")
    name: str = Field(..., description="Provider display name")
    status: str = Field(..., description="Status: operational, degraded, or down")
    latency_ms: Optional[int] = Field(None, description="Response latency in milliseconds")
    last_checked: str = Field(..., description="ISO timestamp of last check")
    status_page_url: str = Field(..., description="URL to provider's official status page")
    error: Optional[str] = Field(None, description="Error message if down")


class StatusResponse(BaseModel):
    """Response model for status endpoint."""
    success: bool = Field(..., description="Whether request was successful")
    overall_status: str = Field(..., description="Overall status: all_operational, issues_detected, or major_outage")
    providers: List[ProviderStatus] = Field(..., description="Status for each provider")
    operational_count: int = Field(..., description="Number of operational providers")
    degraded_count: int = Field(..., description="Number of degraded providers")
    down_count: int = Field(..., description="Number of down providers")
    last_updated: str = Field(..., description="ISO timestamp of this response")
    cache_ttl_seconds: int = Field(60, description="How long this data is cached")


class SubscribeRequest(BaseModel):
    """Request model for status alert subscription."""
    email: EmailStr = Field(..., description="Email address for outage alerts")


class SubscribeResponse(BaseModel):
    """Response model for email subscription."""
    success: bool = Field(..., description="Whether subscription was successful")
    message: str = Field(..., description="Status message")
    mailchimp_synced: bool = Field(False, description="Whether synced to Mailchimp")


# ============================================================================
# Status Checking Logic
# ============================================================================

# Cache for status data
_status_cache: Optional[Dict[str, Any]] = None
_status_cache_time: float = 0
STATUS_CACHE_TTL = 60  # 60 seconds cache

# Thresholds
LATENCY_DEGRADED_MS = 2000  # Above this = degraded
REQUEST_TIMEOUT_S = 10  # Timeout = down


async def check_provider_status(
    client: httpx.AsyncClient,
    provider_id: str,
    provider_config: Dict[str, Any]
) -> ProviderStatus:
    """
    Check the status of a single provider by hitting their API endpoint.
    
    Status logic:
    - Operational: Response received, latency < 2000ms
    - Degraded: Response received, latency >= 2000ms
    - Down: Timeout, 5xx error, or connection failed
    """
    endpoint = provider_config["endpoint"]
    method = provider_config.get("method", "GET")
    status_page = provider_config.get("status_page", "")
    name = provider_config["name"]
    
    start_time = time.time()
    last_checked = datetime.utcnow().isoformat() + "Z"
    
    try:
        if method == "POST":
            response = await client.post(
                endpoint,
                json={},
                timeout=REQUEST_TIMEOUT_S
            )
        else:
            response = await client.get(
                endpoint,
                timeout=REQUEST_TIMEOUT_S
            )
        
        latency_ms = int((time.time() - start_time) * 1000)
        status_code = response.status_code
        
        # Check if status code indicates the API is alive
        # Expected codes (401, 400) mean the API is responding, just needs auth
        # 5xx errors indicate server issues
        if status_code >= 500:
            return ProviderStatus(
                id=provider_id,
                name=name,
                status="down",
                latency_ms=latency_ms,
                last_checked=last_checked,
                status_page_url=status_page,
                error=f"Server error: HTTP {status_code}"
            )
        
        # API is responding - check if degraded based on latency
        if latency_ms >= LATENCY_DEGRADED_MS:
            return ProviderStatus(
                id=provider_id,
                name=name,
                status="degraded",
                latency_ms=latency_ms,
                last_checked=last_checked,
                status_page_url=status_page,
                error=f"High latency: {latency_ms}ms"
            )
        
        # All good - operational
        return ProviderStatus(
            id=provider_id,
            name=name,
            status="operational",
            latency_ms=latency_ms,
            last_checked=last_checked,
            status_page_url=status_page,
            error=None
        )
        
    except httpx.TimeoutException:
        latency_ms = int((time.time() - start_time) * 1000)
        return ProviderStatus(
            id=provider_id,
            name=name,
            status="down",
            latency_ms=latency_ms,
            last_checked=last_checked,
            status_page_url=status_page,
            error=f"Timeout after {REQUEST_TIMEOUT_S}s"
        )
    except httpx.ConnectError:
        return ProviderStatus(
            id=provider_id,
            name=name,
            status="down",
            latency_ms=None,
            last_checked=last_checked,
            status_page_url=status_page,
            error="Connection failed"
        )
    except Exception as e:
        logger.error(f"Error checking {provider_id}: {str(e)}")
        return ProviderStatus(
            id=provider_id,
            name=name,
            status="down",
            latency_ms=None,
            last_checked=last_checked,
            status_page_url=status_page,
            error=str(e)[:100]
        )


async def check_all_providers() -> StatusResponse:
    """
    Check status of all configured providers concurrently.
    Uses caching to avoid hammering APIs.
    """
    global _status_cache, _status_cache_time
    
    # Check cache
    current_time = time.time()
    if _status_cache is not None and (current_time - _status_cache_time) < STATUS_CACHE_TTL:
        logger.info("Returning cached status data")
        return StatusResponse(**_status_cache)
    
    logger.info("Fetching fresh status data")
    config = load_json_data("status_providers.json")
    providers_config = config.get("providers", {})
    
    # Check all providers concurrently
    async with httpx.AsyncClient() as client:
        tasks = [
            check_provider_status(client, provider_id, provider_config)
            for provider_id, provider_config in providers_config.items()
        ]
        provider_statuses = await asyncio.gather(*tasks)
    
    # Sort by status (down first, then degraded, then operational) then by name
    status_order = {"down": 0, "degraded": 1, "operational": 2}
    provider_statuses = sorted(
        provider_statuses,
        key=lambda x: (status_order.get(x.status, 3), x.name)
    )
    
    # Calculate counts
    operational_count = sum(1 for p in provider_statuses if p.status == "operational")
    degraded_count = sum(1 for p in provider_statuses if p.status == "degraded")
    down_count = sum(1 for p in provider_statuses if p.status == "down")
    
    # Determine overall status
    if down_count > 0:
        if down_count >= len(provider_statuses) / 2:
            overall_status = "major_outage"
        else:
            overall_status = "issues_detected"
    elif degraded_count > 0:
        overall_status = "issues_detected"
    else:
        overall_status = "all_operational"
    
    response_data = {
        "success": True,
        "overall_status": overall_status,
        "providers": [p.model_dump() for p in provider_statuses],
        "operational_count": operational_count,
        "degraded_count": degraded_count,
        "down_count": down_count,
        "last_updated": datetime.utcnow().isoformat() + "Z",
        "cache_ttl_seconds": STATUS_CACHE_TTL
    }
    
    # Update cache
    _status_cache = response_data
    _status_cache_time = current_time
    
    return StatusResponse(**response_data)


# ============================================================================
# API Endpoints
# ============================================================================

@router.get("/check", response_model=StatusResponse)
async def get_status():
    """
    Get current status of all AI API providers.
    Results are cached for 60 seconds.
    """
    try:
        return await check_all_providers()
    except FileNotFoundError:
        logger.error("status_providers.json not found")
        raise HTTPException(status_code=500, detail="Status configuration not available.")
    except Exception as e:
        logger.error(f"Error checking status: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error checking status: {str(e)}")


@router.post("/alerts/subscribe", response_model=SubscribeResponse)
async def subscribe_alerts(request: SubscribeRequest):
    """
    Subscribe to AI API outage alerts.
    Integrates with Mailchimp if configured.
    """
    result = subscribe_email(
        email=request.email,
        tool_name="status-page",
        interest_tags=["interest:status-alerts"],
        success_message="Successfully subscribed to outage alerts!"
    )
    
    return SubscribeResponse(**result)


@router.get("/widget", response_class=HTMLResponse)
async def get_status_widget():
    """
    Serve the Status Page widget HTML.
    For embedding in WordPress/Bricks.
    """
    try:
        widget_html = load_widget("status_page_widget.html")
        return HTMLResponse(content=widget_html, status_code=200)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Widget file not found")

"""
Error Decoder API Router
Handles error decoding endpoints.
"""

import logging
import re
from typing import Dict, Any, Optional, List
from datetime import datetime

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field, EmailStr

from api.shared import load_json_data, subscribe_email, load_widget
from api.analytics import track_error_decode

logger = logging.getLogger(__name__)

router = APIRouter()

# ============================================================================
# Pydantic Models
# ============================================================================

class ErrorPattern(BaseModel):
    """Error pattern information."""
    id: str = Field(..., description="Pattern ID")
    provider: str = Field(..., description="Provider name")
    provider_id: str = Field(..., description="Provider ID")
    error_keywords: List[str] = Field(..., description="Keywords to match")
    title: str = Field(..., description="Error title")
    explanation: str = Field(..., description="Plain English explanation")
    fix: str = Field(..., description="How to fix the error")
    severity: str = Field(..., description="Error severity: error, warning")
    common: bool = Field(..., description="Whether this is a common error")
    docs_url: Optional[str] = Field(None, description="Link to documentation")


class DecodeRequest(BaseModel):
    """Request model for error decoding."""
    error_message: str = Field(..., min_length=1, description="The error message to decode")


class DecodedError(BaseModel):
    """Decoded error information."""
    pattern: ErrorPattern = Field(..., description="Matched error pattern")
    confidence: str = Field(..., description="Match confidence: high, medium, low")
    matched_keywords: List[str] = Field(..., description="Keywords that matched")


class DecodeResponse(BaseModel):
    """Response model for error decoding."""
    success: bool = Field(..., description="Whether decoding was successful")
    error_message: str = Field(..., description="Original error message")
    decoded: Optional[DecodedError] = Field(None, description="Decoded error if match found")
    suggestions: List[str] = Field(default_factory=list, description="General suggestions if no match")
    decoded_at: str = Field(..., description="ISO timestamp of decoding")


class PatternsResponse(BaseModel):
    """Response model for patterns endpoint."""
    success: bool = Field(..., description="Whether request was successful")
    patterns: List[ErrorPattern] = Field(..., description="All available error patterns")
    providers: List[str] = Field(..., description="List of unique providers")
    last_updated: str = Field(..., description="Date patterns were last updated")


class SubscribeRequest(BaseModel):
    """Request model for email subscription."""
    email: EmailStr = Field(..., description="Email address for error decoder updates")


class SubscribeResponse(BaseModel):
    """Response model for email subscription."""
    success: bool = Field(..., description="Whether subscription was successful")
    message: str = Field(..., description="Status message")
    mailchimp_synced: bool = Field(False, description="Whether synced to Mailchimp")


# ============================================================================
# Helper Functions
# ============================================================================

def match_error_pattern(error_message: str, pattern: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Match an error message against a pattern.
    Returns match info if found, None otherwise.
    """
    error_lower = error_message.lower()
    matched_keywords = []
    
    for keyword in pattern.get("error_keywords", []):
        keyword_lower = keyword.lower()
        # Check for exact word match or substring match
        if keyword_lower in error_lower:
            matched_keywords.append(keyword)
    
    if not matched_keywords:
        return None
    
    # Calculate confidence based on number of matches
    keyword_count = len(pattern.get("error_keywords", []))
    match_count = len(matched_keywords)
    
    if match_count >= min(3, keyword_count):
        confidence = "high"
    elif match_count >= 2:
        confidence = "medium"
    else:
        confidence = "low"
    
    return {
        "pattern": pattern,
        "matched_keywords": matched_keywords,
        "confidence": confidence,
        "match_score": match_count / keyword_count if keyword_count > 0 else 0
    }


def decode_error(error_message: str, patterns: List[Dict[str, Any]]) -> Optional[DecodedError]:
    """
    Decode an error message by matching against patterns.
    Returns the best match if found.
    """
    matches = []
    
    for pattern in patterns:
        match_info = match_error_pattern(error_message, pattern)
        if match_info:
            matches.append(match_info)
    
    if not matches:
        return None
    
    # Sort by match score (descending) and confidence
    matches.sort(key=lambda x: (x["match_score"], x["confidence"] == "high"), reverse=True)
    
    best_match = matches[0]
    
    return DecodedError(
        pattern=ErrorPattern(**best_match["pattern"]),
        confidence=best_match["confidence"],
        matched_keywords=best_match["matched_keywords"]
    )


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/decode", response_model=DecodeResponse)
async def decode_error_message(request: DecodeRequest):
    """
    Decode an API error message into plain English explanation and fix.
    Matches error messages against known patterns.
    """
    try:
        error_data = load_json_data("error_patterns.json")
        patterns = error_data.get("patterns", [])
        
        decoded = decode_error(request.error_message, patterns)
        
        # Track usage for analytics
        track_error_decode(
            error_message=request.error_message,
            matched=decoded is not None,
            pattern_id=decoded.pattern.id if decoded else None
        )
        
        suggestions = []
        if not decoded:
            # Provide general suggestions if no match found
            suggestions = [
                "Check your API key and authentication",
                "Verify your request parameters are correct",
                "Check the API documentation for the specific error",
                "Ensure your network connection is stable",
                "Try again after a few moments (may be temporary)"
            ]
        
        return DecodeResponse(
            success=True,
            error_message=request.error_message,
            decoded=decoded,
            suggestions=suggestions,
            decoded_at=datetime.utcnow().isoformat() + "Z"
        )
    
    except FileNotFoundError:
        logger.error("error_patterns.json not found")
        raise HTTPException(status_code=500, detail="Error patterns not available.")
    except Exception as e:
        logger.error(f"Error decoding error message: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error decoding error message: {str(e)}")


@router.get("/decode")
async def decode_error_message_get(error_message: str):
    """
    GET version of decode endpoint for shareable URLs.
    Example: /error-decoder/decode?error_message=rate%20limit%20exceeded
    """
    request = DecodeRequest(error_message=error_message)
    return await decode_error_message(request)


@router.get("/patterns", response_model=PatternsResponse)
async def get_error_patterns():
    """
    Get all available error patterns.
    Useful for displaying a list of common errors.
    """
    try:
        error_data = load_json_data("error_patterns.json")
        patterns = error_data.get("patterns", [])
        
        # Extract unique providers
        providers = sorted(set(p.get("provider", "Unknown") for p in patterns))
        
        pattern_models = [ErrorPattern(**p) for p in patterns]
        
        return PatternsResponse(
            success=True,
            patterns=pattern_models,
            providers=providers,
            last_updated=error_data.get("_metadata", {}).get("last_updated", "unknown")
        )
    
    except FileNotFoundError:
        logger.error("error_patterns.json not found")
        raise HTTPException(status_code=500, detail="Error patterns not available.")
    except Exception as e:
        logger.error(f"Error loading error patterns: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error loading error patterns: {str(e)}")


@router.post("/alerts/subscribe", response_model=SubscribeResponse)
async def subscribe_alerts(request: SubscribeRequest):
    """
    Subscribe to error decoder updates and tips.
    Integrates with Mailchimp if configured.
    """
    result = subscribe_email(
        email=request.email,
        tool_name="error-decoder",
        interest_tags=["interest:error-tips"],
        success_message="Successfully subscribed to error decoder updates!"
    )
    
    return SubscribeResponse(**result)


@router.get("/widget", response_class=HTMLResponse)
async def get_error_decoder_widget():
    """
    Serve the Error Decoder widget HTML.
    For embedding in WordPress/Bricks.
    """
    try:
        widget_html = load_widget("error_decoder_widget.html")
        return HTMLResponse(content=widget_html, status_code=200)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Widget file not found")

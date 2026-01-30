"""
Analytics API Router
Handles usage tracking and gap detection for all tools.
"""

import hashlib
import logging
from datetime import datetime
from typing import Dict, Any, List

from fastapi import APIRouter
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter()

# ============================================================================
# In-Memory Storage
# ============================================================================

# Resets on deploy - acceptable, GA4 has historical data
_stats: Dict[str, Any] = {
    "started_at": datetime.utcnow().isoformat() + "Z",
    "error_decoder": {
        "total": 0,
        "matched": 0,
        "unmatched": 0,
        "gaps": {}  # hash -> {count, preview, first_seen}
    },
    "pricing_calculator": {
        "total": 0,
        "token_buckets": {"under_1k": 0, "1k_to_10k": 0, "10k_to_100k": 0, "over_100k": 0},
        "models_not_found": {}  # search_term -> count
    },
    "status_page": {
        "total": 0,
        "by_provider": {}  # provider_id -> count
    }
}


# ============================================================================
# Pydantic Models
# ============================================================================

class ErrorDecoderStats(BaseModel):
    """Stats for error decoder usage."""
    total: int = Field(..., description="Total decode attempts")
    matched: int = Field(..., description="Attempts that found a pattern")
    unmatched: int = Field(..., description="Attempts with no match (gaps)")
    gaps: Dict[str, Any] = Field(..., description="Unmatched error hashes with counts")


class PricingCalculatorStats(BaseModel):
    """Stats for pricing calculator usage."""
    total: int = Field(..., description="Total calculations")
    token_buckets: Dict[str, int] = Field(..., description="Token usage distribution")
    models_not_found: Dict[str, int] = Field(..., description="Models searched but not found")


class StatusPageStats(BaseModel):
    """Stats for status page usage."""
    total: int = Field(..., description="Total status checks")
    by_provider: Dict[str, int] = Field(..., description="Checks per provider")


class StatsData(BaseModel):
    """All usage stats."""
    started_at: str = Field(..., description="When stats collection started")
    error_decoder: ErrorDecoderStats
    pricing_calculator: PricingCalculatorStats
    status_page: StatusPageStats


class StatsResponse(BaseModel):
    """Response for stats endpoint."""
    success: bool = Field(True)
    data: StatsData
    note: str = Field("In-memory stats reset on deploy. Use pull-ga4 for historical data.")


class GapItem(BaseModel):
    """A single gap item."""
    hash: str
    count: int
    preview: str
    first_seen: str


class ModelNotFound(BaseModel):
    """A model that was searched but not found."""
    search_term: str
    searches: int


class GapsResponse(BaseModel):
    """Response for gaps endpoint."""
    success: bool = Field(True)
    error_patterns_to_add: List[GapItem] = Field(..., description="Top unmatched errors")
    pricing_models_to_add: List[ModelNotFound] = Field(..., description="Top models not found")


# ============================================================================
# Tracking Functions (called by other routers)
# ============================================================================

def track_error_decode(error_message: str, matched: bool, pattern_id: str = None) -> None:
    """
    Track an error decode attempt.
    
    Args:
        error_message: The error message user tried to decode
        matched: Whether a pattern was found
        pattern_id: ID of matched pattern (if any)
    """
    _stats["error_decoder"]["total"] += 1
    
    if matched:
        _stats["error_decoder"]["matched"] += 1
    else:
        _stats["error_decoder"]["unmatched"] += 1
        # Store anonymized gap
        msg_hash = hashlib.sha256(error_message.encode()).hexdigest()[:12]
        preview = error_message[:50] + ("..." if len(error_message) > 50 else "")
        
        if msg_hash not in _stats["error_decoder"]["gaps"]:
            _stats["error_decoder"]["gaps"][msg_hash] = {
                "count": 0,
                "preview": preview,
                "first_seen": datetime.utcnow().isoformat() + "Z"
            }
        _stats["error_decoder"]["gaps"][msg_hash]["count"] += 1
        
        logger.info(f"Gap detected: {msg_hash} (preview: {preview[:30]}...)")


def track_pricing_calculation(input_tokens: int, output_tokens: int) -> None:
    """
    Track a pricing calculation.
    
    Args:
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
    """
    _stats["pricing_calculator"]["total"] += 1
    
    # Bucket by total tokens
    total = input_tokens + output_tokens
    if total < 1000:
        _stats["pricing_calculator"]["token_buckets"]["under_1k"] += 1
    elif total < 10000:
        _stats["pricing_calculator"]["token_buckets"]["1k_to_10k"] += 1
    elif total < 100000:
        _stats["pricing_calculator"]["token_buckets"]["10k_to_100k"] += 1
    else:
        _stats["pricing_calculator"]["token_buckets"]["over_100k"] += 1


def track_model_not_found(search_term: str) -> None:
    """
    Track when a user searches for a model that doesn't exist.
    
    Args:
        search_term: The model name/term user searched for
    """
    # Normalize search term
    normalized = search_term.lower().strip()
    if not normalized:
        return
        
    if normalized not in _stats["pricing_calculator"]["models_not_found"]:
        _stats["pricing_calculator"]["models_not_found"][normalized] = 0
    _stats["pricing_calculator"]["models_not_found"][normalized] += 1
    
    logger.info(f"Model not found: {normalized}")


def track_status_check(provider_id: str) -> None:
    """
    Track a status page check for a provider.
    
    Args:
        provider_id: The provider ID that was checked
    """
    _stats["status_page"]["total"] += 1
    
    if provider_id not in _stats["status_page"]["by_provider"]:
        _stats["status_page"]["by_provider"][provider_id] = 0
    _stats["status_page"]["by_provider"][provider_id] += 1


# ============================================================================
# API Endpoints
# ============================================================================

@router.get("/stats", response_model=StatsResponse)
async def get_stats():
    """
    Get current usage stats and gaps.
    
    In-memory stats that reset on deploy. For historical data,
    use the CLI: python scripts/analytics.py pull-ga4
    """
    return StatsResponse(
        success=True,
        data=StatsData(
            started_at=_stats["started_at"],
            error_decoder=ErrorDecoderStats(**_stats["error_decoder"]),
            pricing_calculator=PricingCalculatorStats(**_stats["pricing_calculator"]),
            status_page=StatusPageStats(**_stats["status_page"])
        ),
        note="In-memory stats reset on deploy. Use pull-ga4 for historical data."
    )


@router.get("/gaps", response_model=GapsResponse)
async def get_gaps():
    """
    Get actionable gaps - things users tried that didn't work.
    
    Returns:
        - Top unmatched error patterns (add these to error_patterns.json)
        - Top models not found (add these to pricing_data.json)
    """
    # Sort error gaps by count (descending)
    error_gaps = sorted(
        [
            GapItem(hash=k, count=v["count"], preview=v["preview"], first_seen=v["first_seen"])
            for k, v in _stats["error_decoder"]["gaps"].items()
        ],
        key=lambda x: x.count,
        reverse=True
    )[:20]
    
    # Sort models not found by searches (descending)
    models_not_found = sorted(
        [
            ModelNotFound(search_term=k, searches=v)
            for k, v in _stats["pricing_calculator"]["models_not_found"].items()
        ],
        key=lambda x: x.searches,
        reverse=True
    )[:20]
    
    return GapsResponse(
        success=True,
        error_patterns_to_add=error_gaps,
        pricing_models_to_add=models_not_found
    )


@router.get("/reset")
async def reset_stats():
    """
    Reset all stats. Useful for testing.
    Returns the stats before reset.
    """
    global _stats
    
    old_stats = _stats.copy()
    
    _stats = {
        "started_at": datetime.utcnow().isoformat() + "Z",
        "error_decoder": {
            "total": 0,
            "matched": 0,
            "unmatched": 0,
            "gaps": {}
        },
        "pricing_calculator": {
            "total": 0,
            "token_buckets": {"under_1k": 0, "1k_to_10k": 0, "10k_to_100k": 0, "over_100k": 0},
            "models_not_found": {}
        },
        "status_page": {
            "total": 0,
            "by_provider": {}
        }
    }
    
    logger.info("Stats reset")
    
    return {
        "success": True,
        "message": "Stats reset",
        "previous_stats": old_stats
    }

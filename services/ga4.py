"""
GA4 Data API Service
Pull analytics data from Google Analytics 4.

Setup:
1. Enable "Google Analytics Data API" in Google Cloud Console
2. Create Service Account and download JSON key
3. Add service account email as Viewer in GA4 Admin -> Property Access Management
4. Set environment variables:
   - GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json
   - GA4_PROPERTY_ID=your-property-id (found in GA4 Admin -> Property Settings)
"""

import os
import logging
from datetime import datetime
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Check if GA4 API is available
try:
    from google.analytics.data_v1beta import BetaAnalyticsDataClient
    from google.analytics.data_v1beta.types import (
        RunReportRequest,
        DateRange,
        Dimension,
        Metric,
    )
    GA4_AVAILABLE = True
except ImportError:
    GA4_AVAILABLE = False
    logger.info("google-analytics-data not installed - GA4 pull disabled")

# Configuration
PROPERTY_ID = os.getenv("GA4_PROPERTY_ID")


def is_configured() -> bool:
    """Check if GA4 is properly configured."""
    return GA4_AVAILABLE and bool(PROPERTY_ID)


def pull_events(days: int = 30) -> Dict[str, Any]:
    """
    Pull event data from GA4 for the last N days.
    
    Args:
        days: Number of days to pull (default 30)
        
    Returns:
        Dictionary with events grouped by event name and tool_name
    """
    if not GA4_AVAILABLE:
        return {
            "success": False,
            "error": "google-analytics-data package not installed. Run: pip install google-analytics-data"
        }
    
    if not PROPERTY_ID:
        return {
            "success": False,
            "error": "GA4_PROPERTY_ID environment variable not set"
        }
    
    try:
        client = BetaAnalyticsDataClient()
        
        # First try with tool_name custom dimension, fall back to eventName only
        try:
            request = RunReportRequest(
                property=f"properties/{PROPERTY_ID}",
                date_ranges=[DateRange(
                    start_date=f"{days}daysAgo",
                    end_date="today"
                )],
                dimensions=[
                    Dimension(name="eventName"),
                    Dimension(name="customEvent:tool_name"),
                ],
                metrics=[
                    Metric(name="eventCount"),
                ],
            )
            response = client.run_report(request)
            has_tool_name = True
        except Exception as e:
            # tool_name dimension not set up, fall back to eventName only
            logger.info(f"tool_name dimension not available, using eventName only: {e}")
            request = RunReportRequest(
                property=f"properties/{PROPERTY_ID}",
                date_ranges=[DateRange(
                    start_date=f"{days}daysAgo",
                    end_date="today"
                )],
                dimensions=[
                    Dimension(name="eventName"),
                ],
                metrics=[
                    Metric(name="eventCount"),
                ],
            )
            response = client.run_report(request)
            has_tool_name = False
        
        # Process response into structured data
        events: Dict[str, Dict[str, int]] = {}
        for row in response.rows:
            event_name = row.dimension_values[0].value
            if has_tool_name:
                tool_name = row.dimension_values[1].value or "unknown"
            else:
                tool_name = "all"
            count = int(row.metric_values[0].value)
            
            if event_name not in events:
                events[event_name] = {}
            events[event_name][tool_name] = count
        
        return {
            "success": True,
            "period": f"last_{days}_days",
            "pulled_at": datetime.utcnow().isoformat() + "Z",
            "events": events
        }
        
    except Exception as e:
        logger.error(f"Failed to pull GA4 events: {e}")
        return {
            "success": False,
            "error": str(e)
        }


def pull_traffic(days: int = 30) -> Dict[str, Any]:
    """
    Pull traffic/pageview data from GA4.
    
    Args:
        days: Number of days to pull (default 30)
        
    Returns:
        Dictionary with page views and users by path
    """
    if not GA4_AVAILABLE:
        return {
            "success": False,
            "error": "google-analytics-data package not installed"
        }
    
    if not PROPERTY_ID:
        return {
            "success": False,
            "error": "GA4_PROPERTY_ID environment variable not set"
        }
    
    try:
        client = BetaAnalyticsDataClient()
        
        request = RunReportRequest(
            property=f"properties/{PROPERTY_ID}",
            date_ranges=[DateRange(
                start_date=f"{days}daysAgo",
                end_date="today"
            )],
            dimensions=[
                Dimension(name="pagePath"),
            ],
            metrics=[
                Metric(name="screenPageViews"),
                Metric(name="activeUsers"),
            ],
        )
        
        response = client.run_report(request)
        
        pages = []
        for row in response.rows:
            pages.append({
                "path": row.dimension_values[0].value,
                "views": int(row.metric_values[0].value),
                "users": int(row.metric_values[1].value),
            })
        
        # Sort by views descending
        pages.sort(key=lambda x: x["views"], reverse=True)
        
        return {
            "success": True,
            "period": f"last_{days}_days",
            "pulled_at": datetime.utcnow().isoformat() + "Z",
            "pages": pages
        }
        
    except Exception as e:
        logger.error(f"Failed to pull GA4 traffic: {e}")
        return {
            "success": False,
            "error": str(e)
        }


def pull_funnel(days: int = 30) -> Dict[str, Any]:
    """
    Pull conversion funnel data: page_view -> tool_used -> email_signup
    
    Args:
        days: Number of days to pull (default 30)
        
    Returns:
        Dictionary with funnel metrics per tool
    """
    if not GA4_AVAILABLE or not PROPERTY_ID:
        return {
            "success": False,
            "error": "GA4 not configured"
        }
    
    try:
        client = BetaAnalyticsDataClient()
        
        # Try with tool_name dimension first, fall back to eventName only
        has_tool_name = False
        tool_name_error = None
        
        try:
            request = RunReportRequest(
                property=f"properties/{PROPERTY_ID}",
                date_ranges=[DateRange(
                    start_date=f"{days}daysAgo",
                    end_date="today"
                )],
                dimensions=[
                    Dimension(name="eventName"),
                    Dimension(name="customEvent:tool_name"),
                ],
                metrics=[
                    Metric(name="eventCount"),
                ],
            )
            response = client.run_report(request)
            has_tool_name = True
        except Exception as e:
            error_str = str(e)
            # Check if this is the "dimension not valid" error
            if "not a valid dimension" in error_str or "customEvent:tool_name" in error_str:
                tool_name_error = (
                    "Custom dimension 'tool_name' not configured in GA4. "
                    "To fix: GA4 Admin > Custom definitions > Create custom dimension "
                    "with name 'tool_name', scope 'Event', and event parameter 'tool_name'. "
                    "See WORDPRESS_SETUP.md for detailed instructions."
                )
                logger.warning(f"tool_name dimension not configured: {tool_name_error}")
            else:
                logger.info(f"tool_name dimension query failed, falling back: {e}")
            
            # Fall back to eventName only
            request = RunReportRequest(
                property=f"properties/{PROPERTY_ID}",
                date_ranges=[DateRange(
                    start_date=f"{days}daysAgo",
                    end_date="today"
                )],
                dimensions=[
                    Dimension(name="eventName"),
                ],
                metrics=[
                    Metric(name="eventCount"),
                ],
            )
            response = client.run_report(request)
        
        # Build funnel data
        funnels: Dict[str, Dict[str, int]] = {}
        
        for row in response.rows:
            event_name = row.dimension_values[0].value
            if has_tool_name:
                tool_name = row.dimension_values[1].value or "unknown"
            else:
                tool_name = "all"
            count = int(row.metric_values[0].value)
            
            if tool_name not in funnels:
                funnels[tool_name] = {
                    "tool_used": 0,
                    "email_signup": 0,
                    "share_created": 0
                }
            
            if event_name in funnels[tool_name]:
                funnels[tool_name][event_name] = count
        
        # Calculate conversion rates
        for tool_name, data in funnels.items():
            tool_uses = data.get("tool_used", 0)
            if tool_uses > 0:
                data["email_conversion_rate"] = round(
                    (data.get("email_signup", 0) / tool_uses) * 100, 2
                )
                data["share_conversion_rate"] = round(
                    (data.get("share_created", 0) / tool_uses) * 100, 2
                )
            else:
                data["email_conversion_rate"] = 0
                data["share_conversion_rate"] = 0
        
        # Build result with helpful notes
        result = {
            "success": True,
            "period": f"last_{days}_days",
            "pulled_at": datetime.utcnow().isoformat() + "Z",
            "funnels": funnels,
        }
        
        if not has_tool_name:
            result["note"] = "Showing aggregate data only (not broken down by tool)."
            if tool_name_error:
                result["setup_required"] = tool_name_error
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to pull GA4 funnel: {e}")
        return {
            "success": False,
            "error": str(e)
        }

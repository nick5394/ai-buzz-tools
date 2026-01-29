"""
Shared utilities for all AI-Buzz tools.
Email subscription, data loading, formatting functions.
"""

import os
import json
import hashlib
import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

# Cache for JSON data files (loaded once at startup)
_data_cache: Dict[str, Any] = {}


def load_json_data(filename: str) -> Dict[str, Any]:
    """
    Load JSON data from data/ directory.
    Caches the data in memory for performance.
    
    Args:
        filename: Name of JSON file in data/ directory (e.g., "pricing_data.json")
    
    Returns:
        Dictionary containing the JSON data
    """
    global _data_cache
    
    if filename in _data_cache:
        return _data_cache[filename]
    
    data_path = os.path.join(os.path.dirname(__file__), "..", "data", filename)
    with open(data_path, "r", encoding="utf-8") as f:
        _data_cache[filename] = json.load(f)
    
    logger.info(f"Loaded {filename} successfully")
    return _data_cache[filename]


def subscribe_email(
    email: str,
    tool_name: str,
    interest_tags: List[str],
    success_message: str = "Successfully subscribed!"
) -> Dict[str, Any]:
    """
    Subscribe email to Mailchimp with tool-specific tags.
    
    Args:
        email: Email address to subscribe
        tool_name: Name of the tool (e.g., "pricing-calculator", "status-page")
        interest_tags: List of interest tags (e.g., ["interest:price-alerts"])
        success_message: Custom success message
    
    Returns:
        Dictionary with success, message, and mailchimp_synced keys
    """
    mailchimp_synced = False
    
    # Check for Mailchimp configuration
    mailchimp_api_key = os.getenv("MAILCHIMP_API_KEY")
    mailchimp_list_id = os.getenv("MAILCHIMP_LIST_ID")
    mailchimp_server = os.getenv("MAILCHIMP_SERVER_PREFIX", "us1")
    
    if mailchimp_api_key and mailchimp_list_id:
        try:
            import mailchimp_marketing as MailchimpMarketing
            
            client = MailchimpMarketing.Client()
            client.set_config({
                "api_key": mailchimp_api_key,
                "server": mailchimp_server
            })
            
            # Build tags: tool tag + interest tags
            tags = [f"tool:{tool_name}"] + interest_tags
            
            # Add or update subscriber with tags
            member_data = {
                "email_address": email,
                "status_if_new": "subscribed",
                "status": "subscribed",
                "tags": tags
            }
            
            # Use set_list_member for upsert behavior
            subscriber_hash = hashlib.md5(email.lower().encode()).hexdigest()
            
            client.lists.set_list_member(
                mailchimp_list_id,
                subscriber_hash,
                member_data
            )
            
            mailchimp_synced = True
            logger.info(f"Successfully subscribed {email} to Mailchimp with tags: {tags}")
            
        except Exception as e:
            logger.error(f"Mailchimp error for {email}: {str(e)}")
            # Continue without Mailchimp - still return success
            # The email was valid, we just couldn't sync to Mailchimp
    else:
        logger.warning("Mailchimp not configured - email subscription recorded but not synced")
    
    return {
        "success": True,
        "message": success_message,
        "mailchimp_synced": mailchimp_synced
    }


def format_currency(amount: float) -> str:
    """
    Format a currency amount for display.
    
    Args:
        amount: Amount in USD
    
    Returns:
        Formatted string (e.g., "$1,234.56" or "$0.0012")
    """
    if amount >= 1000:
        return "${:,.2f}".format(amount)
    elif amount >= 0.01:
        return f"${amount:.2f}"
    else:
        return f"${amount:.4f}"


def format_date(date_str: str) -> str:
    """
    Format a date string for display.
    
    Args:
        date_str: Date string in format "YYYY-MM-DD" or ISO format
    
    Returns:
        Formatted date string (e.g., "Jan 28, 2026")
    """
    if not date_str or date_str == "unknown":
        return "Unknown"
    
    try:
        # Try ISO format first
        if "T" in date_str:
            from datetime import datetime
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            return dt.strftime("%b %d, %Y")
        
        # Try YYYY-MM-DD format
        parts = date_str.split("-")
        if len(parts) == 3:
            from datetime import datetime
            dt = datetime(int(parts[0]), int(parts[1]), int(parts[2]))
            return dt.strftime("%b %d, %Y")
        
        return date_str
    except Exception:
        return date_str


def load_widget(filename: str) -> str:
    """
    Load widget HTML file from widgets/ directory.
    
    Args:
        filename: Name of HTML file in widgets/ directory (e.g., "pricing_calculator_widget.html")
    
    Returns:
        Widget HTML content as string
    
    Raises:
        FileNotFoundError: If widget file doesn't exist
    """
    widget_path = os.path.join(os.path.dirname(__file__), "..", "widgets", filename)
    with open(widget_path, "r", encoding="utf-8") as f:
        return f.read()

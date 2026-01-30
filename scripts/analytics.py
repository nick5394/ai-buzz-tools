#!/usr/bin/env python3
"""
Analytics CLI - Pull usage data and generate insights.

Usage:
    python scripts/analytics.py pull-stats          # Pull in-memory stats from production
    python scripts/analytics.py pull-ga4 --days 30  # Pull GA4 data
    python scripts/analytics.py gaps                # Show actionable gaps
    python scripts/analytics.py report              # Generate full insights report

Examples:
    # Check what patterns to add
    python scripts/analytics.py gaps
    
    # Pull all data before a deploy
    python scripts/analytics.py pull-stats
    
    # Generate weekly report
    python scripts/analytics.py report
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

import requests

# Configuration
PROD_URL = "https://ai-buzz-tools.onrender.com"
LOCAL_URL = "http://localhost:8000"
DATA_DIR = Path(__file__).parent.parent / "data" / "analytics"


def ensure_data_dir():
    """Create data directory if it doesn't exist."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def get_base_url(args) -> str:
    """Get API base URL based on args."""
    return LOCAL_URL if getattr(args, 'local', False) else PROD_URL


def pull_stats(args):
    """Pull in-memory stats from production or local."""
    base_url = get_base_url(args)
    print(f"Pulling stats from {base_url}/analytics/stats...")
    
    try:
        resp = requests.get(f"{base_url}/analytics/stats", timeout=30)
        resp.raise_for_status()
        data = resp.json()
        
        ensure_data_dir()
        filename = f"stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = DATA_DIR / filename
        
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
        
        print(f"\nSaved to {filepath}")
        print("\n" + "=" * 50)
        print("STATS SUMMARY")
        print("=" * 50)
        
        stats = data.get("data", {})
        
        # Error Decoder
        ed = stats.get("error_decoder", {})
        print(f"\nError Decoder:")
        print(f"  Total decodes: {ed.get('total', 0)}")
        print(f"  Matched: {ed.get('matched', 0)}")
        print(f"  Unmatched (gaps): {ed.get('unmatched', 0)}")
        
        # Pricing Calculator
        pc = stats.get("pricing_calculator", {})
        print(f"\nPricing Calculator:")
        print(f"  Total calculations: {pc.get('total', 0)}")
        buckets = pc.get("token_buckets", {})
        print(f"  Token distribution: {buckets}")
        
        # Status Page
        sp = stats.get("status_page", {})
        print(f"\nStatus Page:")
        print(f"  Total checks: {sp.get('total', 0)}")
        
    except requests.exceptions.ConnectionError:
        print(f"Error: Could not connect to {base_url}")
        print("Is the server running?" if "localhost" in base_url else "Is the service deployed?")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


def show_gaps(args):
    """Show actionable gaps from production or local."""
    base_url = get_base_url(args)
    print(f"Fetching gaps from {base_url}/analytics/gaps...")
    
    try:
        resp = requests.get(f"{base_url}/analytics/gaps", timeout=30)
        resp.raise_for_status()
        data = resp.json()
        
        print("\n" + "=" * 60)
        print("ACTIONABLE GAPS")
        print("=" * 60)
        
        print("\n📝 ERROR PATTERNS TO ADD")
        print("-" * 40)
        error_gaps = data.get("error_patterns_to_add", [])
        if error_gaps:
            for gap in error_gaps[:10]:
                print(f"  [{gap['count']:3}x] {gap['preview']}")
            print(f"\n  Add these patterns to data/error_patterns.json")
        else:
            print("  No gaps detected yet")
        
        print("\n💰 PRICING MODELS TO ADD")
        print("-" * 40)
        model_gaps = data.get("pricing_models_to_add", [])
        if model_gaps:
            for model in model_gaps[:10]:
                print(f"  [{model['searches']:3}x] {model['search_term']}")
            print(f"\n  Add these models to data/pricing_data.json")
        else:
            print("  No gaps detected yet")
        
        print("\n" + "=" * 60)
        
    except requests.exceptions.ConnectionError:
        print(f"Error: Could not connect to {base_url}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


def pull_ga4(args):
    """Pull GA4 data using the service."""
    print(f"Pulling GA4 data for last {args.days} days...")
    
    # Add project root to path for imports
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))
    
    try:
        from services.ga4 import pull_events, pull_traffic, pull_funnel, is_configured
        
        if not is_configured():
            print("\nGA4 is not configured. To set up:")
            print("1. Enable 'Google Analytics Data API' in Google Cloud Console")
            print("2. Create Service Account and download JSON key")
            print("3. Add service account email as Viewer in GA4 Admin")
            print("4. Set environment variables:")
            print("   export GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json")
            print("   export GA4_PROPERTY_ID=your-property-id")
            sys.exit(1)
        
        ensure_data_dir()
        
        events = pull_events(args.days)
        traffic = pull_traffic(args.days)
        funnel = pull_funnel(args.days)
        
        data = {
            "pulled_at": datetime.utcnow().isoformat() + "Z",
            "period_days": args.days,
            "events": events,
            "traffic": traffic,
            "funnel": funnel
        }
        
        filename = f"ga4_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = DATA_DIR / filename
        
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
        
        print(f"\nSaved to {filepath}")
        
        # Print summary
        print("\n" + "=" * 50)
        print("GA4 DATA SUMMARY")
        print("=" * 50)
        
        if events.get("success"):
            print("\nEvents:")
            for event_name, tools in events.get("events", {}).items():
                total = sum(tools.values())
                print(f"  {event_name}: {total}")
        else:
            print(f"\nEvents: {events.get('error', 'Unknown error')}")
        
        if funnel.get("success"):
            print("\nConversion Funnels:")
            for tool, data in funnel.get("funnels", {}).items():
                print(f"  {tool}:")
                print(f"    tool_used: {data.get('tool_used', 0)}")
                print(f"    email_signup: {data.get('email_signup', 0)} ({data.get('email_conversion_rate', 0)}%)")
        
    except ImportError as e:
        print(f"\nError: {e}")
        print("Run: pip install google-analytics-data")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


def generate_report(args):
    """Generate a full insights report."""
    base_url = get_base_url(args)
    print("Generating insights report...")
    
    # Pull fresh stats
    try:
        stats_resp = requests.get(f"{base_url}/analytics/stats", timeout=30)
        stats = stats_resp.json() if stats_resp.ok else {}
    except:
        stats = {}
    
    try:
        gaps_resp = requests.get(f"{base_url}/analytics/gaps", timeout=30)
        gaps = gaps_resp.json() if gaps_resp.ok else {}
    except:
        gaps = {}
    
    # Generate markdown report
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    stats_data = stats.get("data", {})
    
    ed = stats_data.get("error_decoder", {})
    pc = stats_data.get("pricing_calculator", {})
    sp = stats_data.get("status_page", {})
    
    report = f"""# Usage Insights Report

Generated: {now}
Data source: {base_url}

## Summary

| Tool | Total Uses | Key Metric |
|------|------------|------------|
| Error Decoder | {ed.get('total', 'N/A')} | {ed.get('unmatched', 0)} unmatched |
| Pricing Calculator | {pc.get('total', 'N/A')} | {len(pc.get('models_not_found', {}))} models not found |
| Status Page | {sp.get('total', 'N/A')} | {len(sp.get('by_provider', {}))} providers checked |

## Token Usage Distribution (Pricing Calculator)

"""
    buckets = pc.get("token_buckets", {})
    for bucket, count in buckets.items():
        report += f"- **{bucket}**: {count} calculations\n"
    
    report += """
## Actionable Gaps

### Error Patterns to Add

These errors were searched but didn't match any pattern. Add them to `data/error_patterns.json`:

"""
    error_gaps = gaps.get("error_patterns_to_add", [])
    if error_gaps:
        for gap in error_gaps[:10]:
            report += f"- **{gap['count']}x**: `{gap['preview']}`\n"
    else:
        report += "No gaps detected yet.\n"
    
    report += """
### Pricing Models to Add

These models were searched but not found. Add them to `data/pricing_data.json`:

"""
    model_gaps = gaps.get("pricing_models_to_add", [])
    if model_gaps:
        for model in model_gaps[:10]:
            report += f"- **{model['searches']}x**: {model['search_term']}\n"
    else:
        report += "No gaps detected yet.\n"
    
    report += """
## Provider Popularity (Status Page)

"""
    providers = sp.get("by_provider", {})
    if providers:
        sorted_providers = sorted(providers.items(), key=lambda x: x[1], reverse=True)
        for provider, count in sorted_providers:
            report += f"- **{provider}**: {count} checks\n"
    else:
        report += "No data yet.\n"
    
    report += f"""
---

*Report generated from in-memory stats. Stats reset on deploy.*
*For historical data, run: `python scripts/analytics.py pull-ga4`*
"""
    
    # Save report
    ensure_data_dir()
    report_path = DATA_DIR / "latest_report.md"
    with open(report_path, "w") as f:
        f.write(report)
    
    print(f"\nReport saved to {report_path}")
    print("\n" + report)


def main():
    parser = argparse.ArgumentParser(
        description="Analytics CLI - Pull usage data and generate insights",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/analytics.py gaps                  # See what to build next
  python scripts/analytics.py pull-stats            # Save current stats
  python scripts/analytics.py pull-ga4 --days 30    # Pull GA4 data
  python scripts/analytics.py report                # Generate full report
  python scripts/analytics.py gaps --local          # Check local dev server
        """
    )
    
    parser.add_argument(
        "--local", "-l",
        action="store_true",
        help="Use local server (localhost:8000) instead of production"
    )
    
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # pull-stats command
    pull_stats_parser = subparsers.add_parser(
        "pull-stats",
        help="Pull in-memory stats and save to data/analytics/"
    )
    pull_stats_parser.add_argument("--local", "-l", action="store_true")
    
    # gaps command
    gaps_parser = subparsers.add_parser(
        "gaps",
        help="Show actionable gaps (what to build next)"
    )
    gaps_parser.add_argument("--local", "-l", action="store_true")
    
    # pull-ga4 command
    ga4_parser = subparsers.add_parser(
        "pull-ga4",
        help="Pull GA4 data and save to data/analytics/"
    )
    ga4_parser.add_argument(
        "--days", "-d",
        type=int,
        default=30,
        help="Number of days to pull (default: 30)"
    )
    
    # report command
    report_parser = subparsers.add_parser(
        "report",
        help="Generate full insights report"
    )
    report_parser.add_argument("--local", "-l", action="store_true")
    
    args = parser.parse_args()
    
    commands = {
        "pull-stats": pull_stats,
        "gaps": show_gaps,
        "pull-ga4": pull_ga4,
        "report": generate_report,
    }
    
    commands[args.command](args)


if __name__ == "__main__":
    main()

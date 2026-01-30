#!/usr/bin/env python3
"""
Take screenshots/PDFs of WordPress pages for verification.

Usage:
    python scripts/screenshot_pages.py                    # Capture all pages as PDF
    python scripts/screenshot_pages.py --slug ai-status   # Capture single page
    python scripts/screenshot_pages.py --all --format segments --clean  # Fresh segmented screenshots
    python scripts/screenshot_pages.py --list             # Show available pages
    python scripts/screenshot_pages.py --headed           # Debug with visible browser

Options:
    --slug SLUG    Capture specific page
    --all          Capture all pages (default if no --slug)
    --format       pdf (default), png, both, or segments
    --mobile       Use mobile viewport (375x667)
    --clean        Remove existing screenshots first
    --headed       Show browser window (for debugging)
    --list         List available page slugs and exit
"""
import argparse
import sys
import asyncio
from pathlib import Path
from typing import List, Optional, Tuple

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("Error: playwright not installed. Install with: pip install playwright && playwright install chromium")
    sys.exit(1)


# Tool pages (WordPress Pages with widgets)
TOOL_PAGES = {
    "ai-pricing-calculator": "https://www.ai-buzz.com/ai-pricing-calculator",
    "ai-status": "https://www.ai-buzz.com/ai-status",
    "ai-error-decoder": "https://www.ai-buzz.com/ai-error-decoder",
    "ai-tools": "https://www.ai-buzz.com/ai-tools",
}

# Guide pages (WordPress Posts)
GUIDE_PAGES = {
    "ai-openai-429-errors": "https://www.ai-buzz.com/ai-openai-429-errors",
    "ai-openai-rate-limits": "https://www.ai-buzz.com/ai-openai-rate-limits",
    "ai-openai-vs-anthropic-pricing": "https://www.ai-buzz.com/ai-openai-vs-anthropic-pricing",
    "ai-openai-errors": "https://www.ai-buzz.com/ai-openai-errors",
}

# Combined for backwards compatibility
PAGES = {**TOOL_PAGES, **GUIDE_PAGES}

SCREENSHOT_DIR = Path("screenshots")


async def wait_for_widgets(page, slug: str):
    """Wait for widgets to fully load using optimized strategy.
    
    Args:
        page: Playwright page object
        slug: Page slug to determine which widget to wait for
    """
    # Widget-specific selectors (optimized - try most specific first)
    widget_selectors = {
        "ai-pricing-calculator": "#pricing-calculator-widget",
        "ai-status": "#status-page-widget",
        "ai-error-decoder": "#error-decoder-widget",
        "ai-openai-errors": "#error-decoder-widget",
        "ai-openai-vs-anthropic-pricing": "#pricing-calculator-widget",
        "ai-is-openai-down": "#status-page-widget",
        "ai-tools": None,  # Landing page, no widget
        "ai-openai-429-errors": "#error-decoder-widget",
        "ai-openai-rate-limits": None,  # Content page, no widget
    }
    
    selector = widget_selectors.get(slug)
    if not selector:
        # No widget to wait for
        await page.wait_for_timeout(1000)  # Brief pause for page render
        return
    
    # Wait for widget container (25s timeout - covers cold starts without being excessive)
    try:
        await page.wait_for_selector(selector, timeout=25000, state="attached")
        print(f"    ✓ Widget loaded: {selector}")
        # Brief pause for widget to initialize
        await page.wait_for_timeout(1500)
    except Exception as e:
        print(f"    ⚠ Widget may not be loaded: {e}")
        # Continue anyway - widget might still render
    
    # Scroll to ensure widget is in viewport
    try:
        await page.evaluate(f"document.querySelector('{selector}')?.scrollIntoView({{behavior: 'instant', block: 'center'}})")
        await page.wait_for_timeout(500)
    except:
        pass


async def interact_with_widget(page, slug: str):
    """Interact with widget to show active state before capturing (optimized - faster).
    
    Args:
        page: Playwright page object
        slug: Page slug to determine which widget interaction to perform
    """
    # Skip interaction for landing page
    if slug == "ai-tools":
        await page.wait_for_timeout(500)
        return
    
    try:
        # Quick interactions - just verify widget is functional, don't wait for full results
        if slug in ("ai-pricing-calculator", "ai-openai-vs-anthropic-pricing"):
            calculate_btn = page.locator("#pcw-calculate-btn")
            if await calculate_btn.is_visible(timeout=3000):
                await calculate_btn.click()
                print("    ✓ Triggered calculation")
                # Brief wait for API call to start (don't wait for full results)
                await page.wait_for_timeout(1500)
        
        elif slug in ("ai-error-decoder", "ai-openai-errors", "ai-openai-429-errors"):
            textarea = page.locator("#edw-error-textarea")
            if await textarea.is_visible(timeout=3000):
                await textarea.fill("rate limit exceeded")
                decode_btn = page.locator("#edw-decode-btn")
                if await decode_btn.is_visible(timeout=2000):
                    await decode_btn.click()
                    print("    ✓ Triggered decode")
                    # Brief wait for API call to start
                    await page.wait_for_timeout(1500)
        
        elif slug in ("ai-status", "ai-is-openai-down"):
            # Status page auto-loads, just wait briefly for cards
            try:
                await page.wait_for_selector(".spw-provider-card", timeout=5000, state="attached")
                print("    ✓ Status cards visible")
            except:
                pass
            await page.wait_for_timeout(1000)
        
    except Exception as e:
        # Continue anyway - widget might still be visible
        pass


async def capture_page(
    url: str,
    slug: str,
    output_dir: Path,
    format: str = "pdf",
    mobile: bool = False,
    browser = None,
    headless: bool = True
) -> Tuple[bool, List[Path]]:
    """Capture page as PDF or PNG with optional mobile viewport.
    
    Args:
        url: Page URL to capture
        slug: Page slug for filename
        output_dir: Directory to save output
        format: "pdf", "png", or "both"
        mobile: If True, use mobile viewport (375x667)
        browser: Optional browser instance to reuse
        headless: If True, run browser in headless mode (default True)
    
    Returns:
        Tuple of (success: bool, output_paths: List[Path])
    """
    viewport = {"width": 375, "height": 667} if mobile else {"width": 1920, "height": 1080}
    suffix = "-mobile" if mobile else "-desktop"
    viewport_label = "mobile" if mobile else "desktop"
    
    print(f"📸 Capturing {slug} ({viewport_label})...")
    
    # Reuse browser if provided, otherwise create new one
    if browser is None:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=headless)
            return await _capture_with_browser(browser, url, slug, output_dir, format, mobile, suffix, viewport)
    else:
        return await _capture_with_browser(browser, url, slug, output_dir, format, mobile, suffix, viewport)


async def _capture_with_browser(
    browser,
    url: str,
    slug: str,
    output_dir: Path,
    format: str,
    mobile: bool,
    suffix: str,
    viewport: dict
) -> Tuple[bool, List[Path]]:
    """Internal helper to capture page with an existing browser."""
    context = await browser.new_context(
        viewport=viewport,
        device_scale_factor=2 if not mobile else 1,
    )
    page = await context.new_page()
    
    output_paths = []
    
    try:
        # Navigate to page (optimized - use domcontentloaded for faster initial load)
        print(f"  Loading {url}...")
        await page.goto(url, wait_until="domcontentloaded", timeout=40000)
        
        # Wait for widgets to load (optimized strategy)
        await wait_for_widgets(page, slug)
        
        # Quick interaction to show active state (optional, fast)
        await interact_with_widget(page, slug)
        
        # Capture based on format
        if format in ("pdf", "both"):
            pdf_path = output_dir / f"{slug}{suffix}.pdf"
            overwriting = pdf_path.exists()
            await page.pdf(
                path=str(pdf_path),
                format="A4",
                print_background=True,
                margin={"top": "0.5cm", "right": "0.5cm", "bottom": "0.5cm", "left": "0.5cm"}
            )
            output_paths.append(pdf_path)
            action = "Overwrote" if overwriting else "Saved"
            print(f"  ✓ {action} PDF: {pdf_path}")
        
        if format in ("png", "both"):
            png_path = output_dir / f"{slug}{suffix}.png"
            overwriting = png_path.exists()
            await page.screenshot(
                path=str(png_path),
                full_page=True,
                animations="disabled"
            )
            output_paths.append(png_path)
            action = "Overwrote" if overwriting else "Saved"
            print(f"  ✓ {action} PNG: {png_path}")
        
        return True, output_paths
        
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False, output_paths
    finally:
        await context.close()


async def capture_page_segments(
    page,
    slug: str,
    output_dir: Path
) -> List[Path]:
    """Capture viewport-sized screenshot segments of a page.
    
    Takes multiple 1920x1080 screenshots at different scroll positions,
    with overlap to ensure complete coverage.
    
    Args:
        page: Playwright page object (already navigated to the URL)
        slug: Page slug for filename prefix
        output_dir: Directory to save output
    
    Returns:
        List of output paths for all segments
    """
    output_paths = []
    
    # Get total page height
    total_height = await page.evaluate("document.body.scrollHeight")
    viewport_height = 1080
    overlap = 180
    scroll_step = viewport_height - overlap  # 900px
    
    # Calculate number of segments needed
    segment_count = 1
    current_scroll = 0
    
    while current_scroll < total_height:
        # Scroll to position
        await page.evaluate(f"window.scrollTo(0, {current_scroll})")
        
        # Wait for page to settle after scroll
        await page.wait_for_timeout(300)
        
        # Generate filename with zero-padded segment number
        filename = f"{slug}-{segment_count:03d}.png"
        output_path = output_dir / filename
        overwriting = output_path.exists()
        
        # Take screenshot of current viewport
        await page.screenshot(
            path=str(output_path),
            full_page=False,  # Only capture visible viewport
            animations="disabled"
        )
        
        output_paths.append(output_path)
        action = "Overwrote" if overwriting else "Captured"
        print(f"    ✓ {action} segment {segment_count}: {filename}")
        
        # Move to next position
        current_scroll += scroll_step
        segment_count += 1
        
        # Safety check - don't create more than 50 segments per page
        if segment_count > 50:
            print(f"    ⚠ Reached maximum segment limit (50)")
            break
    
    return output_paths


async def capture_all_segments(output_dir: Optional[Path] = None, headless: bool = True):
    """Capture segmented screenshots for all pages.
    
    Args:
        output_dir: Directory to save output (defaults to SCREENSHOT_DIR)
        headless: If True, run browser in headless mode (default True)
    """
    if output_dir is None:
        output_dir = SCREENSHOT_DIR
    
    output_dir.mkdir(exist_ok=True)
    
    print("=== Segmented Screenshot Capture ===\n")
    print("Viewport: 1920x1080, Overlap: 180px\n")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        
        results = []
        for slug, url in PAGES.items():
            print(f"📸 Capturing segments for {slug}...")
            
            # Create context with desktop viewport
            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
                device_scale_factor=2,
            )
            page = await context.new_page()
            
            try:
                # Navigate to page
                print(f"  Loading {url}...")
                await page.goto(url, wait_until="domcontentloaded", timeout=40000)
                
                # Wait for widgets to load
                await wait_for_widgets(page, slug)
                
                # Interact with widget to show active state
                await interact_with_widget(page, slug)
                
                # Scroll back to top before capturing segments
                await page.evaluate("window.scrollTo(0, 0)")
                await page.wait_for_timeout(300)
                
                # Capture segments
                paths = await capture_page_segments(page, slug, output_dir)
                results.append((slug, True, paths))
                print(f"  ✓ Captured {len(paths)} segment(s)\n")
                
            except Exception as e:
                print(f"  ✗ Error: {e}\n")
                results.append((slug, False, []))
            finally:
                await context.close()
        
        await browser.close()
    
    # Summary
    print("=== Summary ===")
    successful = [(s, p) for s, success, p in results if success]
    failed = [s for s, success, _ in results if not success]
    
    total_segments = sum(len(p) for _, p in successful)
    
    if successful:
        print(f"✓ Successfully captured {len(successful)} page(s) ({total_segments} total segments):")
        for slug, paths in successful:
            print(f"  - {slug}: {len(paths)} segment(s)")
    
    if failed:
        print(f"\n✗ Failed to capture {len(failed)} page(s):")
        for slug in failed:
            print(f"  - {slug}")
    
    print(f"\nSegments saved to: {output_dir.absolute()}")


async def capture_all(format: str = "pdf", mobile: bool = False, headless: bool = True):
    """Capture all pages (optimized - reuses browser)."""
    SCREENSHOT_DIR.mkdir(exist_ok=True)
    
    print("=== WordPress Page Verification ===\n")
    
    # Reuse browser across all pages for faster execution
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        
        results = []
        for slug, url in PAGES.items():
            success, paths = await capture_page(url, slug, SCREENSHOT_DIR, format, mobile, browser)
            results.append((slug, success, paths))
            print()
        
        await browser.close()
    
    # Summary
    print("=== Summary ===")
    successful = [(s, p) for s, success, p in results if success]
    failed = [s for s, success, _ in results if not success]
    
    if successful:
        print(f"✓ Successfully captured {len(successful)} page(s):")
        for slug, paths in successful:
            print(f"  - {slug}")
            for path in paths:
                print(f"    → {path}")
    
    if failed:
        print(f"\n✗ Failed to capture {len(failed)} page(s):")
        for slug in failed:
            print(f"  - {slug}")
    
    print(f"\nScreenshots saved to: {SCREENSHOT_DIR.absolute()}")


async def capture_one(slug: str, format: str = "pdf", mobile: bool = False, headless: bool = True):
    """Capture a single page."""
    if slug not in PAGES:
        print(f"Error: Unknown slug '{slug}'")
        print(f"Available slugs: {', '.join(PAGES.keys())}")
        return 1
    
    SCREENSHOT_DIR.mkdir(exist_ok=True)
    url = PAGES[slug]
    
    success, paths = await capture_page(url, slug, SCREENSHOT_DIR, format, mobile, browser=None, headless=headless)
    return 0 if success else 1


# Legacy function names for backward compatibility
async def take_screenshot(url: str, slug: str, output_dir: Path):
    """Legacy function - takes PNG screenshot (backward compatibility)."""
    success, _ = await capture_page(url, slug, output_dir, format="png", mobile=False)
    return success


async def screenshot_all():
    """Legacy function - takes PNG screenshots of all pages."""
    await capture_all(format="png", mobile=False)


async def screenshot_one(slug: str):
    """Legacy function - takes PNG screenshot of single page."""
    return await capture_one(slug, format="png", mobile=False)


def clean_screenshot_dir(output_dir: Path):
    """Remove all existing screenshots from output directory.
    
    Args:
        output_dir: Directory to clean
    """
    if not output_dir.exists():
        return
    
    removed = 0
    for ext in ("*.pdf", "*.png"):
        for f in output_dir.glob(ext):
            f.unlink()
            removed += 1
    
    if removed > 0:
        print(f"🧹 Cleaned {removed} existing file(s) from {output_dir}")


def main():
    parser = argparse.ArgumentParser(description="Take screenshots/PDFs of WordPress pages")
    parser.add_argument(
        "--slug",
        help="Take screenshot of specific page slug",
        choices=list(PAGES.keys())
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Take screenshots of all pages"
    )
    parser.add_argument(
        "--format",
        choices=["pdf", "png", "both", "segments"],
        default="pdf",
        help="Output format: pdf (default), png, both, or segments (viewport-sized PNGs)"
    )
    parser.add_argument(
        "--mobile",
        action="store_true",
        help="Capture mobile viewport (375x667) instead of desktop"
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Remove existing screenshots before capturing"
    )
    parser.add_argument(
        "--headed",
        action="store_true",
        help="Run with visible browser (for debugging)"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available page slugs and exit"
    )
    
    args = parser.parse_args()
    
    # Handle --list
    if args.list:
        print("Available page slugs:")
        for slug, url in PAGES.items():
            print(f"  {slug}: {url}")
        return 0
    
    # Handle --clean
    if args.clean:
        clean_screenshot_dir(SCREENSHOT_DIR)
    
    # Handle capture modes
    headless = not args.headed
    
    if args.format == "segments":
        # Segments format captures all pages with viewport-sized screenshots
        if args.mobile:
            print("Warning: --mobile is ignored for segments format (uses 1920x1080)")
        asyncio.run(capture_all_segments(headless=headless))
        return 0
    elif args.all:
        asyncio.run(capture_all(format=args.format, mobile=args.mobile, headless=headless))
        return 0
    elif args.slug:
        return asyncio.run(capture_one(args.slug, format=args.format, mobile=args.mobile, headless=headless))
    else:
        # Default: capture all
        asyncio.run(capture_all(format=args.format, mobile=args.mobile, headless=headless))
        return 0


if __name__ == "__main__":
    sys.exit(main())

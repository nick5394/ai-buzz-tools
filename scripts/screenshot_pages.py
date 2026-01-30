#!/usr/bin/env python3
"""
Take screenshots/PDFs of WordPress pages for verification.

Usage:
    python scripts/screenshot_pages.py
    python scripts/screenshot_pages.py --slug ai-pricing-calculator
    python scripts/screenshot_pages.py --all --format pdf --mobile
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


PAGES = {
    "ai-pricing-calculator": "https://www.ai-buzz.com/ai-pricing-calculator",
    "ai-status": "https://www.ai-buzz.com/ai-status",
    "ai-error-decoder": "https://www.ai-buzz.com/ai-error-decoder",
    "ai-openai-errors": "https://www.ai-buzz.com/ai-openai-errors",
    "ai-openai-vs-anthropic-pricing": "https://www.ai-buzz.com/ai-openai-vs-anthropic-pricing",
    "ai-is-openai-down": "https://www.ai-buzz.com/ai-is-openai-down",
    "ai-tools": "https://www.ai-buzz.com/ai-tools",
}

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
        
        elif slug in ("ai-error-decoder", "ai-openai-errors"):
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
    browser = None
) -> Tuple[bool, List[Path]]:
    """Capture page as PDF or PNG with optional mobile viewport.
    
    Args:
        url: Page URL to capture
        slug: Page slug for filename
        output_dir: Directory to save output
        format: "pdf", "png", or "both"
        mobile: If True, use mobile viewport (375x667)
        browser: Optional browser instance to reuse
    
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
            browser = await p.chromium.launch(headless=True)
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
            await page.pdf(
                path=str(pdf_path),
                format="A4",
                print_background=True,
                margin={"top": "0.5cm", "right": "0.5cm", "bottom": "0.5cm", "left": "0.5cm"}
            )
            output_paths.append(pdf_path)
            print(f"  ✓ PDF saved to {pdf_path}")
        
        if format in ("png", "both"):
            png_path = output_dir / f"{slug}{suffix}.png"
            await page.screenshot(
                path=str(png_path),
                full_page=True,
                animations="disabled"
            )
            output_paths.append(png_path)
            print(f"  ✓ PNG saved to {png_path}")
        
        return True, output_paths
        
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False, output_paths
    finally:
        await context.close()


async def capture_all(format: str = "pdf", mobile: bool = False):
    """Capture all pages (optimized - reuses browser)."""
    SCREENSHOT_DIR.mkdir(exist_ok=True)
    
    print("=== WordPress Page Verification ===\n")
    
    # Reuse browser across all pages for faster execution
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
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


async def capture_one(slug: str, format: str = "pdf", mobile: bool = False):
    """Capture a single page."""
    if slug not in PAGES:
        print(f"Error: Unknown slug '{slug}'")
        print(f"Available slugs: {', '.join(PAGES.keys())}")
        return 1
    
    SCREENSHOT_DIR.mkdir(exist_ok=True)
    url = PAGES[slug]
    
    success, paths = await capture_page(url, slug, SCREENSHOT_DIR, format, mobile, browser=None)
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


async def screenshot_all():
    """Take screenshots of all pages."""
    SCREENSHOT_DIR.mkdir(exist_ok=True)
    
    print("=== WordPress Page Screenshots ===\n")
    
    results = []
    for slug, url in PAGES.items():
        success = await take_screenshot(url, slug, SCREENSHOT_DIR)
        results.append((slug, success))
        print()
    
    # Summary
    print("=== Summary ===")
    successful = [s for s, success in results if success]
    failed = [s for s, success in results if not success]
    
    if successful:
        print(f"✓ Successfully captured {len(successful)} page(s):")
        for slug in successful:
            print(f"  - {slug}")
    
    if failed:
        print(f"\n✗ Failed to capture {len(failed)} page(s):")
        for slug in failed:
            print(f"  - {slug}")
    
    print(f"\nScreenshots saved to: {SCREENSHOT_DIR.absolute()}")


async def screenshot_one(slug: str):
    """Take screenshot of a single page."""
    if slug not in PAGES:
        print(f"Error: Unknown slug '{slug}'")
        print(f"Available slugs: {', '.join(PAGES.keys())}")
        return 1
    
    SCREENSHOT_DIR.mkdir(exist_ok=True)
    url = PAGES[slug]
    
    success = await take_screenshot(url, slug, SCREENSHOT_DIR)
    return 0 if success else 1


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
        choices=["pdf", "png", "both"],
        default="pdf",
        help="Output format: pdf (default), png, or both"
    )
    parser.add_argument(
        "--mobile",
        action="store_true",
        help="Capture mobile viewport (375x667) instead of desktop"
    )
    
    args = parser.parse_args()
    
    if args.all:
        asyncio.run(capture_all(format=args.format, mobile=args.mobile))
        return 0
    elif args.slug:
        return asyncio.run(capture_one(args.slug, format=args.format, mobile=args.mobile))
    else:
        # Default: capture all
        asyncio.run(capture_all(format=args.format, mobile=args.mobile))
        return 0


if __name__ == "__main__":
    sys.exit(main())

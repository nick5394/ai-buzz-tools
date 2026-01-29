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
}

SCREENSHOT_DIR = Path("screenshots")


async def wait_for_widgets(page, slug: str):
    """Wait for widgets to fully load using improved strategy.
    
    Args:
        page: Playwright page object
        slug: Page slug to determine which widget to wait for
    """
    # 1. Wait for network idle (already done by goto, but ensure)
    try:
        await page.wait_for_load_state("networkidle", timeout=10000)
    except:
        pass  # May already be idle
    
    # 2. Wait for widget container (tool-specific selectors with longer timeout for cold starts)
    widget_selectors = {
        "ai-pricing-calculator": ["#pricing-calculator-widget", "#pcw-calculate-btn"],
        "ai-status": ["#status-page-widget", ".spw-provider-card"],
        "ai-error-decoder": ["#error-decoder-widget", "#edw-error-textarea"],
    }
    
    # Try slug-specific selectors first, then fallback to generic
    selectors_to_try = widget_selectors.get(slug, []) + [
        "#pricing-calculator-widget",
        "#status-page-widget", 
        "#error-decoder-widget",
        "[id*='widget']",
        "[class*='widget']",
    ]
    
    widget_found = False
    for selector in selectors_to_try:
        try:
            # Longer timeout to handle Render cold starts (up to 30s)
            await page.wait_for_selector(selector, timeout=35000)
            widget_found = True
            print(f"    ✓ Found widget: {selector}")
            break
        except:
            continue  # Try next selector
    
    if not widget_found:
        print(f"    ⚠ Widget container not found (may still be loading)")
    
    # 3. Scroll to bottom (trigger lazy loading)
    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    await page.wait_for_timeout(1000)  # Brief pause after scroll
    
    # 4. Additional wait for any async widget loading (PHP file_get_contents + Render cold start)
    await page.wait_for_timeout(5000)  # Give extra time for widget HTML to load


async def interact_with_widget(page, slug: str):
    """Interact with widget to show active state before capturing.
    
    Args:
        page: Playwright page object
        slug: Page slug to determine which widget interaction to perform
    """
    print(f"  Interacting with {slug} widget...")
    
    try:
        if slug == "ai-pricing-calculator":
            # Wait for pricing calculator widget to be visible (longer timeout for cold starts)
            try:
                await page.wait_for_selector("#pricing-calculator-widget", timeout=35000)
            except:
                # Try alternative selectors
                try:
                    await page.wait_for_selector("#pcw-calculate-btn", timeout=10000)
                except:
                    print("    ⚠ Widget may not be fully loaded")
            
            # Scroll widget into view
            await page.evaluate("document.getElementById('pricing-calculator-widget')?.scrollIntoView({behavior: 'smooth', block: 'center'})")
            await page.wait_for_timeout(1000)
            
            # Click "Calculate Costs" button
            calculate_btn = page.locator("#pcw-calculate-btn")
            if await calculate_btn.is_visible():
                await calculate_btn.click()
                print("    ✓ Clicked 'Calculate Costs' button")
                
                # Wait for results to appear (either results section or error)
                try:
                    # Wait for results table or cards to appear
                    await page.wait_for_selector("#pcw-results.visible, #pcw-results-table, #pcw-results-cards", timeout=30000)
                    print("    ✓ Results loaded")
                except:
                    # Check if error appeared instead
                    error_visible = await page.locator("#pcw-error.visible").is_visible()
                    if error_visible:
                        print("    ⚠ Error message displayed (widget still functional)")
                    else:
                        print("    ⚠ Results may not have loaded (continuing anyway)")
                
                # Wait a bit more for any animations/rendering
                await page.wait_for_timeout(2000)
            else:
                print("    ⚠ Calculate button not found")
        
        elif slug == "ai-status":
            # Status page auto-refreshes, just wait for status cards (longer timeout for cold starts)
            try:
                await page.wait_for_selector("#status-page-widget", timeout=35000)
            except:
                # Try alternative selectors
                try:
                    await page.wait_for_selector(".spw-provider-card", timeout=10000)
                except:
                    print("    ⚠ Widget may not be fully loaded")
            
            # Scroll widget into view
            await page.evaluate("document.getElementById('status-page-widget')?.scrollIntoView({behavior: 'smooth', block: 'center'})")
            await page.wait_for_timeout(1000)
            
            # Wait for provider status cards to appear
            try:
                await page.wait_for_selector(".spw-provider-card, .spw-status-card", timeout=30000)
                print("    ✓ Status cards loaded")
            except:
                print("    ⚠ Status cards may not have loaded (continuing anyway)")
            
            # Wait for any auto-refresh to complete
            await page.wait_for_timeout(3000)
        
        elif slug == "ai-error-decoder":
            # Wait for error decoder widget to be visible (longer timeout for cold starts)
            try:
                await page.wait_for_selector("#error-decoder-widget", timeout=35000)
            except:
                # Try alternative selectors
                try:
                    await page.wait_for_selector("#edw-error-textarea", timeout=10000)
                except:
                    print("    ⚠ Widget may not be fully loaded")
            
            # Scroll widget into view
            await page.evaluate("document.getElementById('error-decoder-widget')?.scrollIntoView({behavior: 'smooth', block: 'center'})")
            await page.wait_for_timeout(1000)
            
            # Enter a test error message
            textarea = page.locator("#edw-error-textarea")
            if await textarea.is_visible():
                await textarea.fill("rate limit exceeded")
                print("    ✓ Entered test error message")
                
                # Click decode button
                decode_btn = page.locator("#edw-decode-btn")
                if await decode_btn.is_visible():
                    await decode_btn.click()
                    print("    ✓ Clicked 'Decode Error' button")
                    
                    # Wait for explanation to appear
                    try:
                        await page.wait_for_selector("#edw-explanation.visible, .edw-explanation-section.visible", timeout=30000)
                        print("    ✓ Explanation loaded")
                    except:
                        # Check if error appeared instead
                        error_visible = await page.locator("#edw-error.visible").is_visible()
                        if error_visible:
                            print("    ⚠ Error message displayed (widget still functional)")
                        else:
                            print("    ⚠ Explanation may not have loaded (continuing anyway)")
                    
                    # Wait a bit more for any animations/rendering
                    await page.wait_for_timeout(2000)
                else:
                    print("    ⚠ Decode button not found")
            else:
                print("    ⚠ Textarea not found")
        
    except Exception as e:
        print(f"    ⚠ Interaction error (continuing anyway): {e}")
        # Continue anyway - widget might still be visible


async def capture_page(
    url: str,
    slug: str,
    output_dir: Path,
    format: str = "pdf",
    mobile: bool = False
) -> Tuple[bool, List[Path]]:
    """Capture page as PDF or PNG with optional mobile viewport.
    
    Args:
        url: Page URL to capture
        slug: Page slug for filename
        output_dir: Directory to save output
        format: "pdf", "png", or "both"
        mobile: If True, use mobile viewport (375x667)
    
    Returns:
        Tuple of (success: bool, output_paths: List[Path])
    """
    async with async_playwright() as p:
        viewport = {"width": 375, "height": 667} if mobile else {"width": 1920, "height": 1080}
        suffix = "-mobile" if mobile else "-desktop"
        viewport_label = "mobile" if mobile else "desktop"
        
        print(f"📸 Capturing {slug} ({viewport_label})...")
        
        # Launch browser
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport=viewport,
            device_scale_factor=2 if not mobile else 1,  # Higher quality for desktop
        )
        page = await context.new_page()
        
        output_paths = []
        
        try:
            # Navigate to page
            print(f"  Loading {url}...")
            await page.goto(url, wait_until="networkidle", timeout=60000)  # Longer timeout for cold starts
            
            # Wait for widgets to load (with slug-specific strategy)
            await wait_for_widgets(page, slug)
            
            # Interact with widget to show active state
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
            await browser.close()


async def capture_all(format: str = "pdf", mobile: bool = False):
    """Capture all pages."""
    SCREENSHOT_DIR.mkdir(exist_ok=True)
    
    print("=== WordPress Page Verification ===\n")
    
    results = []
    for slug, url in PAGES.items():
        success, paths = await capture_page(url, slug, SCREENSHOT_DIR, format, mobile)
        results.append((slug, success, paths))
        print()
    
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
    
    success, paths = await capture_page(url, slug, SCREENSHOT_DIR, format, mobile)
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

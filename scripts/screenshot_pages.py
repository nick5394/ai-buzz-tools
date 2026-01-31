#!/usr/bin/env python3
"""
Take screenshots/PDFs of WordPress pages for LLM visual analysis.

PURPOSE:
    Captures WordPress pages so an LLM can visually analyze what readers see -
    layout, widget rendering, interactive states. Raw HTML files provide text
    content; these screenshots show the final rendered output.

Usage:
    python scripts/screenshot_pages.py                    # Capture all pages as PDF
    python scripts/screenshot_pages.py --slug ai-status   # Capture single page
    python scripts/screenshot_pages.py --format segments --jpeg  # LLM-optimized capture
    python scripts/screenshot_pages.py --all --format segments --clean  # Fresh segmented screenshots
    python scripts/screenshot_pages.py --list             # Show available pages
    python scripts/screenshot_pages.py --headed           # Debug with visible browser

Options:
    --slug SLUG    Capture specific page
    --all          Capture all pages (default if no --slug)
    --format       pdf (default), png, both, or segments
    --jpeg         Use JPEG format (smaller files, recommended for LLM analysis)
    --compact      Lower resolution mode (1440x900 at 1.5x scale, opt-in)
    --mobile       Use mobile viewport (375x667)
    --clean        Remove existing screenshots first
    --headed       Show browser window (for debugging)
    --parallel N   Concurrency level for parallel capture (default: 3)
    --list         List available page slugs and exit

Recommended for LLM visual analysis:
    python scripts/screenshot_pages.py --format segments --jpeg
"""
import argparse
import sys
import asyncio
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any

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
    "ai-is-openai-down": "https://www.ai-buzz.com/ai-is-openai-down",
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
        await page.wait_for_timeout(500)  # Brief pause for page render
        return
    
    # Wait for widget container (25s timeout - covers cold starts without being excessive)
    try:
        await page.wait_for_selector(selector, timeout=25000, state="attached")
        print(f"    ✓ Widget loaded: {selector}")
        # Brief pause for widget to initialize
        await page.wait_for_timeout(750)
    except Exception as e:
        print(f"    ⚠ Widget may not be loaded: {e}")
        # Continue anyway - widget might still render
    
    # Scroll to ensure widget is in viewport
    try:
        await page.evaluate(f"document.querySelector('{selector}')?.scrollIntoView({{behavior: 'instant', block: 'center'}})")
        await page.wait_for_timeout(200)
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
        await page.wait_for_timeout(250)
        return
    
    try:
        # Quick interactions - just verify widget is functional, don't wait for full results
        if slug in ("ai-pricing-calculator", "ai-openai-vs-anthropic-pricing"):
            calculate_btn = page.locator("#pcw-calculate-btn")
            if await calculate_btn.is_visible(timeout=3000):
                await calculate_btn.click()
                print("    ✓ Triggered calculation")
                # Brief wait for API call to start (don't wait for full results)
                await page.wait_for_timeout(1000)
        
        elif slug in ("ai-error-decoder", "ai-openai-errors", "ai-openai-429-errors"):
            textarea = page.locator("#edw-error-textarea")
            if await textarea.is_visible(timeout=3000):
                await textarea.fill("rate limit exceeded")
                decode_btn = page.locator("#edw-decode-btn")
                if await decode_btn.is_visible(timeout=2000):
                    await decode_btn.click()
                    print("    ✓ Triggered decode")
                    # Brief wait for API call to start
                    await page.wait_for_timeout(1000)
        
        elif slug in ("ai-status", "ai-is-openai-down"):
            # Status page auto-loads, just wait briefly for cards
            try:
                await page.wait_for_selector(".spw-provider-card", timeout=5000, state="attached")
                print("    ✓ Status cards visible")
            except:
                pass
            await page.wait_for_timeout(500)
        
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
    headless: bool = True,
    use_webp: bool = False,
    compact: bool = False
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
        use_webp: If True, use WebP format instead of PNG (smaller files)
        compact: If True, use lower resolution (1440x900 at 1.5x scale)
    
    Returns:
        Tuple of (success: bool, output_paths: List[Path])
    """
    if mobile:
        viewport = {"width": 375, "height": 667}
        device_scale = 1
    elif compact:
        viewport = {"width": 1440, "height": 900}
        device_scale = 1.5
    else:
        viewport = {"width": 1920, "height": 1080}
        device_scale = 2
    
    suffix = "-mobile" if mobile else "-desktop"
    viewport_label = "mobile" if mobile else ("compact" if compact else "desktop")
    
    print(f"📸 Capturing {slug} ({viewport_label})...")
    
    # Reuse browser if provided, otherwise create new one
    if browser is None:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=headless)
            return await _capture_with_browser(browser, url, slug, output_dir, format, mobile, suffix, viewport, device_scale, use_webp)
    else:
        return await _capture_with_browser(browser, url, slug, output_dir, format, mobile, suffix, viewport, device_scale, use_webp)


async def _capture_with_browser(
    browser,
    url: str,
    slug: str,
    output_dir: Path,
    format: str,
    mobile: bool,
    suffix: str,
    viewport: dict,
    device_scale: float = 2,
    use_webp: bool = False
) -> Tuple[bool, List[Path]]:
    """Internal helper to capture page with an existing browser."""
    context = await browser.new_context(
        viewport=viewport,
        device_scale_factor=device_scale,
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
            # Determine image format and extension
            if use_webp:
                img_path = output_dir / f"{slug}{suffix}.webp"
                screenshot_opts = {"path": str(img_path), "full_page": True, "animations": "disabled", "type": "jpeg"}
                # Note: Playwright doesn't support webp directly, use high-quality JPEG as alternative
                # Actually, let's check - if format is png we use png, but webp flag means we want smaller
                # Playwright supports: png, jpeg. WebP not directly supported, so use jpeg with quality
                img_path = output_dir / f"{slug}{suffix}.jpg"
                await page.screenshot(
                    path=str(img_path),
                    full_page=True,
                    animations="disabled",
                    type="jpeg",
                    quality=90
                )
            else:
                img_path = output_dir / f"{slug}{suffix}.png"
                await page.screenshot(
                    path=str(img_path),
                    full_page=True,
                    animations="disabled"
                )
            overwriting = img_path.exists()
            output_paths.append(img_path)
            action = "Overwrote" if overwriting else "Saved"
            print(f"  ✓ {action} {img_path.suffix.upper()[1:]}: {img_path}")
        
        return True, output_paths
        
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False, output_paths
    finally:
        await context.close()


async def capture_page_segments(
    page,
    slug: str,
    output_dir: Path,
    use_webp: bool = False,
    viewport_height: int = 1080
) -> List[Path]:
    """Capture viewport-sized screenshot segments of a page.
    
    Takes multiple screenshots at different scroll positions,
    with overlap to ensure complete coverage.
    
    Args:
        page: Playwright page object (already navigated to the URL)
        slug: Page slug for filename prefix
        output_dir: Directory to save output
        use_webp: If True, use JPEG format with quality 90 (smaller files)
        viewport_height: Height of viewport for segment calculation
    
    Returns:
        List of output paths for all segments
    """
    output_paths = []
    
    # Get total page height
    total_height = await page.evaluate("document.body.scrollHeight")
    overlap = 180
    scroll_step = viewport_height - overlap
    
    # Pre-calculate total segments for improved naming
    total_segments = 1
    calc_scroll = 0
    while calc_scroll + scroll_step < total_height:
        calc_scroll += scroll_step
        total_segments += 1
    total_segments = min(total_segments, 50)  # Cap at 50
    
    # Determine file extension
    ext = ".jpg" if use_webp else ".png"
    
    segment_num = 1
    current_scroll = 0
    
    while current_scroll < total_height:
        # Scroll to position
        await page.evaluate(f"window.scrollTo(0, {current_scroll})")
        
        # Wait for page to settle after scroll (reduced from 300ms)
        await page.wait_for_timeout(150)
        
        # Generate filename with segment number and total (e.g., slug-001-of-03.png)
        filename = f"{slug}-{segment_num:03d}-of-{total_segments:02d}{ext}"
        output_path = output_dir / filename
        overwriting = output_path.exists()
        
        # Take screenshot of current viewport
        if use_webp:
            await page.screenshot(
                path=str(output_path),
                full_page=False,
                animations="disabled",
                type="jpeg",
                quality=90
            )
        else:
            await page.screenshot(
                path=str(output_path),
                full_page=False,
                animations="disabled"
            )
        
        output_paths.append(output_path)
        action = "Overwrote" if overwriting else "Captured"
        print(f"    ✓ {action} segment {segment_num}/{total_segments}: {filename}")
        
        # Move to next position
        current_scroll += scroll_step
        segment_num += 1
        
        # Safety check - don't create more than 50 segments per page
        if segment_num > 50:
            print(f"    ⚠ Reached maximum segment limit (50)")
            break
    
    return output_paths


async def capture_all_segments(
    output_dir: Optional[Path] = None,
    headless: bool = True,
    use_webp: bool = False,
    compact: bool = False,
    parallel: int = 3
):
    """Capture segmented screenshots for all pages with parallel execution.
    
    Args:
        output_dir: Directory to save output (defaults to SCREENSHOT_DIR)
        headless: If True, run browser in headless mode (default True)
        use_webp: If True, use JPEG format with quality 90 (smaller files)
        compact: If True, use lower resolution (1440x900 at 1.5x scale)
        parallel: Number of concurrent page captures (default: 3)
    """
    if output_dir is None:
        output_dir = SCREENSHOT_DIR
    
    output_dir.mkdir(exist_ok=True)
    
    # Determine viewport settings
    if compact:
        viewport = {"width": 1440, "height": 900}
        device_scale = 1.5
        viewport_label = "1440x900 @ 1.5x"
    else:
        viewport = {"width": 1920, "height": 1080}
        device_scale = 2
        viewport_label = "1920x1080 @ 2x"
    
    print("=== Segmented Screenshot Capture (LLM Visual Analysis) ===\n")
    print(f"Viewport: {viewport_label}, Overlap: 180px")
    print(f"Format: {'JPEG (quality 90)' if use_webp else 'PNG'}")
    print(f"Parallel: {parallel} concurrent captures\n")
    
    start_time = time.perf_counter()
    manifest_data: Dict[str, Any] = {
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "viewport": {**viewport, "scale": device_scale},
        "format": "jpeg" if use_webp else "png",
        "pages": []
    }
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        semaphore = asyncio.Semaphore(parallel)
        
        async def capture_one_page(slug: str, url: str) -> Tuple[str, bool, List[Path], bool]:
            """Capture segments for a single page with semaphore limiting."""
            async with semaphore:
                page_start = time.perf_counter()
                print(f"📸 Capturing segments for {slug}...")
                
                context = await browser.new_context(
                    viewport=viewport,
                    device_scale_factor=device_scale,
                )
                page = await context.new_page()
                widget_interacted = False
                
                try:
                    print(f"  Loading {url}...")
                    await page.goto(url, wait_until="domcontentloaded", timeout=40000)
                    
                    await wait_for_widgets(page, slug)
                    await interact_with_widget(page, slug)
                    widget_interacted = True
                    
                    # Scroll back to top before capturing segments
                    await page.evaluate("window.scrollTo(0, 0)")
                    await page.wait_for_timeout(150)
                    
                    paths = await capture_page_segments(
                        page, slug, output_dir,
                        use_webp=use_webp,
                        viewport_height=viewport["height"]
                    )
                    
                    elapsed = time.perf_counter() - page_start
                    print(f"  ✓ Captured {len(paths)} segment(s) in {elapsed:.1f}s\n")
                    return (slug, True, paths, widget_interacted)
                    
                except Exception as e:
                    print(f"  ✗ Error: {e}\n")
                    return (slug, False, [], widget_interacted)
                finally:
                    await context.close()
        
        # Run all captures in parallel with semaphore limiting
        tasks = [capture_one_page(slug, url) for slug, url in PAGES.items()]
        results = await asyncio.gather(*tasks)
        
        await browser.close()
    
    total_time = time.perf_counter() - start_time
    
    # Build manifest and summary
    successful = []
    failed = []
    
    for slug, success, paths, widget_interacted in results:
        if success:
            successful.append((slug, paths))
            # Determine page type
            page_type = "tool" if slug in TOOL_PAGES else "guide"
            manifest_data["pages"].append({
                "slug": slug,
                "url": PAGES[slug],
                "type": page_type,
                "segments": [p.name for p in paths],
                "widget_interacted": widget_interacted
            })
        else:
            failed.append(slug)
    
    # Write manifest
    manifest_path = output_dir / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest_data, f, indent=2)
    
    # Summary
    print("=== Summary ===")
    total_segments = sum(len(p) for _, p in successful)
    
    if successful:
        print(f"✓ Successfully captured {len(successful)} page(s) ({total_segments} total segments):")
        for slug, paths in successful:
            print(f"  - {slug}: {len(paths)} segment(s)")
    
    if failed:
        print(f"\n✗ Failed to capture {len(failed)} page(s):")
        for slug in failed:
            print(f"  - {slug}")
    
    print(f"\nTotal time: {total_time:.1f}s")
    print(f"Manifest: {manifest_path}")
    print(f"Segments saved to: {output_dir.absolute()}")


async def capture_all(
    format: str = "pdf",
    mobile: bool = False,
    headless: bool = True,
    use_webp: bool = False,
    compact: bool = False,
    parallel: int = 3
):
    """Capture all pages with parallel execution."""
    SCREENSHOT_DIR.mkdir(exist_ok=True)
    
    print("=== WordPress Page Capture ===\n")
    print(f"Format: {format}, Parallel: {parallel} concurrent captures\n")
    
    start_time = time.perf_counter()
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        semaphore = asyncio.Semaphore(parallel)
        
        async def capture_with_limit(slug: str, url: str) -> Tuple[str, bool, List[Path]]:
            async with semaphore:
                success, paths = await capture_page(
                    url, slug, SCREENSHOT_DIR, format, mobile, browser,
                    headless, use_webp, compact
                )
                return (slug, success, paths)
        
        tasks = [capture_with_limit(slug, url) for slug, url in PAGES.items()]
        results = await asyncio.gather(*tasks)
        
        await browser.close()
    
    total_time = time.perf_counter() - start_time
    
    # Summary
    print("\n=== Summary ===")
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
    
    print(f"\nTotal time: {total_time:.1f}s")
    print(f"Screenshots saved to: {SCREENSHOT_DIR.absolute()}")


async def capture_one(
    slug: str,
    format: str = "pdf",
    mobile: bool = False,
    headless: bool = True,
    use_webp: bool = False,
    compact: bool = False
):
    """Capture a single page."""
    if slug not in PAGES:
        print(f"Error: Unknown slug '{slug}'")
        print(f"Available slugs: {', '.join(PAGES.keys())}")
        return 1
    
    SCREENSHOT_DIR.mkdir(exist_ok=True)
    url = PAGES[slug]
    
    success, paths = await capture_page(
        url, slug, SCREENSHOT_DIR, format, mobile,
        browser=None, headless=headless, use_webp=use_webp, compact=compact
    )
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
    """Remove all existing screenshots and manifest from output directory.
    
    Args:
        output_dir: Directory to clean
    """
    if not output_dir.exists():
        return
    
    removed = 0
    for ext in ("*.pdf", "*.png", "*.jpg", "*.webp", "manifest.json"):
        for f in output_dir.glob(ext):
            f.unlink()
            removed += 1
    
    if removed > 0:
        print(f"🧹 Cleaned {removed} existing file(s) from {output_dir}")


def main():
    parser = argparse.ArgumentParser(
        description="Take screenshots/PDFs of WordPress pages for LLM visual analysis",
        epilog="Recommended for LLM analysis: --format segments --jpeg"
    )
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
        help="Output format: pdf (default), png, both, or segments (viewport-sized)"
    )
    parser.add_argument(
        "--jpeg",
        action="store_true",
        help="Use JPEG format with quality 90 (smaller files, recommended for LLM analysis)"
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Lower resolution mode (1440x900 at 1.5x scale, opt-in)"
    )
    parser.add_argument(
        "--mobile",
        action="store_true",
        help="Capture mobile viewport (375x667) instead of desktop"
    )
    parser.add_argument(
        "--parallel",
        type=int,
        default=3,
        help="Number of concurrent page captures (default: 3)"
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
        print("\nTool pages:")
        for slug, url in TOOL_PAGES.items():
            print(f"  {slug}: {url}")
        print("\nGuide pages:")
        for slug, url in GUIDE_PAGES.items():
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
            print("Warning: --mobile is ignored for segments format")
        asyncio.run(capture_all_segments(
            headless=headless,
            use_webp=args.jpeg,
            compact=args.compact,
            parallel=args.parallel
        ))
        return 0
    elif args.all:
        asyncio.run(capture_all(
            format=args.format,
            mobile=args.mobile,
            headless=headless,
            use_webp=args.jpeg,
            compact=args.compact,
            parallel=args.parallel
        ))
        return 0
    elif args.slug:
        return asyncio.run(capture_one(
            args.slug,
            format=args.format,
            mobile=args.mobile,
            headless=headless,
            use_webp=args.jpeg,
            compact=args.compact
        ))
    else:
        # Default: capture all
        asyncio.run(capture_all(
            format=args.format,
            mobile=args.mobile,
            headless=headless,
            use_webp=args.jpeg,
            compact=args.compact,
            parallel=args.parallel
        ))
        return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
CLI tool for WordPress page management.

Content files are stored as HTML with YAML frontmatter. No markdown conversion needed.

Usage:
    python scripts/wp_pages.py list
    python scripts/wp_pages.py pull --slug ai-pricing-calculator
    python scripts/wp_pages.py push --file content/tools/ai-pricing-calculator.html
    python scripts/wp_pages.py diff --slug ai-pricing-calculator
    python scripts/wp_pages.py verify [--slug SLUG] [--format pdf|png|both] [--mobile]
"""
import argparse
import sys
import re
from pathlib import Path
from typing import Tuple, Dict

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

from services.wordpress import WordPressService


def parse_frontmatter(content: str) -> Tuple[Dict, str]:
    """Parse YAML frontmatter from content file.
    
    Args:
        content: Full content with frontmatter
        
    Returns:
        Tuple of (frontmatter_dict, body_content)
    """
    if not content.startswith('---'):
        return {}, content
    
    # Find the closing ---
    parts = content.split('---', 2)
    if len(parts) < 3:
        return {}, content
    
    frontmatter_text = parts[1].strip()
    body = parts[2].strip()
    
    # Parse YAML-like frontmatter (simple key: value parsing)
    meta = {}
    for line in frontmatter_text.split('\n'):
        line = line.strip()
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            meta[key] = value
    
    return meta, body


def format_frontmatter(meta: Dict) -> str:
    """Format dict as YAML frontmatter.
    
    Args:
        meta: Dictionary of frontmatter fields
        
    Returns:
        YAML frontmatter string
    """
    lines = ['---']
    for key, value in meta.items():
        if isinstance(value, str):
            # Escape quotes if needed
            if '"' in value or "'" in value:
                escaped = value.replace('"', '\\"')
                value = f'"{escaped}"'
            lines.append(f"{key}: {value}")
        else:
            lines.append(f"{key}: {value}")
    lines.append('---')
    return '\n'.join(lines)


def strip_html_for_display(html: str) -> str:
    """Strip HTML tags for display purposes (used in diff/pull preview).
    
    Args:
        html: HTML content
        
    Returns:
        Plain text for display
    """
    # Remove WordPress comments
    text = re.sub(r'<!--.*?-->', '', html, flags=re.DOTALL)
    # Remove script tags entirely
    text = re.sub(r'<script[^>]*>.*?</script>', '[WIDGET]', text, flags=re.DOTALL)
    # Convert some tags to readable format
    text = re.sub(r'<h[1-6]>(.*?)</h[1-6]>', r'\n## \1\n', text)
    text = re.sub(r'<p>(.*?)</p>', r'\1\n', text, flags=re.DOTALL)
    text = re.sub(r'<li>(.*?)</li>', r'  - \1', text, flags=re.DOTALL)
    # Remove remaining tags
    text = re.sub(r'<[^>]+>', '', text)
    # Clean up whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def cmd_list(args):
    """List all pages from WordPress."""
    wp = WordPressService()
    if not wp.is_configured():
        print("Error: WordPress not configured. Set WORDPRESS_USERNAME and WORDPRESS_APP_PASSWORD.")
        return 1
    
    pages = wp.list_pages()
    print(f"{'ID':>6}  {'Slug':<35}  {'Status':<10}  Title")
    print("-" * 80)
    for page in sorted(pages, key=lambda p: p.get('slug', '')):
        title = page.get('title', {}).get('rendered', '')[:30] if isinstance(page.get('title'), dict) else str(page.get('title', ''))[:30]
        print(f"{page['id']:>6}  {page['slug']:<35}  {page['status']:<10}  {title}")


def cmd_pull(args):
    """Pull page content to local HTML file."""
    wp = WordPressService()
    if not wp.is_configured():
        print("Error: WordPress not configured. Set WORDPRESS_USERNAME and WORDPRESS_APP_PASSWORD.")
        return 1
    
    page = wp.get_page_by_slug(args.slug)
    if not page:
        print(f"Page not found: {args.slug}")
        return 1
    
    # Build frontmatter
    title = page.get('title', {}).get('rendered', '') if isinstance(page.get('title'), dict) else str(page.get('title', ''))
    meta = {
        'title': title,
        'slug': page['slug'],
        'status': page['status'],
        'page_id': str(page['id']),
        'seo_title': '',  # Would need AIOSEO API call to get this
        'seo_description': '',
        'widget_endpoint': '',  # Infer from slug
    }
    
    # Infer widget endpoint from slug
    slug_parts = args.slug.replace('ai-', '').split('-')
    if slug_parts:
        meta['widget_endpoint'] = f"/{slug_parts[0]}/widget"
    
    # Get HTML content directly (no conversion)
    content_html = page.get('content', {}).get('rendered', '') if isinstance(page.get('content'), dict) else str(page.get('content', ''))
    
    # Write file as HTML
    output_path = Path(f"content/tools/{args.slug}.html")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    content = format_frontmatter(meta) + "\n\n" + content_html.strip()
    output_path.write_text(content, encoding='utf-8')
    print(f"Pulled: {output_path}")
    
    # Show preview
    print("\nContent preview:")
    print("-" * 40)
    preview = strip_html_for_display(content_html)[:500]
    print(preview + ("..." if len(content_html) > 500 else ""))


def cmd_push(args):
    """Push local HTML file to WordPress."""
    wp = WordPressService()
    if not wp.is_configured():
        print("Error: WordPress not configured. Set WORDPRESS_USERNAME and WORDPRESS_APP_PASSWORD.")
        return 1
    
    content_path = Path(args.file)
    
    if not content_path.exists():
        print(f"File not found: {content_path}")
        return 1
    
    content = content_path.read_text(encoding='utf-8')
    meta, body = parse_frontmatter(content)
    
    if not meta.get('slug'):
        print("Error: slug is required in frontmatter")
        return 1
    
    # Check if page exists
    existing = wp.get_page_by_slug(meta['slug'])
    
    # Body is already HTML - send directly to WordPress
    page_data = {
        'title': meta.get('title', 'Untitled'),
        'content': body,  # HTML body, no conversion needed
        'slug': meta['slug'],
        'status': meta.get('status', 'draft'),
    }
    
    if existing:
        result = wp.update_page(existing['id'], page_data)
        action = "Updated"
        page_id = existing['id']
    else:
        result = wp.create_page(page_data)
        action = "Created"
        page_id = result['id'] if result else None
    
    if result:
        print(f"{action} page {page_id}: {meta['slug']}")
        
        # Update SEO meta if present
        if meta.get('seo_title') or meta.get('seo_description'):
            wp.update_aioseo_meta(page_id, {
                'title': meta.get('seo_title', ''),
                'description': meta.get('seo_description', ''),
            })
            print(f"Updated AIOSEO meta")
    else:
        print(f"Failed to {action.lower()} page")
        return 1


def cmd_diff(args):
    """Show diff between local and remote content."""
    wp = WordPressService()
    if not wp.is_configured():
        print("Error: WordPress not configured. Set WORDPRESS_USERNAME and WORDPRESS_APP_PASSWORD.")
        return 1
    
    # Get remote page
    page = wp.get_page_by_slug(args.slug)
    if not page:
        print(f"Page not found in WordPress: {args.slug}")
        return 1
    
    # Get local file (try .html first, then .md for backwards compatibility)
    local_path = Path(f"content/tools/{args.slug}.html")
    if not local_path.exists():
        local_path = Path(f"content/tools/{args.slug}.md")
    
    if not local_path.exists():
        print(f"Local file not found: content/tools/{args.slug}.html")
        print("Use 'pull' command to download from WordPress first.")
        return 1
    
    # Compare
    local_content = local_path.read_text(encoding='utf-8')
    _, local_body = parse_frontmatter(local_content)
    
    remote_html = page.get('content', {}).get('rendered', '') if isinstance(page.get('content'), dict) else str(page.get('content', ''))
    
    # Simple comparison - check if content lengths are similar
    local_len = len(local_body.strip())
    remote_len = len(remote_html.strip())
    
    print(f"Diff for: {args.slug}")
    print("=" * 80)
    print(f"Local file: {local_path}")
    print(f"Local content length: {local_len} chars")
    print(f"Remote content length: {remote_len} chars")
    print(f"Remote page ID: {page['id']}")
    print(f"Remote status: {page['status']}")
    
    if abs(local_len - remote_len) > 100:
        print(f"\n⚠️  Content lengths differ significantly!")
        if local_len > remote_len:
            print(f"   Local is {local_len - remote_len} chars longer - consider pushing")
        else:
            print(f"   Remote is {remote_len - local_len} chars longer - consider pulling")


def cmd_push_all(args):
    """Push all HTML files in content/tools/ to WordPress."""
    import time
    
    wp = WordPressService()
    if not wp.is_configured():
        print("Error: WordPress not configured. Set WORDPRESS_USERNAME and WORDPRESS_APP_PASSWORD.")
        return 1
    
    content_dir = Path("content/tools")
    
    # Find all content files (.html preferred, .md for backwards compatibility)
    html_files = sorted(content_dir.glob("*.html"))
    md_files = sorted(content_dir.glob("*.md"))
    
    # Use HTML files, but include MD files that don't have HTML equivalents
    html_slugs = {f.stem for f in html_files}
    content_files = list(html_files)
    for md_file in md_files:
        if md_file.stem not in html_slugs and not md_file.name.startswith('_'):
            content_files.append(md_file)
    
    # Skip template files
    content_files = [f for f in content_files if not f.name.startswith('_')]
    content_files = sorted(content_files, key=lambda f: f.stem)
    
    print(f"Found {len(content_files)} content files to push")
    print("-" * 50)
    
    successes = []
    failures = []
    
    for i, content_path in enumerate(content_files):
        print(f"\n[{i+1}/{len(content_files)}] Pushing {content_path.name}...")
        
        content = content_path.read_text(encoding='utf-8')
        meta, body = parse_frontmatter(content)
        
        if not meta.get('slug'):
            print(f"  ⚠️  Skipped: no slug in frontmatter")
            failures.append((content_path.name, "no slug"))
            continue
        
        # Check if page exists
        existing = wp.get_page_by_slug(meta['slug'])
        
        # Body is HTML - send directly (no conversion)
        page_data = {
            'title': meta.get('title', 'Untitled'),
            'content': body,
            'slug': meta['slug'],
            'status': meta.get('status', 'draft'),
        }
        
        if existing:
            result = wp.update_page(existing['id'], page_data)
            action = "Updated"
            page_id = existing['id']
        else:
            result = wp.create_page(page_data)
            action = "Created"
            page_id = result['id'] if result else None
        
        if result:
            print(f"  ✅ {action} page {page_id}: {meta['slug']}")
            
            # Update SEO meta if present
            if meta.get('seo_title') or meta.get('seo_description'):
                wp.update_aioseo_meta(page_id, {
                    'title': meta.get('seo_title', ''),
                    'description': meta.get('seo_description', ''),
                })
            
            successes.append((content_path.name, meta['slug'], page_id))
        else:
            print(f"  ❌ Failed to {action.lower()} page")
            failures.append((content_path.name, f"failed to {action.lower()}"))
        
        # Small delay between requests to be nice to the server
        if i < len(content_files) - 1:
            time.sleep(1)
    
    # Summary
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    print(f"✅ Successes: {len(successes)}")
    for name, slug, page_id in successes:
        print(f"   - {name} → {slug} (ID: {page_id})")
    
    if failures:
        print(f"\n❌ Failures: {len(failures)}")
        for name, reason in failures:
            print(f"   - {name}: {reason}")
        return 1
    
    return 0


def cmd_push_post(args):
    """Push local HTML file to WordPress as a POST (not page)."""
    wp = WordPressService()
    if not wp.is_configured():
        print("Error: WordPress not configured. Set WORDPRESS_USERNAME and WORDPRESS_APP_PASSWORD.")
        return 1
    
    content_path = Path(args.file)
    
    if not content_path.exists():
        print(f"File not found: {content_path}")
        return 1
    
    content = content_path.read_text(encoding='utf-8')
    meta, body = parse_frontmatter(content)
    
    if not meta.get('slug'):
        print("Error: slug is required in frontmatter")
        return 1
    
    # Check if post exists
    existing = wp.get_post_by_slug(meta['slug'])
    
    # Get or create category if specified
    category_ids = []
    if meta.get('category'):
        cat_id = wp.get_or_create_category(meta['category'])
        if cat_id:
            category_ids.append(cat_id)
    
    # Body is already HTML - send directly to WordPress
    post_data = {
        'title': meta.get('title', 'Untitled'),
        'content': body,
        'slug': meta['slug'],
        'status': meta.get('status', 'draft'),
    }
    
    if category_ids:
        post_data['categories'] = category_ids
    
    if existing:
        result = wp.update_post(existing['id'], post_data)
        action = "Updated"
        post_id = existing['id']
    else:
        result = wp.create_post(post_data)
        action = "Created"
        post_id = result['id'] if result else None
    
    if result:
        print(f"{action} POST {post_id}: {meta['slug']}")
        
        # Update SEO meta if present
        if meta.get('seo_title') or meta.get('seo_description'):
            wp.update_aioseo_meta(post_id, {
                'title': meta.get('seo_title', ''),
                'description': meta.get('seo_description', ''),
            })
            print(f"Updated AIOSEO meta")
        
        # Show URL
        print(f"URL: https://www.ai-buzz.com/{meta['slug']}/")
    else:
        print(f"Failed to {action.lower()} post")
        return 1


def cmd_push_guides(args):
    """Push all guide HTML files as WordPress posts."""
    import time
    
    wp = WordPressService()
    if not wp.is_configured():
        print("Error: WordPress not configured. Set WORDPRESS_USERNAME and WORDPRESS_APP_PASSWORD.")
        return 1
    
    content_dir = Path("content/guides")
    
    if not content_dir.exists():
        print(f"Directory not found: {content_dir}")
        return 1
    
    html_files = sorted(content_dir.glob("*.html"))
    html_files = [f for f in html_files if not f.name.startswith('_')]
    
    print(f"Found {len(html_files)} guide files to push as posts")
    print("-" * 50)
    
    # Get or create the "AI Guides" category
    guides_category_id = wp.get_or_create_category("AI Guides", "ai-guides")
    if guides_category_id:
        print(f"Using category 'AI Guides' (ID: {guides_category_id})")
    
    successes = []
    failures = []
    
    for i, content_path in enumerate(html_files):
        print(f"\n[{i+1}/{len(html_files)}] Pushing {content_path.name} as POST...")
        
        content = content_path.read_text(encoding='utf-8')
        meta, body = parse_frontmatter(content)
        
        if not meta.get('slug'):
            print(f"  ⚠️  Skipped: no slug in frontmatter")
            failures.append((content_path.name, "no slug"))
            continue
        
        # Check if post exists
        existing = wp.get_post_by_slug(meta['slug'])
        
        post_data = {
            'title': meta.get('title', 'Untitled'),
            'content': body,
            'slug': meta['slug'],
            'status': meta.get('status', 'draft'),
        }
        
        if guides_category_id:
            post_data['categories'] = [guides_category_id]
        
        if existing:
            result = wp.update_post(existing['id'], post_data)
            action = "Updated"
            post_id = existing['id']
        else:
            result = wp.create_post(post_data)
            action = "Created"
            post_id = result['id'] if result else None
        
        if result:
            print(f"  ✅ {action} POST {post_id}: {meta['slug']}")
            
            if meta.get('seo_title') or meta.get('seo_description'):
                wp.update_aioseo_meta(post_id, {
                    'title': meta.get('seo_title', ''),
                    'description': meta.get('seo_description', ''),
                })
            
            successes.append((content_path.name, meta['slug'], post_id))
        else:
            print(f"  ❌ Failed to {action.lower()} post")
            failures.append((content_path.name, f"failed to {action.lower()}"))
        
        if i < len(html_files) - 1:
            time.sleep(1)
    
    # Summary
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    print(f"✅ Successes: {len(successes)}")
    for name, slug, post_id in successes:
        print(f"   - {name} → {slug} (POST ID: {post_id})")
    
    if failures:
        print(f"\n❌ Failures: {len(failures)}")
        for name, reason in failures:
            print(f"   - {name}: {reason}")
        return 1
    
    print("\n⚠️  IMPORTANT: Set up 301 redirects from old PAGE URLs to new POST URLs")
    print("   Add these redirects in WordPress (Redirection plugin or .htaccess)")
    
    return 0


def cmd_verify(args):
    """Verify WordPress pages by taking screenshots/PDFs."""
    # Lazy import - only load screenshot module when verify command is called
    try:
        import importlib.util
        import asyncio
        screenshot_module_path = Path(__file__).parent / "screenshot_pages.py"
        spec = importlib.util.spec_from_file_location("screenshot_pages", screenshot_module_path)
        screenshot_pages = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(screenshot_pages)
        capture_all = screenshot_pages.capture_all
        capture_one = screenshot_pages.capture_one
        PAGES = screenshot_pages.PAGES
    except (ImportError, AttributeError, FileNotFoundError) as e:
        print("Error: Screenshot functionality not available.")
        print("Install playwright: pip install playwright && playwright install chromium")
        return 1
    
    format_type = args.format if hasattr(args, 'format') else 'pdf'
    mobile = args.mobile if hasattr(args, 'mobile') else False
    
    if args.slug:
        # Verify single page
        if args.slug not in PAGES:
            print(f"Error: Unknown slug '{args.slug}'")
            print(f"Available slugs: {', '.join(PAGES.keys())}")
            return 1
        return asyncio.run(capture_one(args.slug, format=format_type, mobile=mobile))
    else:
        # Verify all pages
        asyncio.run(capture_all(format=format_type, mobile=mobile))
        return 0


def main():
    parser = argparse.ArgumentParser(description='WordPress page management for AI-Buzz tools')
    subparsers = parser.add_subparsers(dest='command', required=True)
    
    subparsers.add_parser('list', help='List all WordPress pages')
    
    pull = subparsers.add_parser('pull', help='Pull page to local HTML file')
    pull.add_argument('--slug', required=True, help='Page slug (e.g., ai-pricing-calculator)')
    
    push = subparsers.add_parser('push', help='Push local HTML file to WordPress')
    push.add_argument('--file', required=True, help='Path to HTML file')
    
    subparsers.add_parser('push-all', help='Push all HTML files to WordPress')
    
    diff = subparsers.add_parser('diff', help='Show diff between local and remote')
    diff.add_argument('--slug', required=True, help='Page slug')
    
    verify = subparsers.add_parser('verify', help='Verify pages by taking screenshots/PDFs')
    verify.add_argument('--slug', help='Verify specific page slug (default: all pages)')
    verify.add_argument('--format', choices=['pdf', 'png', 'both'], default='pdf', help='Output format (default: pdf)')
    verify.add_argument('--mobile', action='store_true', help='Capture mobile viewport instead of desktop')
    
    # Post commands (for guide content)
    push_post = subparsers.add_parser('push-post', help='Push HTML file as WordPress POST (not page)')
    push_post.add_argument('--file', required=True, help='Path to HTML file')
    
    subparsers.add_parser('push-guides', help='Push all guides in content/guides/ as WordPress posts')
    
    args = parser.parse_args()
    
    commands = {
        'list': cmd_list,
        'pull': cmd_pull,
        'push': cmd_push,
        'push-all': cmd_push_all,
        'diff': cmd_diff,
        'verify': cmd_verify,
        'push-post': cmd_push_post,
        'push-guides': cmd_push_guides,
    }
    return commands[args.command](args) or 0


if __name__ == '__main__':
    sys.exit(main())

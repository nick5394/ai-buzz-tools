#!/usr/bin/env python3
"""
CLI tool for WordPress page management.

Usage:
    python scripts/wp_pages.py list
    python scripts/wp_pages.py pull --slug ai-pricing-calculator
    python scripts/wp_pages.py push --file content/tools/pricing-calculator.md
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
    """Parse YAML frontmatter from markdown content.
    
    Args:
        content: Full markdown content with frontmatter
        
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
                value = f'"{value.replace('"', '\\"')}"'
            lines.append(f"{key}: {value}")
        else:
            lines.append(f"{key}: {value}")
    lines.append('---')
    return '\n'.join(lines)


def html_to_markdown(html: str) -> str:
    """Convert WordPress HTML to markdown (basic conversion).
    
    Args:
        html: HTML content from WordPress
        
    Returns:
        Markdown content
    """
    # Remove WordPress-specific tags
    html = re.sub(r'<!--.*?-->', '', html, flags=re.DOTALL)
    
    # Convert headings
    html = re.sub(r'<h1>(.*?)</h1>', r'# \1', html)
    html = re.sub(r'<h2>(.*?)</h2>', r'## \1', html)
    html = re.sub(r'<h3>(.*?)</h3>', r'### \1', html)
    
    # Convert paragraphs
    html = re.sub(r'<p>(.*?)</p>', r'\1\n\n', html, flags=re.DOTALL)
    
    # Convert lists
    html = re.sub(r'<li>(.*?)</li>', r'- \1', html, flags=re.DOTALL)
    html = re.sub(r'<ul>|</ul>|<ol>|</ol>', '', html)
    
    # Convert links
    html = re.sub(r'<a href="([^"]+)">(.*?)</a>', r'[\2](\1)', html)
    
    # Convert bold/italic
    html = re.sub(r'<strong>(.*?)</strong>', r'**\1**', html)
    html = re.sub(r'<em>(.*?)</em>', r'*\1*', html)
    
    # Remove remaining HTML tags
    html = re.sub(r'<[^>]+>', '', html)
    
    # Clean up whitespace
    html = re.sub(r'\n{3,}', '\n\n', html)
    
    return html.strip()


def markdown_to_html(md: str) -> str:
    """Convert markdown body to HTML for WordPress.
    
    Args:
        md: Markdown content
        
    Returns:
        HTML content
    """
    html = md
    
    # First, handle code blocks (``` ... ```) - convert to <pre><code>
    # This must happen before other conversions to preserve code content
    def replace_code_block(match):
        lang = match.group(1) or ''
        code = match.group(2)
        # Escape HTML entities in code
        code = code.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        if lang:
            return f'<pre><code class="language-{lang}">{code}</code></pre>'
        return f'<pre><code>{code}</code></pre>'
    
    html = re.sub(r'```(\w*)\n(.*?)```', replace_code_block, html, flags=re.DOTALL)
    
    # Convert headings
    html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
    
    # Convert links
    html = re.sub(r'\[([^\]]+)\]\(([^\)]+)\)', r'<a href="\2">\1</a>', html)
    
    # Convert bold/italic
    html = re.sub(r'\*\*([^\*]+)\*\*', r'<strong>\1</strong>', html)
    html = re.sub(r'\*([^\*]+)\*', r'<em>\1</em>', html)
    
    # Convert markdown tables to HTML tables
    def convert_table(table_lines):
        """Convert markdown table lines to HTML table."""
        rows = []
        for i, line in enumerate(table_lines):
            # Skip separator row (contains only |, -, and spaces)
            if re.match(r'^[\|\-\s:]+$', line):
                continue
            cells = [cell.strip() for cell in line.strip('|').split('|')]
            tag = 'th' if i == 0 else 'td'
            row = ''.join(f'<{tag}>{cell}</{tag}>' for cell in cells)
            rows.append(f'<tr>{row}</tr>')
        if rows:
            # First row is header
            header = rows[0] if rows else ''
            body = ''.join(rows[1:]) if len(rows) > 1 else ''
            return f'<table><thead>{header}</thead><tbody>{body}</tbody></table>'
        return ''
    
    # Convert lists and paragraphs, preserving HTML tags
    lines = html.split('\n')
    in_list = False
    in_table = False
    table_lines = []
    result = []
    
    for line in lines:
        stripped = line.strip()
        
        # Check if line is part of a markdown table (starts and ends with |)
        is_table_line = stripped.startswith('|') and stripped.endswith('|')
        
        if is_table_line:
            if not in_table:
                in_table = True
                table_lines = []
            table_lines.append(stripped)
            continue
        elif in_table:
            # End of table, convert it
            result.append(convert_table(table_lines))
            in_table = False
            table_lines = []
        
        # Skip lines that already contain HTML (like <script>, <pre>, <table>, etc.)
        # These should pass through unchanged
        if stripped.startswith('<') and ('>' in stripped or stripped.startswith('</')):
            if in_list:
                result.append('</ul>')
                in_list = False
            result.append(stripped)
        elif stripped.startswith('- '):
            if not in_list:
                result.append('<ul>')
                in_list = True
            result.append(f'<li>{stripped[2:]}</li>')
        else:
            if in_list:
                result.append('</ul>')
                in_list = False
            if stripped:
                result.append(f'<p>{stripped}</p>')
            else:
                result.append('')
    
    # Close any open list
    if in_list:
        result.append('</ul>')
    
    # Handle any remaining table
    if in_table and table_lines:
        result.append(convert_table(table_lines))
    
    html = '\n'.join(result)
    
    # Clean up multiple newlines
    html = re.sub(r'\n{3,}', '\n\n', html)
    
    return html


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
    """Pull page content to local markdown file."""
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
    
    # Convert content
    content_html = page.get('content', {}).get('rendered', '') if isinstance(page.get('content'), dict) else str(page.get('content', ''))
    body = html_to_markdown(content_html)
    
    # Write file
    output_path = Path(f"content/tools/{args.slug}.md")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    content = format_frontmatter(meta) + "\n\n" + body
    output_path.write_text(content, encoding='utf-8')
    print(f"Pulled: {output_path}")

def cmd_push(args):
    """Push local markdown file to WordPress."""
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
    
    page_data = {
        'title': meta.get('title', 'Untitled'),
        'content': markdown_to_html(body),
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
    
    # Get local file
    local_path = Path(f"content/tools/{args.slug}.md")
    if not local_path.exists():
        print(f"Local file not found: {local_path}")
        print("Use 'pull' command to download from WordPress first.")
        return 1
    
    # Compare
    local_content = local_path.read_text(encoding='utf-8')
    remote_content_html = page.get('content', {}).get('rendered', '') if isinstance(page.get('content'), dict) else str(page.get('content', ''))
    remote_content = html_to_markdown(remote_content_html)
    
    print(f"Diff for: {args.slug}")
    print("=" * 80)
    print("Local file exists. Use 'pull' to overwrite with remote content.")
    print("Or manually compare the files.")
    print(f"\nRemote page ID: {page['id']}")
    print(f"Remote status: {page['status']}")

def cmd_push_all(args):
    """Push all markdown files in content/tools/ to WordPress."""
    from pathlib import Path
    import time
    
    wp = WordPressService()
    if not wp.is_configured():
        print("Error: WordPress not configured. Set WORDPRESS_USERNAME and WORDPRESS_APP_PASSWORD.")
        return 1
    
    content_dir = Path("content/tools")
    md_files = sorted(content_dir.glob("*.md"))
    
    # Skip template file
    md_files = [f for f in md_files if not f.name.startswith('_')]
    
    print(f"Found {len(md_files)} content files to push")
    print("-" * 50)
    
    successes = []
    failures = []
    
    for i, content_path in enumerate(md_files):
        print(f"\n[{i+1}/{len(md_files)}] Pushing {content_path.name}...")
        
        content = content_path.read_text(encoding='utf-8')
        meta, body = parse_frontmatter(content)
        
        if not meta.get('slug'):
            print(f"  ⚠️  Skipped: no slug in frontmatter")
            failures.append((content_path.name, "no slug"))
            continue
        
        # Check if page exists
        existing = wp.get_page_by_slug(meta['slug'])
        
        page_data = {
            'title': meta.get('title', 'Untitled'),
            'content': markdown_to_html(body),
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
        if i < len(md_files) - 1:
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
    
    pull = subparsers.add_parser('pull', help='Pull page to local markdown')
    pull.add_argument('--slug', required=True, help='Page slug (e.g., ai-pricing-calculator)')
    
    push = subparsers.add_parser('push', help='Push local markdown to WordPress')
    push.add_argument('--file', required=True, help='Path to markdown file')
    
    subparsers.add_parser('push-all', help='Push all markdown files to WordPress')
    
    diff = subparsers.add_parser('diff', help='Show diff between local and remote')
    diff.add_argument('--slug', required=True, help='Page slug')
    
    verify = subparsers.add_parser('verify', help='Verify pages by taking screenshots/PDFs')
    verify.add_argument('--slug', help='Verify specific page slug (default: all pages)')
    verify.add_argument('--format', choices=['pdf', 'png', 'both'], default='pdf', help='Output format (default: pdf)')
    verify.add_argument('--mobile', action='store_true', help='Capture mobile viewport instead of desktop')
    
    args = parser.parse_args()
    
    commands = {
        'list': cmd_list,
        'pull': cmd_pull,
        'push': cmd_push,
        'push-all': cmd_push_all,
        'diff': cmd_diff,
        'verify': cmd_verify,
    }
    return commands[args.command](args) or 0

if __name__ == '__main__':
    sys.exit(main())

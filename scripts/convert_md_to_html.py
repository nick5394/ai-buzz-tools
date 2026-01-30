#!/usr/bin/env python3
"""
One-time conversion script: Convert markdown content files to HTML.
Delete this script after running it.
"""
import re
from pathlib import Path


def parse_frontmatter(content: str):
    """Parse YAML frontmatter from content."""
    if not content.startswith('---'):
        return {}, content
    
    parts = content.split('---', 2)
    if len(parts) < 3:
        return {}, content
    
    frontmatter_text = parts[1].strip()
    body = parts[2].strip()
    
    meta = {}
    for line in frontmatter_text.split('\n'):
        line = line.strip()
        if ':' in line:
            key, value = line.split(':', 1)
            meta[key.strip()] = value.strip().strip('"').strip("'")
    
    return meta, body


def format_frontmatter(meta: dict) -> str:
    """Format dict as YAML frontmatter."""
    lines = ['---']
    for key, value in meta.items():
        lines.append(f"{key}: {value}")
    lines.append('---')
    return '\n'.join(lines)


def markdown_to_html(md: str) -> str:
    """Convert markdown to HTML with H1 demoted to H2."""
    html = md
    
    # Handle code blocks first (preserve content)
    code_blocks = []
    def save_code_block(match):
        lang = match.group(1) or ''
        code = match.group(2)
        code = code.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        idx = len(code_blocks)
        if lang:
            code_blocks.append(f'<pre><code class="language-{lang}">{code}</code></pre>')
        else:
            code_blocks.append(f'<pre><code>{code}</code></pre>')
        return f'__CODE_BLOCK_{idx}__'
    
    html = re.sub(r'```(\w*)\n(.*?)```', save_code_block, html, flags=re.DOTALL)
    
    # Handle inline code
    html = re.sub(r'`([^`]+)`', r'<code>\1</code>', html)
    
    # Convert headings - demote by 1 level (H1 -> H2, H2 -> H3, H3 -> H4)
    html = re.sub(r'^### (.+)$', r'<h4>\1</h4>', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
    html = re.sub(r'^# (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
    
    # Convert links
    html = re.sub(r'\[([^\]]+)\]\(([^\)]+)\)', r'<a href="\2">\1</a>', html)
    
    # Convert bold/italic (order matters - bold first)
    html = re.sub(r'\*\*([^\*]+)\*\*', r'<strong>\1</strong>', html)
    html = re.sub(r'\*([^\*]+)\*', r'<em>\1</em>', html)
    
    # Convert tables
    def convert_table(table_lines):
        rows = []
        for i, line in enumerate(table_lines):
            if re.match(r'^[\|\-\s:]+$', line):
                continue
            cells = [cell.strip() for cell in line.strip('|').split('|')]
            tag = 'th' if i == 0 else 'td'
            row = ''.join(f'<{tag}>{cell}</{tag}>' for cell in cells)
            rows.append(f'<tr>{row}</tr>')
        if rows:
            header = rows[0]
            body = ''.join(rows[1:])
            return f'<table><thead>{header}</thead><tbody>{body}</tbody></table>'
        return ''
    
    # Process line by line
    lines = html.split('\n')
    result = []
    in_list = False
    in_numbered_list = False
    in_table = False
    table_lines = []
    
    for line in lines:
        stripped = line.strip()
        
        # Check for table
        is_table_line = stripped.startswith('|') and stripped.endswith('|')
        
        if is_table_line:
            if not in_table:
                if in_list:
                    result.append('</ul>')
                    in_list = False
                if in_numbered_list:
                    result.append('</ol>')
                    in_numbered_list = False
                in_table = True
                table_lines = []
            table_lines.append(stripped)
            continue
        elif in_table:
            result.append(convert_table(table_lines))
            in_table = False
            table_lines = []
        
        # Skip if already HTML
        if stripped.startswith('<') and ('>' in stripped or stripped.startswith('</')):
            if in_list:
                result.append('</ul>')
                in_list = False
            if in_numbered_list:
                result.append('</ol>')
                in_numbered_list = False
            result.append(stripped)
        # Numbered list
        elif re.match(r'^\d+\.\s', stripped):
            if in_list:
                result.append('</ul>')
                in_list = False
            if not in_numbered_list:
                result.append('<ol>')
                in_numbered_list = True
            item = re.sub(r'^\d+\.\s*', '', stripped)
            result.append(f'<li>{item}</li>')
        # Bullet list
        elif stripped.startswith('- '):
            if in_numbered_list:
                result.append('</ol>')
                in_numbered_list = False
            if not in_list:
                result.append('<ul>')
                in_list = True
            result.append(f'<li>{stripped[2:]}</li>')
        # Empty line
        elif not stripped:
            if in_list:
                result.append('</ul>')
                in_list = False
            if in_numbered_list:
                result.append('</ol>')
                in_numbered_list = False
            result.append('')
        # Regular paragraph
        else:
            if in_list:
                result.append('</ul>')
                in_list = False
            if in_numbered_list:
                result.append('</ol>')
                in_numbered_list = False
            result.append(f'<p>{stripped}</p>')
    
    # Close any open lists
    if in_list:
        result.append('</ul>')
    if in_numbered_list:
        result.append('</ol>')
    if in_table and table_lines:
        result.append(convert_table(table_lines))
    
    html = '\n'.join(result)
    
    # Restore code blocks
    for i, block in enumerate(code_blocks):
        html = html.replace(f'__CODE_BLOCK_{i}__', block)
    
    # Clean up
    html = re.sub(r'\n{3,}', '\n\n', html)
    html = re.sub(r'<p></p>', '', html)
    
    return html.strip()


def convert_file(md_path: Path):
    """Convert a markdown file to HTML."""
    content = md_path.read_text(encoding='utf-8')
    meta, body = parse_frontmatter(content)
    
    if not meta:
        print(f"  Skipped (no frontmatter): {md_path.name}")
        return
    
    html_body = markdown_to_html(body)
    html_content = format_frontmatter(meta) + '\n\n' + html_body
    
    html_path = md_path.with_suffix('.html')
    html_path.write_text(html_content, encoding='utf-8')
    print(f"  Converted: {md_path.name} -> {html_path.name}")


def main():
    content_dir = Path("content/tools")
    md_files = sorted(content_dir.glob("*.md"))
    
    # Skip template
    md_files = [f for f in md_files if not f.name.startswith('_')]
    
    print(f"Converting {len(md_files)} markdown files to HTML...")
    print("-" * 50)
    
    for md_path in md_files:
        convert_file(md_path)
    
    print("-" * 50)
    print("Done! You can now delete the .md files and this script.")
    print("\nTo delete .md files (keep _template.md):")
    print("  rm content/tools/ai-*.md")
    print("\nTo delete this script:")
    print("  rm scripts/convert_md_to_html.py")


if __name__ == '__main__':
    main()

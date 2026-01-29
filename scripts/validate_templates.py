#!/usr/bin/env python3
"""
Validate content templates before pushing to WordPress.

Checks:
- Frontmatter fields are present
- SEO title/description length limits
- Slug format consistency
- Required body sections exist
"""
import sys
from pathlib import Path
import re

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.wp_pages import parse_frontmatter


def validate_template(file_path: Path) -> tuple[bool, list[str]]:
    """Validate a content template file.
    
    Returns:
        (is_valid, list_of_errors)
    """
    errors = []
    
    if not file_path.exists():
        return False, [f"File not found: {file_path}"]
    
    content = file_path.read_text(encoding='utf-8')
    meta, body = parse_frontmatter(content)
    
    # Check required frontmatter fields
    required_fields = ['title', 'slug', 'status', 'seo_title', 'seo_description', 'widget_endpoint']
    for field in required_fields:
        if not meta.get(field):
            errors.append(f"Missing required field: {field}")
    
    # Check slug format (should start with 'ai-')
    if meta.get('slug') and not meta['slug'].startswith('ai-'):
        errors.append(f"Slug should start with 'ai-': {meta['slug']}")
    
    # Check SEO title length (should be <= 60 chars)
    seo_title = meta.get('seo_title', '')
    if len(seo_title) > 60:
        errors.append(f"SEO title too long ({len(seo_title)} chars, max 60): {seo_title[:70]}...")
    
    # Check SEO description length (should be <= 155 chars)
    seo_description = meta.get('seo_description', '')
    if len(seo_description) > 155:
        errors.append(f"SEO description too long ({len(seo_description)} chars, max 155): {seo_description[:165]}...")
    
    # Check status is valid
    if meta.get('status') not in ['draft', 'publish']:
        errors.append(f"Invalid status: {meta.get('status')} (must be 'draft' or 'publish')")
    
    # Check body has required sections
    body_lower = body.lower()
    required_sections = ['how to use', 'faq', 'related tools']
    for section in required_sections:
        if section not in body_lower:
            errors.append(f"Missing required section: '{section}'")
    
    # Check FAQ has "Is this tool free?" question
    if 'faq' in body_lower and 'is this tool free' not in body_lower:
        errors.append("FAQ section should include 'Is this tool free?' question")
    
    return len(errors) == 0, errors


def main():
    """Validate all content templates."""
    templates_dir = Path(__file__).parent.parent / 'content' / 'tools'
    
    # Skip template file
    template_files = [
        templates_dir / 'pricing-calculator.md',
        templates_dir / 'status-page.md',
        templates_dir / 'error-decoder.md',
    ]
    
    all_valid = True
    for template_file in template_files:
        print(f"\nValidating: {template_file.name}")
        is_valid, errors = validate_template(template_file)
        
        if is_valid:
            print("  ✓ Valid")
        else:
            all_valid = False
            print("  ✗ Errors found:")
            for error in errors:
                print(f"    - {error}")
    
    if all_valid:
        print("\n✓ All templates are valid!")
        return 0
    else:
        print("\n✗ Some templates have errors. Fix them before pushing.")
        return 1


if __name__ == '__main__':
    sys.exit(main())

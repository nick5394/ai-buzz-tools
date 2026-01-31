#!/usr/bin/env python3
"""
Set up "AI Developer Tools" category and assign guide posts.

This script:
1. Creates the "AI Developer Tools" category (if it doesn't exist)
2. Assigns guide posts to this category
3. Optionally deletes empty old categories

Usage:
    python scripts/setup_developer_tools_category.py
    python scripts/setup_developer_tools_category.py --dry-run
    python scripts/setup_developer_tools_category.py --cleanup
"""
import argparse
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

from services.wordpress import WordPressService


# Category configuration
CATEGORY_CONFIG = {
    'name': 'AI Developer Tools',
    'slug': 'ai-developer-tools',
    'description': 'Free tools and guides for developers working with AI APIs. Compare pricing, check status, decode errors, and troubleshoot common issues.',
    'parent': 0,  # Top-level category
}

# AIOSEO meta for the category (needs to be set manually in WordPress admin)
CATEGORY_SEO = {
    'title': 'AI Developer Tools - Free Pricing Calculator, Status & Error Decoder',
    'description': 'Free tools for AI developers. Compare API costs, check if OpenAI is down, decode error messages. No signup required.',
}

# Posts to assign to this category (by slug)
GUIDE_POST_SLUGS = [
    'ai-openai-429-errors',
    'ai-openai-rate-limits',
    'ai-openai-vs-anthropic-pricing',
]

# Categories to potentially delete (if empty)
# Note: 'ai-tools-and-applications' and 'ai-guides' were deleted in Jan 2026 cleanup
CATEGORIES_TO_CLEANUP = []


def main():
    parser = argparse.ArgumentParser(description='Set up AI Developer Tools category')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without making changes')
    parser.add_argument('--cleanup', action='store_true', help='Delete empty old categories')
    parser.add_argument('--list-categories', action='store_true', help='List all categories')
    args = parser.parse_args()
    
    wp = WordPressService()
    
    if not wp.is_configured():
        print("❌ WordPress credentials not configured. Set WORDPRESS_USERNAME and WORDPRESS_APP_PASSWORD in .env")
        sys.exit(1)
    
    # List categories mode
    if args.list_categories:
        print("\n📋 All WordPress Categories:\n")
        categories = wp.list_categories()
        for cat in sorted(categories, key=lambda x: x.get('name', '')):
            parent_str = f" (parent: {cat.get('parent')})" if cat.get('parent') else " (top-level)"
            count = cat.get('count', 0)
            print(f"  [{cat['id']}] {cat['name']} ({cat['slug']}){parent_str} - {count} posts")
        return
    
    print("\n🚀 Setting up AI Developer Tools category\n")
    
    # Step 1: Create or get the category
    print("Step 1: Create/Get category...")
    
    existing = wp.get_category_by_slug(CATEGORY_CONFIG['slug'])
    if existing:
        category_id = existing['id']
        print(f"  ✅ Category already exists: {CATEGORY_CONFIG['name']} (ID: {category_id})")
    else:
        if args.dry_run:
            print(f"  🔍 [DRY RUN] Would create category: {CATEGORY_CONFIG['name']}")
            category_id = None
        else:
            category_id = wp.get_or_create_category(
                name=CATEGORY_CONFIG['name'],
                slug=CATEGORY_CONFIG['slug'],
                description=CATEGORY_CONFIG['description'],
                parent=CATEGORY_CONFIG['parent']
            )
            if category_id:
                print(f"  ✅ Created category: {CATEGORY_CONFIG['name']} (ID: {category_id})")
            else:
                print(f"  ❌ Failed to create category")
                sys.exit(1)
    
    # Step 2: Assign posts to the category
    print("\nStep 2: Assign posts to category...")
    
    for slug in GUIDE_POST_SLUGS:
        post = wp.get_post_by_slug(slug)
        if not post:
            print(f"  ⚠️  Post not found: {slug}")
            continue
        
        post_id = post['id']
        current_categories = post.get('categories', [])
        
        if category_id and category_id in current_categories:
            print(f"  ✅ Post already in category: {slug}")
            continue
        
        if args.dry_run:
            print(f"  🔍 [DRY RUN] Would assign post to category: {slug} (ID: {post_id})")
        else:
            if category_id:
                # Set only the new category (removes from old categories)
                result = wp.update_post(post_id, {'categories': [category_id]})
                if result:
                    print(f"  ✅ Assigned to category: {slug} (ID: {post_id})")
                else:
                    print(f"  ❌ Failed to assign: {slug}")
            else:
                print(f"  ⏭️  Skipping (no category ID): {slug}")
    
    # Step 3: Cleanup old categories (optional)
    if args.cleanup:
        print("\nStep 3: Cleanup old categories...")
        
        for cat_slug in CATEGORIES_TO_CLEANUP:
            cat = wp.get_category_by_slug(cat_slug)
            if not cat:
                print(f"  ⏭️  Category not found: {cat_slug}")
                continue
            
            post_count = cat.get('count', 0)
            if post_count > 0:
                print(f"  ⚠️  Category not empty ({post_count} posts): {cat['name']}")
                continue
            
            if args.dry_run:
                print(f"  🔍 [DRY RUN] Would delete empty category: {cat['name']} (ID: {cat['id']})")
            else:
                if wp.delete_category(cat['id']):
                    print(f"  ✅ Deleted empty category: {cat['name']}")
                else:
                    print(f"  ❌ Failed to delete: {cat['name']}")
    
    # Summary
    print("\n" + "=" * 50)
    print("📝 Summary")
    print("=" * 50)
    
    if category_id:
        print(f"\n✅ Category: {CATEGORY_CONFIG['name']}")
        print(f"   URL: https://www.ai-buzz.com/{CATEGORY_CONFIG['slug']}/")
        print(f"   ID: {category_id}")
    
    print("\n⚠️  Manual steps still required:")
    print("   1. Configure AIOSEO meta for category in WordPress Admin:")
    print(f"      - SEO Title: {CATEGORY_SEO['title']}")
    print(f"      - Meta Description: {CATEGORY_SEO['description']}")
    print("   2. Update navigation menu (Appearance > Menus)")
    print("   3. Configure breadcrumbs for tool Pages (optional)")
    
    if not args.cleanup:
        print("\n💡 Run with --cleanup to delete empty old categories")
    
    print()


if __name__ == '__main__':
    main()

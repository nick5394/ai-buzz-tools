#!/bin/bash
# Sync content templates to WordPress pages
# 
# Prerequisites:
# 1. WordPress credentials configured in .env file
# 2. Run: python scripts/wp_pages.py list (to verify connection)
#
# This script:
# 1. Backs up existing WordPress pages
# 2. Pushes content templates to WordPress

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKUP_DIR="$PROJECT_ROOT/content/wordpress-backup"

echo "=== WordPress Page Sync ==="
echo ""

# Check WordPress credentials
echo "Checking WordPress configuration..."
if ! python "$SCRIPT_DIR/wp_pages.py" list > /dev/null 2>&1; then
    echo "❌ Error: WordPress not configured."
    echo "   Set WORDPRESS_USERNAME and WORDPRESS_APP_PASSWORD in .env file"
    exit 1
fi

echo "✓ WordPress connection verified"
echo ""

# Create backup directory
mkdir -p "$BACKUP_DIR"
echo "Backup directory: $BACKUP_DIR"
echo ""

# Backup existing pages
echo "=== Step 1: Backing up existing WordPress pages ==="
for slug in "ai-pricing-calculator" "ai-status" "ai-error-decoder"; do
    echo "Backing up: $slug"
    if python "$SCRIPT_DIR/wp_pages.py" pull --slug "$slug" 2>/dev/null; then
        if [ -f "$PROJECT_ROOT/content/tools/$slug.md" ]; then
            mv "$PROJECT_ROOT/content/tools/$slug.md" "$BACKUP_DIR/$slug.md"
            echo "  ✓ Backed up to $BACKUP_DIR/$slug.md"
        fi
    else
        echo "  ⚠ Page not found in WordPress (will be created)"
    fi
done
echo ""

# Push templates
echo "=== Step 2: Pushing content templates to WordPress ==="
for template in "pricing-calculator" "status-page" "error-decoder"; do
    template_file="$PROJECT_ROOT/content/tools/$template.md"
    echo "Pushing: $template_file"
    
    if python "$SCRIPT_DIR/wp_pages.py" push --file "$template_file"; then
        echo "  ✓ Success"
    else
        echo "  ❌ Failed"
        exit 1
    fi
done
echo ""

# Optional: Take verification screenshots
echo "=== Step 3: Taking verification screenshots (optional) ==="
if python "$SCRIPT_DIR/wp_pages.py" verify --format pdf 2>/dev/null; then
    echo "✓ Screenshots captured successfully"
else
    echo "⚠ Screenshot capture skipped (playwright may not be installed)"
fi
echo ""

echo "=== Sync Complete ==="
echo ""
echo "Next steps:"
echo "1. Visit each page on ai-buzz.com to verify content"
echo "2. Verify widgets load correctly"
echo "3. Check SEO meta in WordPress admin (AIOSEO panel)"
echo "4. Review screenshots in screenshots/ directory (if captured)"
echo ""
echo "Backups saved to: $BACKUP_DIR"

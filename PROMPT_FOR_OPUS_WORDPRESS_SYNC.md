# Prompt for Opus: Complete WordPress Page Sync

## Context

I've implemented WordPress REST API integration for managing tool pages in the AI-Buzz Tools project. The code is complete and tested, but I need you to complete the actual sync of content templates to WordPress pages.

**What's Already Done:**

- WordPress service (`services/wordpress.py`) - REST API client
- CLI tool (`scripts/wp_pages.py`) - Commands: list, pull, push, diff
- Content templates (`content/tools/*.md`) - 3 templates ready with SEO optimized
- Validation script (`scripts/validate_templates.py`) - All templates pass validation ✓
- Sync script (`scripts/sync_wordpress_pages.sh`) - Automated sync ready
- Documentation - Setup guides created

**What Needs to Be Done:**

1. Get WordPress credentials from the other repo's `.env` file
2. Configure credentials in this repo's `.env` file
3. Test WordPress connection
4. Backup existing WordPress pages
5. Push content templates to WordPress
6. Verify pages display correctly

## Your Task

Complete the WordPress page sync by following these steps:

### Step 1: Get WordPress Credentials

I have WordPress credentials in another repository. You'll need to:

- Ask me for the path to the other repo, OR
- I'll provide the credentials directly

The credentials needed are:

- `WORDPRESS_SITE_URL` (should be `https://www.ai-buzz.com`)
- `WORDPRESS_USERNAME` (WordPress username)
- `WORDPRESS_APP_PASSWORD` (Application password, format: `xxxx xxxx xxxx xxxx xxxx xxxx`)

### Step 2: Configure .env File

1. Check if `.env` file exists in this repo root
2. If not, copy from `env.example`:
   ```bash
   cp env.example .env
   ```
3. Add WordPress credentials to `.env`:
   ```bash
   WORDPRESS_SITE_URL=https://www.ai-buzz.com
   WORDPRESS_USERNAME=<from other repo>
   WORDPRESS_APP_PASSWORD=<from other repo>
   ```

### Step 3: Test Connection

Run the list command to verify WordPress connection:

```bash
python scripts/wp_pages.py list
```

Expected: Table showing WordPress pages with ID, slug, status, title.

If you see "Error: WordPress not configured", check the `.env` file.

### Step 4: Verify Existing Pages

From the `list` output, verify these slugs exist:

- `ai-pricing-calculator`
- `ai-status` (or `ai-status-page` - check which one)
- `ai-error-decoder`

Note: The template file is `status-page.md` but the slug might be `ai-status` or `ai-status-page`. Check the actual WordPress slug.

### Step 5: Backup Existing Pages (Optional but Recommended)

Before pushing, backup existing WordPress content:

```bash
mkdir -p content/wordpress-backup

# Backup each page
python scripts/wp_pages.py pull --slug ai-pricing-calculator
mv content/tools/ai-pricing-calculator.md content/wordpress-backup/ 2>/dev/null || true

python scripts/wp_pages.py pull --slug ai-status
mv content/tools/ai-status.md content/wordpress-backup/ 2>/dev/null || true

# If ai-status doesn't exist, try ai-status-page
python scripts/wp_pages.py pull --slug ai-status-page
mv content/tools/ai-status-page.md content/wordpress-backup/ 2>/dev/null || true

python scripts/wp_pages.py pull --slug ai-error-decoder
mv content/tools/ai-error-decoder.md content/wordpress-backup/ 2>/dev/null || true
```

### Step 6: Validate Templates

Run validation to ensure templates are ready:

```bash
python scripts/validate_templates.py
```

Expected: All 3 templates show "✓ Valid"

### Step 7: Push Templates to WordPress

**Option A: Use automated script (recommended)**

```bash
./scripts/sync_wordpress_pages.sh
```

**Option B: Manual push**

```bash
python scripts/wp_pages.py push --file content/tools/pricing-calculator.md
python scripts/wp_pages.py push --file content/tools/status-page.md
python scripts/wp_pages.py push --file content/tools/error-decoder.md
```

Expected output for each:

- "Created page XXX: ai-pricing-calculator" (if new)
- "Updated page XXX: ai-pricing-calculator" (if existing)
- "Updated AIOSEO meta"

### Step 8: Verify Slug Mapping

After pushing, check if the `status-page.md` template's slug (`ai-status`) matches WordPress. If WordPress has `ai-status-page` instead, you may need to:

1. Update the template's slug to match WordPress, OR
2. Update WordPress slug to match template

The template currently has `slug: "ai-status"` - verify this matches WordPress.

### Step 9: Post-Sync Verification

After pushing, verify:

1. **Check WordPress pages exist:**

   ```bash
   python scripts/wp_pages.py list | grep -E "ai-pricing-calculator|ai-status|ai-error-decoder"
   ```

2. **Verify pages are published:**
   - Status should be "publish" (not "draft")
   - If draft, update template `status: "publish"` and push again

3. **Manual verification needed** (I'll do this):
   - Visit pages on ai-buzz.com
   - Verify widgets load
   - Check SEO meta in WordPress admin

## Important Notes

- **Widget Embedding**: Widgets are embedded via Bricks Builder Code elements in WordPress, not via the CLI. The CLI only syncs page content.
- **SEO Meta**: The push command updates AIOSEO meta automatically if `seo_title` and `seo_description` are in the template frontmatter.
- **Backups**: Backups are saved to `content/wordpress-backup/` if you run the backup step.
- **Slug Consistency**: Template files are named `pricing-calculator.md` but slugs are `ai-pricing-calculator`. This is fine - the CLI reads slugs from frontmatter, not filenames.

## Files Reference

- **Templates**: `content/tools/pricing-calculator.md`, `status-page.md`, `error-decoder.md`
- **CLI Tool**: `scripts/wp_pages.py`
- **Validation**: `scripts/validate_templates.py`
- **Sync Script**: `scripts/sync_wordpress_pages.sh`
- **Setup Guide**: `WORDPRESS_SETUP.md` (for reference)

## Expected Output

After successful sync, you should see:

```
=== WordPress Page Sync ===

Checking WordPress configuration...
✓ WordPress connection verified

=== Step 1: Backing up existing WordPress pages ===
Backing up: ai-pricing-calculator
  ✓ Backed up to content/wordpress-backup/ai-pricing-calculator.md
...

=== Step 2: Pushing content templates to WordPress ===
Pushing: content/tools/pricing-calculator.md
Created page 123: ai-pricing-calculator
  ✓ Success
Updated AIOSEO meta
...

=== Sync Complete ===
```

## Questions to Ask Me

If you encounter issues:

1. **Credentials not working**: Ask me to verify the credentials from the other repo
2. **Slug mismatch**: Ask which slug WordPress actually uses for the status page
3. **Page not found**: Ask if the pages exist in WordPress or need to be created
4. **AIOSEO errors**: Ask if AIOSEO plugin is installed and active in WordPress

## Success Criteria

✅ WordPress connection works (`list` command shows pages)
✅ All 3 templates pushed successfully
✅ Pages show status "publish" (not draft)
✅ AIOSEO meta updated (check WordPress admin if possible)
✅ Backup created (if pages existed before)

Once you complete these steps, I'll manually verify the pages display correctly on ai-buzz.com.

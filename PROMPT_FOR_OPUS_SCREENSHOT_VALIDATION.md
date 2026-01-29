# Prompt for Opus: Screenshot/PDF Validation for WordPress Pages

## Context

I've implemented WordPress page sync functionality that pushes content templates to WordPress. After syncing, I need a way to verify that pages display correctly with widgets loaded.

**Current State:**

- WordPress sync CLI tool (`scripts/wp_pages.py`) - working ✓
- Screenshot script started (`scripts/screenshot_pages.py`) - basic structure exists
- Need: Full-page capture (PDF or high-res image) for LLM context

**Goal:**
Create a validation step that captures full-page screenshots/PDFs of WordPress pages so LLMs can verify:

- Content displays correctly
- Widgets load and function
- Layout is correct
- Mobile responsiveness (optional)

## Requirements

### 1. Capture Format

**Option A: PDF (Preferred)**

- Single PDF per page with full content
- Easy for LLMs to read and analyze
- Can include multiple pages (desktop + mobile views)

**Option B: High-Resolution Image**

- Full-page screenshot at high DPI (2x or 3x)
- PNG format for quality
- Single image per page

**Decision Needed:** Which format? PDF seems better for LLM analysis.

### 2. Integration Points

The screenshot/PDF capture should be:

1. **Part of sync workflow** - Run automatically after `wp_pages.py push`
2. **Standalone command** - Can run independently for verification
3. **CI/CD integration** - Can be run in automated tests

### 3. What to Capture

For each WordPress page:

- **Desktop view** (1920x1080 or similar)
- **Mobile view** (375px width) - optional but recommended
- **Full page** (not just viewport - scroll to capture everything)
- **Wait for widgets** - Ensure widgets load before capture

### 4. Output Structure

```
screenshots/
  ai-pricing-calculator/
    desktop.pdf (or .png)
    mobile.pdf (or .png)
  ai-status/
    desktop.pdf
    mobile.pdf
  ai-error-decoder/
    desktop.pdf
    mobile.pdf
```

OR single file per page:

```
screenshots/
  ai-pricing-calculator.pdf
  ai-status.pdf
  ai-error-decoder.pdf
```

### 5. Technical Implementation

**Current Script:** `scripts/screenshot_pages.py`

- Uses Playwright (good choice)
- Basic structure exists
- Needs: PDF export, mobile view, better integration

**Enhancements Needed:**

1. **PDF Export**

   ```python
   # Playwright can generate PDFs
   await page.pdf(path="output.pdf", format="A4", print_background=True)
   ```

2. **Mobile View Capture**

   ```python
   # Set mobile viewport
   context = await browser.new_context(
       viewport={"width": 375, "height": 667},
       user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)..."
   )
   ```

3. **Full Page Capture**
   - Ensure widgets load (wait for network idle + delay)
   - Scroll to bottom to trigger lazy loading
   - Capture full page height

4. **Integration with Sync Script**
   - Add `--screenshot` flag to `wp_pages.py push`
   - Or create separate `wp_pages.py verify` command
   - Or add to `sync_wordpress_pages.sh`

## Your Task

Plan the implementation of screenshot/PDF validation:

### Step 1: Choose Format

- Decide: PDF vs PNG vs both
- Consider: LLM readability, file size, ease of analysis

### Step 2: Enhance Screenshot Script

- Add PDF export capability
- Add mobile view capture
- Improve widget loading detection
- Better error handling
- Progress output

### Step 3: Integration Options

- Option A: Add to `sync_wordpress_pages.sh` (automatic after push)
- Option B: Add `verify` command to `wp_pages.py`
- Option C: Standalone script (current approach)
- **Recommendation:** Option B - `wp_pages.py verify --screenshot`

### Step 4: Validation Workflow

After syncing pages, run:

```bash
# Option 1: Automatic (if integrated into sync script)
./scripts/sync_wordpress_pages.sh

# Option 2: Manual verification
python scripts/wp_pages.py verify --screenshot

# Option 3: Individual page
python scripts/wp_pages.py verify --slug ai-pricing-calculator --screenshot
```

### Step 5: LLM Analysis Integration

The captured PDFs/images should be:

- Saved to `screenshots/` directory
- Named consistently (`{slug}-desktop.pdf`, `{slug}-mobile.pdf`)
- Included in git (or .gitignore if too large)
- Available for LLM context in future conversations

## Questions to Consider

1. **PDF vs PNG:** Which is better for LLM analysis?
   - PDF: Better for text extraction, multi-page support
   - PNG: Better for visual inspection, smaller files
   - **Suggestion:** PDF for desktop, PNG for mobile (or both)

2. **File Size:** Should screenshots be committed to git?
   - If yes: Use PDF (smaller) or compress PNGs
   - If no: Add to `.gitignore`, generate on-demand

3. **Mobile Views:** Always capture mobile or make it optional?
   - **Suggestion:** Make optional flag `--mobile` (default: desktop only)

4. **Widget Loading:** How to ensure widgets are fully loaded?
   - Current: 3 second delay
   - Better: Wait for specific selectors or network idle
   - **Suggestion:** Wait for widget container + network idle + 2s buffer

5. **Error Handling:** What if page fails to load?
   - Retry logic?
   - Partial capture?
   - Error reporting?

## Success Criteria

✅ Can capture full-page PDF/image of WordPress pages
✅ Captures both desktop and mobile views (optional)
✅ Waits for widgets to fully load
✅ Integrates with sync workflow
✅ Outputs are suitable for LLM analysis
✅ Can run standalone or as part of sync

## Files to Modify/Create

1. **Enhance:** `scripts/screenshot_pages.py`
   - Add PDF export
   - Add mobile view support
   - Improve widget detection

2. **Create:** `scripts/verify_pages.py` (optional)
   - Wrapper that combines screenshot + validation
   - Or integrate into `wp_pages.py`

3. **Update:** `scripts/wp_pages.py`
   - Add `verify` command with `--screenshot` flag

4. **Update:** `scripts/sync_wordpress_pages.sh`
   - Add screenshot step after push (optional)

5. **Update:** `.gitignore`
   - Decide if screenshots should be committed

6. **Update:** Documentation
   - Add screenshot verification to testing checklist
   - Update `WORDPRESS_SETUP.md` with verification steps

## Example Output

After running verification, should see:

```
=== WordPress Page Verification ===

Taking screenshots...
  📸 ai-pricing-calculator (desktop)... ✓ Saved to screenshots/ai-pricing-calculator-desktop.pdf
  📸 ai-pricing-calculator (mobile)... ✓ Saved to screenshots/ai-pricing-calculator-mobile.pdf
  📸 ai-status (desktop)... ✓ Saved to screenshots/ai-status-desktop.pdf
  📸 ai-status (mobile)... ✓ Saved to screenshots/ai-status-mobile.pdf
  📸 ai-error-decoder (desktop)... ✓ Saved to screenshots/ai-error-decoder-desktop.pdf
  📸 ai-error-decoder (mobile)... ✓ Saved to screenshots/ai-error-decoder-mobile.pdf

Verification complete. Screenshots saved to screenshots/
```

## Next Steps

1. Review this prompt and plan the implementation
2. Decide on format (PDF vs PNG vs both)
3. Enhance screenshot script with chosen format
4. Integrate into workflow (sync script or separate command)
5. Test with actual WordPress pages
6. Document usage in setup guide

## Reference

- Current screenshot script: `scripts/screenshot_pages.py`
- WordPress sync script: `scripts/sync_wordpress_pages.sh`
- WordPress CLI: `scripts/wp_pages.py`
- Playwright PDF docs: https://playwright.dev/python/docs/api/class-page#page-pdf

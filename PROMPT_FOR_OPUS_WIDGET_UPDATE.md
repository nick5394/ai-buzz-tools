# Prompt for Opus: Update WordPress Pages with JS Embed Script & Validate

## Context

I just implemented a JavaScript widget embed system to replace the old PHP `file_get_contents()` approach. The new system uses a universal loader script (`embed.js`) that fetches widgets client-side, bypassing WordPress caching entirely.

### What Was Implemented

1. **Universal Embed Script** (`api/embed.py`)
   - Serves `/embed.js` endpoint
   - Reads `data-tool` attribute from script tag
   - Fetches widget HTML dynamically
   - Handles Render cold starts with retry logic

2. **Updated Documentation**
   - `WORDPRESS_SETUP.md` - Shows simple method (add script tag directly in page content)
   - `content/tools/_template.md` - Updated with embed code example
   - All docs updated to reflect JS approach

### Current State

- **3 WordPress pages** need updating:
  - `/ai-pricing-calculator` - needs `data-tool="pricing"`
  - `/ai-status` - needs `data-tool="status"`
  - `/ai-error-decoder` - needs `data-tool="error-decoder"`

- **Widget endpoints** are working:
  - `https://ai-buzz-tools.onrender.com/pricing/widget`
  - `https://ai-buzz-tools.onrender.com/status/widget`
  - `https://ai-buzz-tools.onrender.com/error-decoder/widget`

- **Embed script** is deployed:
  - `https://ai-buzz-tools.onrender.com/embed.js`

### Current Widget Embedding

Pages currently use PHP `file_get_contents()` in Bricks Builder Code elements. This needs to be replaced with the simple script tag approach.

## Your Task

Create a plan to:

1. **Update WordPress pages** with the new JS embed script
2. **Validate widgets load correctly** on all pages
3. **Take screenshots** for verification
4. **Document any issues** found during validation

## Embed Script Format

The script tag to add to each page:

```html
<script src="https://ai-buzz-tools.onrender.com/embed.js" data-tool="[tool-name]"></script>
```

**Tool names:**
- `pricing` - for Pricing Calculator page
- `status` - for Status Page
- `error-decoder` - for Error Decoder page

## WordPress Page Update Methods

### Option 1: WordPress Block Editor (Recommended)

1. Edit page in WordPress admin
2. Add an **HTML block** where you want the widget
3. Paste the script tag
4. Update/Publish page

### Option 2: Classic Editor

1. Edit page
2. Switch to **Text** mode (not Visual)
3. Paste script tag where widget should appear
4. Update page

### Option 3: Bricks Builder (if still using)

1. Edit page in Bricks
2. Replace existing Code element PHP with script tag
3. Save/Update page

## Validation Checklist

After updating each page, verify:

- [ ] Script tag is present in page HTML (view page source)
- [ ] Widget container appears (check for loading spinner)
- [ ] Widget loads successfully (no "temporarily unavailable" message)
- [ ] Widget is functional (can interact with it)
- [ ] Widget styling matches expected design
- [ ] Mobile responsive (test at 375px width)
- [ ] No JavaScript errors in browser console

## Screenshot Script

There's an existing screenshot script at `scripts/screenshot_pages.py` that:

- Takes screenshots/PDFs of WordPress pages
- Waits for widgets to load (handles cold starts)
- Interacts with widgets to show active state
- Saves to `screenshots/` directory

**Usage:**
```bash
# Screenshot all pages
python scripts/screenshot_pages.py --all --format png

# Screenshot specific page
python scripts/screenshot_pages.py --slug ai-pricing-calculator --format png

# Mobile screenshots
python scripts/screenshot_pages.py --all --format png --mobile
```

**Note:** The screenshot script currently looks for widget containers by ID:
- `#pricing-calculator-widget`
- `#status-page-widget`
- `#error-decoder-widget`

These should still work with the new JS embed system since the widgets inject themselves with the same IDs.

## Pages to Update

### 1. AI Pricing Calculator (`/ai-pricing-calculator`)

**Current:** PHP Code element fetching `/pricing/widget`
**Update to:** 
```html
<script src="https://ai-buzz-tools.onrender.com/embed.js" data-tool="pricing"></script>
```

**Validation:**
- Widget shows pricing calculator interface
- Can enter token amounts
- "Calculate Costs" button works
- Results table displays correctly

### 2. AI Status Page (`/ai-status`)

**Current:** PHP Code element fetching `/status/widget`
**Update to:**
```html
<script src="https://ai-buzz-tools.onrender.com/embed.js" data-tool="status"></script>
```

**Validation:**
- Widget shows status cards for providers
- Status indicators (green/red) display correctly
- "Last checked" timestamp updates
- Auto-refresh works (if implemented)

### 3. AI Error Decoder (`/ai-error-decoder`)

**Current:** PHP Code element fetching `/error-decoder/widget`
**Update to:**
```html
<script src="https://ai-buzz-tools.onrender.com/embed.js" data-tool="error-decoder"></script>
```

**Validation:**
- Widget shows error input textarea
- Can paste error message
- "Decode Error" button works
- Explanation and fix steps display correctly

## Plan Structure

Provide a detailed plan with:

1. **Pre-Update Checklist**
   - Verify embed.js endpoint is accessible
   - Test widget endpoints return HTML
   - Check WordPress credentials are configured
   - Backup current page content (optional but recommended)

2. **Update Steps** (for each page)
   - Exact steps to update the page
   - Where to place the script tag
   - How to verify script tag is in HTML output

3. **Validation Steps**
   - Manual browser testing checklist
   - Screenshot capture commands
   - What to look for in screenshots
   - How to verify widgets are functional

4. **Troubleshooting Guide**
   - Common issues and solutions
   - How to check if embed.js loaded
   - How to verify widget fetch succeeded
   - What to do if widget doesn't appear

5. **Post-Update Tasks**
   - Update content templates with embed code (if needed)
   - Document any WordPress-specific notes
   - Update any internal documentation

## Important Notes

- **No cache clearing needed** - JS approach bypasses WordPress caching automatically
- **Script tag placement** - Can go anywhere in page content, widget will inject itself
- **Multiple widgets** - Can add multiple script tags on same page if needed
- **Cold starts** - Widget retries automatically if API is cold (up to 30s delay)
- **Error handling** - Widget shows "temporarily unavailable" if fetch fails after retry

## Expected Outcomes

After completing the plan:

1. All 3 WordPress pages updated with JS embed script
2. Widgets load and function correctly on all pages
3. Screenshots captured showing widgets working
4. Documentation updated with any WordPress-specific notes
5. Clear process documented for future widget updates

## Questions to Address

- Should we update the content templates (`content/tools/*.md`) to include the embed code?
- How do we handle pages that might have custom layouts in Bricks?
- Should we test on staging first, or go straight to production?
- What's the rollback plan if something breaks?

## Output Format

Provide:

- **Numbered step-by-step plan** for updating each page
- **Validation checklist** with specific things to verify
- **Screenshot commands** to run after updates
- **Troubleshooting section** for common issues
- **Success criteria** - how we know it's working

Focus on practical, actionable steps that ensure widgets work correctly and can be validated with screenshots.

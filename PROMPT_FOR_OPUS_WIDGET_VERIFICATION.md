# Prompt for Opus: Verify WordPress Widget Embed Implementation

## Context

The WordPress pages have been updated to use a new JavaScript embed system (`embed.js`) instead of the old PHP `file_get_contents()` approach. All content templates have been updated and pushed to WordPress via REST API.

### What Was Implemented

1. **Content Templates Updated** (`content/tools/`)
   - `pricing-calculator.md` - Added `<script src="https://ai-buzz-tools.onrender.com/embed.js" data-tool="pricing"></script>`
   - `status-page.md` - Added `<script src="https://ai-buzz-tools.onrender.com/embed.js" data-tool="status"></script>`
   - `error-decoder.md` - Added `<script src="https://ai-buzz-tools.onrender.com/embed.js" data-tool="error-decoder"></script>`
   - `_template.md` - Updated with new embed pattern for future tools

2. **WordPress Pages Updated** (via REST API)
   - `/ai-pricing-calculator` - Page 14695 updated
   - `/ai-status` - Page 14733 updated
   - `/ai-error-decoder` - Page 14735 updated

3. **Backup Files Created**
   - `content/tools/ai-pricing-calculator.md` - Pulled from WordPress before changes
   - `content/tools/ai-status.md` - Pulled from WordPress before changes
   - `content/tools/ai-error-decoder.md` - Pulled from WordPress before changes

### Current Status

- **Pricing Calculator**: Script tag confirmed in HTML source
- **Status Page**: Script tag confirmed in WordPress REST API post content
- **Error Decoder**: Script tag confirmed in WordPress REST API post content

**Note**: Status and Error Decoder pages may need Bricks Builder "Post Content" element to render the script tag, as Bricks may be using custom layouts instead of post content.

## Your Task

Create a comprehensive verification plan to ensure:

1. **Script tags are present** in the rendered HTML of all pages
2. **Widgets load correctly** on all pages
3. **Widgets are functional** (interactive elements work)
4. **No JavaScript errors** occur
5. **Mobile responsive** design works
6. **Bricks Builder compatibility** - verify if Post Content elements are needed

## Verification Methods

### Method 1: Browser Automation (MCP Browser Tools)

Use `cursor-browser-extension` MCP tools to:
- Navigate to each page
- Take snapshots to inspect DOM
- Check for script tags and widget containers
- Interact with widgets to verify functionality
- Check browser console for errors

### Method 2: Screenshot Script

Use the existing screenshot script:
```bash
python scripts/screenshot_pages.py --all --format png
python scripts/screenshot_pages.py --all --format png --mobile
```

This script:
- Waits for widgets to load (handles Render cold starts)
- Interacts with widgets before capture
- Saves screenshots to `screenshots/` directory

### Method 3: Manual Verification

- Visit each page in browser
- View page source to check for script tags
- Open browser DevTools console to check for errors
- Test widget functionality manually
- Test mobile responsive design (Chrome DevTools 375px)

## Pages to Verify

### 1. AI Pricing Calculator (`/ai-pricing-calculator`)

**Expected:**
- Script tag: `<script src="https://ai-buzz-tools.onrender.com/embed.js" data-tool="pricing"></script>`
- Widget container: `#ai-buzz-widget-container-pricing` or `#pricing-calculator-widget`
- Widget shows: Token input fields, preset buttons, "Calculate Costs" button
- Functionality: Can enter tokens, click calculate, see results table

**Verification Steps:**
1. Navigate to `https://www.ai-buzz.com/ai-pricing-calculator`
2. Check page source for script tag
3. Verify widget container appears
4. Test: Enter 1M input tokens, 0.5M output tokens
5. Click "Calculate Costs" button
6. Verify results table displays
7. Check browser console for errors
8. Test mobile viewport (375px)

### 2. AI Status Page (`/ai-status`)

**Expected:**
- Script tag: `<script src="https://ai-buzz-tools.onrender.com/embed.js" data-tool="status"></script>`
- Widget container: `#ai-buzz-widget-container-status` or `#status-page-widget`
- Widget shows: Status cards for providers (OpenAI, Anthropic, Google, Mistral)
- Functionality: Status indicators (green/red), "last checked" timestamps

**Verification Steps:**
1. Navigate to `https://www.ai-buzz.com/ai-status`
2. Check page source for script tag (may need to check WordPress REST API if not in HTML)
3. Verify widget container appears
4. Verify status cards display for all providers
5. Check that status indicators show (green/red)
6. Verify "last checked" timestamps are present
7. Check browser console for errors
8. Test mobile viewport (375px)

**Potential Issue**: If script tag not in HTML, Bricks Builder may need "Post Content" element added.

### 3. AI Error Decoder (`/ai-error-decoder`)

**Expected:**
- Script tag: `<script src="https://ai-buzz-tools.onrender.com/embed.js" data-tool="error-decoder"></script>`
- Widget container: `#ai-buzz-widget-container-error-decoder` or `#error-decoder-widget`
- Widget shows: Error input textarea, "Decode Error" button
- Functionality: Can paste error, get explanation and fix steps

**Verification Steps:**
1. Navigate to `https://www.ai-buzz.com/ai-error-decoder`
2. Check page source for script tag (may need to check WordPress REST API if not in HTML)
3. Verify widget container appears
4. Test: Paste "rate limit exceeded" error message
5. Click "Decode Error" button
6. Verify explanation and fix steps display
7. Check browser console for errors
8. Test mobile viewport (375px)

**Potential Issue**: If script tag not in HTML, Bricks Builder may need "Post Content" element added.

## Verification Checklist

For each page, verify:

- [ ] Script tag present in page HTML source
- [ ] Script tag has correct `data-tool` attribute
- [ ] `embed.js` loads without errors (check Network tab)
- [ ] Widget container appears (`#ai-buzz-widget-container-{tool}`)
- [ ] Widget HTML loads (no "temporarily unavailable" message)
- [ ] Widget displays correctly (all UI elements visible)
- [ ] Widget is interactive (buttons/inputs work)
- [ ] No JavaScript console errors
- [ ] Mobile responsive (test at 375px width)
- [ ] Widget handles Render cold starts (retry logic works)

## Troubleshooting Guide

### Script Tag Not in HTML

**Symptom**: Script tag exists in WordPress REST API but not in rendered HTML

**Possible Causes**:
1. Bricks Builder using custom layout (not rendering post content)
2. WordPress cache not cleared
3. Bricks "Post Content" element missing

**Solutions**:
1. Check if page uses Bricks Builder custom layout
2. Add "Post Content" element in Bricks Builder where widget should appear
3. Clear WordPress cache (SiteGround Optimizer or similar)
4. Check Bricks Builder settings for post content rendering

### Widget Doesn't Load

**Symptom**: Script tag present but widget container empty or shows error

**Possible Causes**:
1. Render API cold start (10-30s delay)
2. Widget endpoint returns 404
3. CORS or network error
4. JavaScript error in embed.js

**Solutions**:
1. Wait 30 seconds for Render cold start
2. Check browser console for errors
3. Verify widget endpoint returns HTML: `curl https://ai-buzz-tools.onrender.com/{tool}/widget`
4. Check Network tab for failed requests
5. Verify `embed.js` loads correctly

### Widget Shows "Temporarily Unavailable"

**Symptom**: Widget container shows error message after retry

**Possible Causes**:
1. Widget endpoint down or returning error
2. Render API timeout
3. Network connectivity issue

**Solutions**:
1. Check widget endpoint directly: `curl https://ai-buzz-tools.onrender.com/{tool}/widget`
2. Verify API is deployed and running
3. Check Render dashboard for service status
4. Wait and retry (may be temporary cold start issue)

## Expected Outcomes

After verification, document:

1. **Status of each page**:
   - Script tag present: Yes/No
   - Widget loads: Yes/No
   - Widget functional: Yes/No
   - Issues found: List any problems

2. **Screenshots captured**:
   - Desktop screenshots for all pages
   - Mobile screenshots for all pages (if possible)
   - Any error states captured

3. **Issues identified**:
   - Bricks Builder configuration needed
   - WordPress cache clearing needed
   - API endpoint issues
   - JavaScript errors

4. **Next steps**:
   - What needs to be fixed
   - How to fix identified issues
   - Any WordPress admin actions required

## Tools Available

### MCP Browser Extension
- `browser_navigate` - Navigate to pages
- `browser_snapshot` - Inspect DOM structure
- `browser_console_messages` - Check for JavaScript errors
- `browser_take_screenshot` - Capture visual state
- `browser_click`, `browser_type` - Interact with widgets

### Screenshot Script
- `python scripts/screenshot_pages.py --all --format png`
- `python scripts/screenshot_pages.py --slug {slug} --format png --mobile`
- Handles widget loading waits automatically
- Interacts with widgets before capture

### WordPress CLI
- `python scripts/wp_pages.py pull --slug {slug}` - Pull current content
- `python scripts/wp_pages.py diff --slug {slug}` - Compare local vs remote
- `python scripts/wp_pages.py list` - List all pages

### Direct Verification
- WordPress REST API: `https://www.ai-buzz.com/wp-json/wp/v2/pages?slug={slug}`
- Widget endpoints: `https://ai-buzz-tools.onrender.com/{tool}/widget`
- Embed script: `https://ai-buzz-tools.onrender.com/embed.js`

## Plan Structure

Provide a detailed verification plan with:

1. **Pre-Verification Setup**
   - Check WordPress credentials configured
   - Verify screenshot script dependencies installed
   - Test MCP browser tools accessible

2. **Verification Steps** (for each page)
   - Navigate to page
   - Check script tag presence
   - Verify widget loads
   - Test functionality
   - Capture screenshots
   - Check for errors

3. **Documentation**
   - Record findings for each page
   - Capture screenshots
   - Document any issues found
   - Provide recommendations

4. **Issue Resolution**
   - If Bricks Builder issue: Steps to add Post Content element
   - If cache issue: How to clear WordPress cache
   - If API issue: How to verify/debug endpoints

Focus on practical, actionable verification steps that can be executed systematically.

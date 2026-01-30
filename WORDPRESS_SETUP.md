# WordPress Integration Setup Guide

## Prerequisites

Before syncing content templates to WordPress, you need to configure WordPress credentials.

### Step 1: Create WordPress Application Password

1. Log in to WordPress Admin: `https://www.ai-buzz.com/wp-admin`
2. Go to **Users > Profile**
3. Scroll to **Application Passwords** section
4. Create a new password:
   - Name: `ai-buzz-tools`
   - Click **Add New Application Password**
5. Copy the generated password (format: `xxxx xxxx xxxx xxxx xxxx xxxx`)

### Step 2: Configure Environment Variables

Create a `.env` file in the project root (if it doesn't exist):

```bash
cp env.example .env
```

Edit `.env` and add your WordPress credentials:

```bash
WORDPRESS_SITE_URL=https://www.ai-buzz.com
WORDPRESS_USERNAME=your-wordpress-username
WORDPRESS_APP_PASSWORD=xxxx xxxx xxxx xxxx xxxx xxxx
```

**Important:** Never commit the `.env` file to git. It's already in `.gitignore`.

### Step 3: Verify Connection

Test the WordPress connection:

```bash
python scripts/wp_pages.py list
```

Expected output: A table showing all WordPress pages with ID, slug, status, and title.

If you see "Error: WordPress not configured", check your `.env` file.

## Syncing Pages

### Option 1: Automated Script (Recommended)

Run the sync script:

```bash
./scripts/sync_wordpress_pages.sh
```

This will:

1. Back up existing WordPress pages to `content/wordpress-backup/`
2. Push all three content templates to WordPress
3. Update SEO meta via AIOSEO

### Option 2: Manual Steps

**Backup existing pages:**

```bash
mkdir -p content/wordpress-backup
python scripts/wp_pages.py pull --slug ai-pricing-calculator
mv content/tools/ai-pricing-calculator.md content/wordpress-backup/
python scripts/wp_pages.py pull --slug ai-status
mv content/tools/ai-status.md content/wordpress-backup/
python scripts/wp_pages.py pull --slug ai-error-decoder
mv content/tools/ai-error-decoder.md content/wordpress-backup/
```

**Push templates:**

```bash
python scripts/wp_pages.py push --file content/tools/pricing-calculator.md
python scripts/wp_pages.py push --file content/tools/status-page.md
python scripts/wp_pages.py push --file content/tools/error-decoder.md
```

## Verification Checklist

After syncing, verify:

- [ ] Visit `https://www.ai-buzz.com/ai-pricing-calculator` - content displays correctly
- [ ] Visit `https://www.ai-buzz.com/ai-status` - content displays correctly
- [ ] Visit `https://www.ai-buzz.com/ai-error-decoder` - content displays correctly
- [ ] Widgets load on all three pages (embedded via script tag)
- [ ] SEO meta updated in WordPress admin (check AIOSEO panel)
- [ ] Pages are published (not draft)

## Troubleshooting

### "WordPress not configured" Error

- Check `.env` file exists and has correct values
- Verify `WORDPRESS_USERNAME` matches your WordPress username
- Verify `WORDPRESS_APP_PASSWORD` is the full password (with spaces)

### "Page not found" Error

- Run `python scripts/wp_pages.py list` to see all pages
- Verify the slug matches (e.g., `ai-status` vs `ai-status-page`)

### SEO Meta Not Updating

- Check WordPress admin > Pages > [page] > AIOSEO panel
- Verify AIOSEO plugin is installed and active
- Check server logs for AIOSEO API errors

### Widget Not Loading

- Widget embedding is handled directly in page content (see Widget Embedding section)
- Verify script tag is correctly placed in page content
- Check that `data-tool` attribute matches a valid tool name
- See [Widget Embedding](#widget-embedding) section below for details

## CLI Commands Reference

```bash
# List all WordPress pages
python scripts/wp_pages.py list

# Pull page from WordPress to local HTML
python scripts/wp_pages.py pull --slug ai-pricing-calculator

# Push local HTML to WordPress (as page)
python scripts/wp_pages.py push --file content/tools/ai-pricing-calculator.html

# Push all pages
python scripts/wp_pages.py push-all

# Push local HTML as WordPress POST (for guides)
python scripts/wp_pages.py push-post --file content/guides/ai-openai-429-errors.html

# Push all guides as posts
python scripts/wp_pages.py push-guides

# Show diff info (basic)
python scripts/wp_pages.py diff --slug ai-pricing-calculator

# Validate templates before pushing
python scripts/validate_templates.py
```

## Content Architecture

### Pages vs Posts

**Tool Pages (WordPress Pages)** - `content/tools/`
- Interactive tools with widgets
- Clean URLs: `/ai-pricing-calculator`
- 4 pages: pricing-calculator, status, error-decoder, tools

**Guide Pages (WordPress Posts)** - `content/guides/`
- Article content with guides and tutorials
- Uses working post template for proper HTML rendering
- 4 guides: openai-429-errors, openai-rate-limits, openai-vs-anthropic-pricing, openai-errors
- Category: "AI Guides"

### Required Redirects

After migrating guides from Pages to Posts, set up 301 redirects to preserve SEO:

**In WordPress Redirection plugin or .htaccess:**

```
# Old PAGE URLs → New POST URLs
/ai-is-openai-down → /ai-status (merged content)

# If post URLs differ from page URLs, add redirects like:
# /page-slug → /post-slug
```

The guides should retain their slugs (`ai-openai-429-errors`, etc.) so redirects may not be needed if WordPress preserves the URL structure.

## Widget Embedding

### How It Works

Widgets are embedded via a JavaScript loader that fetches content client-side. This bypasses WordPress caching entirely - no more manual cache clearing.

The loader script (`embed.js`) is cached by WordPress (since it never changes), but the actual widget content loads fresh every time from the API.

### Embedding a Widget (Simple Method)

**Just add the script tag directly in your WordPress page content.** No Bricks Builder needed!

#### Option 1: WordPress Block Editor (Gutenberg)

1. Edit your page in WordPress
2. Add an **HTML block** (search for "HTML" in block inserter)
3. Paste this code:

```html
<script
  src="https://ai-buzz-tools.onrender.com/embed.js"
  data-tool="error-decoder"
></script>
```

4. Publish/Update the page

#### Option 2: Classic Editor

1. Edit your page
2. Switch to **Text** mode (not Visual)
3. Paste the script tag where you want the widget to appear:

```html
<script
  src="https://ai-buzz-tools.onrender.com/embed.js"
  data-tool="error-decoder"
></script>
```

4. Update the page

**Available tools:**

- `pricing` - AI Pricing Calculator
- `status` - AI Status Page
- `error-decoder` - AI Error Decoder

### Alternative: Bricks Builder

If you're using Bricks Builder, add a **Code element** with the same script tag:

```html
<script
  src="https://ai-buzz-tools.onrender.com/embed.js"
  data-tool="error-decoder"
></script>
```

### Why JavaScript Instead of PHP?

WordPress aggressively caches page content to serve static HTML fast. The old PHP approach (`file_get_contents()`) fetched widget HTML at page-render time, which then got cached. When widgets were updated, WordPress served stale cached content until cache was manually cleared.

The JavaScript approach works _with_ WordPress caching:

- The static script tag gets cached (which is fine - it never changes)
- Widget content loads fresh every time via client-side fetch
- No cache clearing needed - updates appear immediately

### Example: Error Decoder Widget

```html
<script
  src="https://ai-buzz-tools.onrender.com/embed.js"
  data-tool="error-decoder"
></script>
```

The loader automatically:

1. Creates a container div
2. Shows a loading state (spinner)
3. Fetches widget HTML from the API
4. Injects the HTML into the container
5. Handles errors gracefully (retries once for Render cold starts)

### Multiple Widgets on Same Page

You can embed multiple widgets on the same page - each script tag works independently:

```html
<script
  src="https://ai-buzz-tools.onrender.com/embed.js"
  data-tool="pricing"
></script>
<script
  src="https://ai-buzz-tools.onrender.com/embed.js"
  data-tool="status"
></script>
<script
  src="https://ai-buzz-tools.onrender.com/embed.js"
  data-tool="error-decoder"
></script>
```

### Troubleshooting Widget Issues

**Widget shows "Loading tool..." but never loads:**

- Check browser console for JavaScript errors
- Verify API is accessible: `curl https://ai-buzz-tools.onrender.com/embed.js`
- Check that `data-tool` attribute matches a valid tool name

**Widget shows "Tool temporarily unavailable":**

- API may be experiencing a cold start (Render free tier)
- Widget will retry automatically after 3 seconds
- If it persists, check API status: `curl https://ai-buzz-tools.onrender.com/`

**Widget doesn't appear at all:**

- Check that script tag syntax is correct (no typos)
- Verify you're in Text mode (Classic Editor) or HTML block (Block Editor), not Visual mode
- Some security plugins block script tags - check if you have one installed
- Try viewing page source to confirm script tag is in the HTML output

## GA4 Analytics Setup

Widgets track user interactions via Google Analytics 4 (GA4). This section covers how to verify GA4 is working and configure custom dimensions for detailed reporting.

### Prerequisites

GA4 must be installed on your WordPress site. Common methods:

- **Bricks Builder** - Settings > Custom Code > Header Scripts
- **Site Kit by Google** - Plugin that manages GA4
- **MonsterInsights** - Popular GA4 plugin
- **Manual gtag.js** - Add snippet to theme header

### Events Tracked by Widgets

All widgets track these events automatically:

| Event Name      | When Fired                                            | Parameters            |
| --------------- | ----------------------------------------------------- | --------------------- |
| `tool_used`     | User completes main action (decode, calculate, check) | `tool_name`, `action` |
| `email_signup`  | User subscribes to alerts                             | `tool_name`           |
| `share_created` | User copies share URL                                 | `tool_name`           |

**tool_name values:** `error_decoder`, `pricing_calculator`, `status_page`, `tools-landing`

### Step 1: Verify GA4 is Loading

Open browser DevTools console on any tool page and run:

```javascript
aiBuzzDebug();
```

**Expected output if GA4 is working:**

```
=== AI-Buzz GA4 Debug ===
gtag available: true
dataLayer: 5 items
Sending test event: ai_buzz_debug_test
Test event sent! Check GA4 DebugView...
```

**If gtag shows `false`:** GA4 is not installed on the page. Check your WordPress GA4 setup.

### Step 2: Configure Custom Dimensions in GA4

To see `tool_name` in your GA4 reports, you need to register it as a custom dimension:

1. Go to **GA4 Admin** (gear icon)
2. Under Property, click **Custom definitions**
3. Click **Create custom dimension**
4. Create these two dimensions:

| Dimension name | Scope | Event parameter |
| -------------- | ----- | --------------- |
| Tool Name      | Event | `tool_name`     |
| Action         | Event | `action`        |

5. Click **Save**

**Note:** Custom dimensions take 24-48 hours to start populating with data.

### Step 3: Enable GA4 DebugView for Testing

DebugView shows events in real-time (instead of waiting 24-48 hours):

1. Install **GA Debugger** Chrome extension
2. Enable the extension on your site
3. Go to **GA4 Admin > Property > DebugView**
4. Use a tool on your site - events should appear in DebugView within seconds

### Step 4: Verify Events Are Firing

1. Open browser DevTools Console
2. Visit a tool page (e.g., `/ai-error-decoder`)
3. Use the tool (decode an error, calculate pricing, etc.)
4. Look for console messages like:

```
[AI-Buzz] Event tracked: tool_used {tool_name: "error_decoder", action: "decode"}
```

If you see this message, events are being sent to GA4.

### Troubleshooting GA4 Issues

**Events not appearing in GA4 reports:**

- Custom dimensions take 24-48 hours to populate
- Use DebugView for immediate testing
- Verify `aiBuzzDebug()` shows `gtag available: true`

**"gtag not available" in console:**

- GA4 is not installed or loading after widgets
- Check WordPress GA4 plugin settings
- Verify gtag.js is in page source (View Source > search for "gtag")
- Widgets retry for up to 2 seconds, so gtag loading slightly late is OK

**Events fire but tool_name is empty in reports:**

- Custom dimension `tool_name` not configured in GA4 Admin
- Follow Step 2 above to create the custom dimension
- Wait 24-48 hours for data to appear

**DebugView not showing events:**

- Make sure GA Debugger extension is enabled
- Refresh the page after enabling
- Check that you're looking at the correct GA4 property

### Viewing Analytics Data

**In GA4 (web interface):**

1. Go to **Reports > Engagement > Events**
2. Click on `tool_used`, `email_signup`, or `share_created`
3. Add secondary dimension "Tool Name" to see breakdown by tool

**Via API (automated):**

```bash
# Pull GA4 data to local JSON file
python scripts/analytics.py pull-ga4 --days 7

# Generate insights report
python scripts/analytics.py report

# View report
cat data/analytics/latest_report.md
```

### GA4 Setup Checklist

- [ ] GA4 is installed on WordPress (verify with `aiBuzzDebug()`)
- [ ] Custom dimension `tool_name` created in GA4 Admin
- [ ] Custom dimension `action` created in GA4 Admin
- [ ] Events appear in DebugView when using tools
- [ ] Console shows "[AI-Buzz] Event tracked:" messages

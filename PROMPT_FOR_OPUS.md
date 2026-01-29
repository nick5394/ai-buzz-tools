# Prompt for Opus 4.5: WordPress Integration Next Steps

You are helping plan the next steps for the AI-Buzz Tools WordPress integration that was just implemented.

## Context

I just completed implementing WordPress REST API integration for managing tool pages. Here's what was built:

### What Was Implemented

1. **WordPress Service** (`services/wordpress.py`)
   - REST API client for WordPress page operations
   - Methods: get_page_by_slug, get_page, create_page, update_page, list_pages, update_aioseo_meta
   - Uses environment variables for authentication (application password)

2. **CLI Tool** (`scripts/wp_pages.py`)
   - Commands: `list`, `pull`, `push`, `diff`
   - Converts between WordPress HTML and Markdown
   - Parses YAML frontmatter from content templates

3. **Content Templates** (`content/tools/`)
   - Base template (`_template.md`)
   - Content files for 3 existing tools (pricing-calculator, status-page, error-decoder)
   - Each includes frontmatter (title, slug, SEO meta) and body content

4. **Documentation**
   - Updated `env.example` with WordPress credentials
   - Added WordPress Integration section to Cursor rules

### Current Project State

- **3 tools deployed**: Pricing Calculator, Status Page, Error Decoder
- **Backend**: FastAPI on Render (free tier)
- **Frontend**: WordPress/Bricks Builder at ai-buzz.com
- **Widgets**: Self-contained HTML/CSS/JS served via API endpoints
- **Goal**: Portfolio of free tools for AI developers, validate demand, grow email list

### Constraints

- Solo developer, limited maintenance bandwidth
- $0-20/month budget
- Tools must run themselves (no manual maintenance)
- Follow "don't over-engineer" philosophy
- Ship fast, iterate based on real feedback

## Your Task

Create a detailed plan for the next steps to:

1. **Test and validate** the WordPress integration
2. **Sync existing WordPress pages** with the new content templates
3. **Identify any gaps or improvements** needed
4. **Plan the workflow** for adding future tools
5. **Consider edge cases** and error scenarios

## What I Need From You

Provide a structured plan that includes:

1. **Testing Checklist** - Step-by-step tests to verify everything works
2. **Migration Plan** - How to sync existing WordPress pages with new templates
3. **Workflow Documentation** - Clear process for adding new tools going forward
4. **Risk Assessment** - What could go wrong and how to handle it
5. **Improvement Opportunities** - What could be better (but only if it adds real value)
6. **Next Tool Template** - How to use this system when building the next tool

## Important Considerations

- The WordPress integration is optional - tools work without it
- Content templates are source of truth (git-tracked)
- CLI tool requires WordPress credentials (won't work without .env setup)
- Markdown ↔ HTML conversion is basic (may need refinement)
- AIOSEO integration may need testing (depends on WordPress setup)

## Questions to Address

- How should we handle the first sync? Pull existing pages or push new templates?
- What happens if WordPress content differs from templates?
- Should we add validation/checks before pushing?
- Do we need better error messages in the CLI?
- Should content templates include the widget embed code, or keep it separate?
- How do we handle SEO meta that's already set in WordPress?

## Output Format

Provide your plan as:

- Numbered steps with clear actions
- Checklists for validation
- Code snippets/examples where helpful
- Risk mitigation strategies
- Prioritization (must-do vs nice-to-have)

Focus on practical, actionable steps that help me validate the integration works and establish a smooth workflow for future tools.

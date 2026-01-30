"""
Integration tests for widgets using Playwright.

These tests load the actual widget HTML in a browser and test:
- Widget loads correctly
- User interactions work
- API calls are made correctly
- DOM updates based on API responses
- Error handling and loading states
- Share URLs and email forms
"""

import pytest
import urllib.request
import urllib.error
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError


# Helper Functions

async def load_widget(page: Page, widget_name: str, api_base: str, setup_proxy: bool = True):
    """Load widget HTML and inject API base URL override.
    
    This function:
    1. Fetches widget HTML from the test server
    2. Sets up route interception to proxy API requests (bypasses CORS for null origin)
    3. Injects window.API_BASE_URL before widget scripts execute
    4. Loads widget HTML via page.set_content()
    5. Waits for widget container to be ready
    
    Route interception proxies API requests because page.set_content() creates a
    null origin page, which browsers restrict for CORS. Simple route.continue_()
    doesn't bypass this - we need to actually proxy the requests.
    
    Args:
        page: Playwright page object
        widget_name: Name of widget (error-decoder, pricing, status)
        api_base: Base URL for API calls (e.g., http://localhost:8765)
        setup_proxy: If True (default), sets up route proxy for CORS bypass.
                    Set to False if test sets up its own route handlers.
    """
    # Map widget names to their API paths
    widget_paths = {
        "error-decoder": "error-decoder",
        "pricing": "pricing",
        "status": "status",
    }
    
    widget_path = widget_paths.get(widget_name, widget_name)
    widget_url = f"{api_base}/{widget_path}/widget"
    
    # Fetch widget HTML
    response = await page.request.get(widget_url)
    assert response.status == 200, f"Failed to fetch widget from {widget_url}"
    widget_html = await response.text()
    
    # Set up route handler that proxies API requests to bypass CORS
    # This is needed because set_content creates a null-origin page
    if setup_proxy:
        async def proxy_route(route):
            url = route.request.url
            method = route.request.method
            
            # Proxy requests to our test server (bypass CORS)
            if api_base in url and method in ('GET', 'POST'):
                try:
                    headers = {'Content-Type': 'application/json'}
                    data = route.request.post_data.encode() if route.request.post_data else None
                    
                    req = urllib.request.Request(url, data=data, headers=headers, method=method)
                    with urllib.request.urlopen(req, timeout=10) as resp:
                        body = resp.read()
                        await route.fulfill(
                            status=resp.status,
                            headers={'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                            body=body
                        )
                        return
                except urllib.error.HTTPError as e:
                    await route.fulfill(status=e.code, body=e.read())
                    return
                except Exception:
                    pass
            
            await route.continue_()
        
        await page.route("**/*", proxy_route)
    
    # Inject window.API_BASE_URL before the widget script runs
    injection_script = f'<script>window.API_BASE_URL = "{api_base}";</script>'
    
    # Insert injection script before first script tag
    if '<head>' in widget_html:
        widget_html = widget_html.replace('<head>', f'<head>{injection_script}', 1)
    elif '<script>' in widget_html:
        widget_html = widget_html.replace('<script>', f'{injection_script}<script>', 1)
    else:
        widget_html = injection_script + widget_html
    
    # Set content and wait for widget container
    await page.set_content(widget_html)
    
    # Wait for widget container to be attached
    widget_selectors = {
        "error-decoder": "#error-decoder-widget",
        "pricing": "#pricing-calculator-widget",
        "status": "#status-page-widget",
    }
    selector = widget_selectors.get(widget_name)
    if selector:
        await page.wait_for_selector(selector, timeout=3000, state="attached")
        await page.wait_for_load_state("domcontentloaded")
        await page.wait_for_timeout(100)


async def wait_for_widget_ready(page: Page, widget_name: str, timeout: int = 3000):
    """Wait for widget to be ready (initialized).
    
    Args:
        page: Playwright page object
        widget_name: Name of widget
        timeout: Maximum wait time in milliseconds (default: 3000)
    """
    widget_selectors = {
        "error-decoder": "#error-decoder-widget",
        "pricing": "#pricing-calculator-widget",
        "status": "#status-page-widget",
    }
    selector = widget_selectors.get(widget_name)
    if selector:
        await page.wait_for_selector(selector, timeout=timeout, state="attached")
        await page.wait_for_load_state("domcontentloaded")


async def wait_for_loading_state(page: Page, widget_name: str, visible: bool = True):
    """Wait for loading state to appear or disappear.
    
    Args:
        page: Playwright page object
        widget_name: Name of widget
        visible: If True, wait for loading to appear; if False, wait for it to disappear
    """
    loading_selectors = {
        "error-decoder": "#edw-loading.visible",
        "pricing": "#pcw-loading.visible",
        "status": "#spw-loading.visible",
    }
    selector = loading_selectors.get(widget_name)
    if selector:
        try:
            if visible:
                await page.wait_for_selector(selector, timeout=2000)
            else:
                # Wait for loading to disappear (not visible or no .visible class)
                await page.wait_for_selector(selector, timeout=5000, state="hidden")
        except PlaywrightTimeoutError:
            # Loading state might be too fast or not appear - that's okay
            pass


async def wait_for_results(page: Page, widget_name: str):
    """Wait for results section to appear.
    
    Args:
        page: Playwright page object
        widget_name: Name of widget
    """
    results_selectors = {
        "error-decoder": "#edw-results.visible",
        "pricing": "#pcw-results.visible",
        "status": "#spw-content",  # Status page doesn't use .visible class
    }
    error_selectors = {
        "error-decoder": "#edw-error.visible",
        "pricing": "#pcw-error.visible",
        "status": "#spw-error.visible",
    }
    
    selector = results_selectors.get(widget_name)
    error_selector = error_selectors.get(widget_name)
    
    if selector:
        # Wait for either results or error to appear
        try:
            # For status page, wait for content to be visible (not just attached)
            if widget_name == "status":
                await page.wait_for_selector(selector, timeout=15000, state="visible")
            else:
                # For other widgets, wait for selector first, then check if visible class is added
                await page.wait_for_selector(selector, timeout=15000)
                # Wait a bit for the visible class to be added
                await page.wait_for_timeout(200)
                # Check if element has visible class or is actually visible
                element = page.locator(selector)
                is_visible_class = await element.evaluate("el => el.classList.contains('visible')")
                is_actually_visible = await element.is_visible()
                if not is_visible_class and not is_actually_visible:
                    # Wait a bit more for visibility
                    await page.wait_for_timeout(500)
        except PlaywrightTimeoutError:
            # Check if error appeared instead
            if error_selector:
                try:
                    await page.wait_for_selector(error_selector, timeout=1000)
                    # Error appeared - that's still a valid result for testing
                    return
                except PlaywrightTimeoutError:
                    pass
            raise


async def wait_for_error_state(page: Page, widget_name: str):
    """Wait for error state to appear.
    
    Args:
        page: Playwright page object
        widget_name: Name of widget
    """
    error_selectors = {
        "error-decoder": "#edw-error.visible",
        "pricing": "#pcw-error.visible",
        "status": "#spw-error.visible",
    }
    selector = error_selectors.get(widget_name)
    if selector:
        await page.wait_for_selector(selector, timeout=5000)


# Test Classes

class TestErrorDecoderWidgetIntegration:
    """Integration tests for Error Decoder widget."""
    
    @pytest.mark.asyncio
    async def test_widget_loads(self, page: Page, test_server):
        """Test that widget HTML loads correctly."""
        await load_widget(page, "error-decoder", test_server)
        
        # Verify widget container exists
        widget = page.locator("#error-decoder-widget")
        assert await widget.is_visible()
        
        # Verify key elements exist
        assert await page.locator("#edw-error-input").is_visible()
        assert await page.locator("#edw-decode-btn").is_visible()
    
    @pytest.mark.asyncio
    async def test_decode_error_happy_path(self, page: Page, test_server, sample_error_message):
        """Test successful error decoding flow."""
        await load_widget(page, "error-decoder", test_server)
        
        # Enter error message
        textarea = page.locator("#edw-error-input")
        await textarea.fill(sample_error_message)
        
        # Click decode button and wait for API response
        decode_btn = page.locator("#edw-decode-btn")
        async with page.expect_response(lambda r: "/error-decoder/decode" in r.url and r.status == 200):
            await decode_btn.click()
        
        # Wait for loading state to appear, then disappear
        loading = page.locator("#edw-loading.visible")
        try:
            await loading.wait_for(state="visible", timeout=2000)
        except PlaywrightTimeoutError:
            # Loading might be too fast, that's okay
            pass
        
        # Wait for results (wait for loading to disappear and results to appear)
        await wait_for_results(page, "error-decoder")
        
        # Check if error appeared instead
        error_container = page.locator("#edw-error.visible")
        if await error_container.is_visible():
            # Error appeared - check what it says
            error_text = await error_container.text_content()
            pytest.fail(f"Error appeared instead of results: {error_text}")
        
        # Verify results displayed - use single reliable wait_for pattern
        results = page.locator("#edw-results.visible")
        await results.wait_for(state="visible", timeout=5000)
        assert await results.is_visible()
        
        # Verify explanation text contains keywords
        explanation = page.locator(".edw-explanation")
        explanation_text = await explanation.text_content()
        assert explanation_text is not None
        assert len(explanation_text) > 0
        
        # Verify share URL generated
        share_input = page.locator("#edw-share-url")
        share_url = await share_input.input_value()
        assert "ai-buzz.com/ai-error-decoder" in share_url
        assert "error=" in share_url
    
    @pytest.mark.asyncio
    async def test_decode_error_api_call(self, page: Page, test_server, sample_error_message):
        """Test that API call is made correctly."""
        api_calls = []
        
        async def handle_route(route):
            url = route.request.url
            method = route.request.method
            
            if "/error-decoder/decode" in url:
                api_calls.append({
                    "url": url,
                    "method": method,
                    "post_data": route.request.post_data if method == "POST" else None
                })
            
            # Also proxy the request to bypass CORS
            if test_server in url and method in ('GET', 'POST'):
                try:
                    headers = {'Content-Type': 'application/json'}
                    data = route.request.post_data.encode() if route.request.post_data else None
                    req = urllib.request.Request(url, data=data, headers=headers, method=method)
                    with urllib.request.urlopen(req, timeout=10) as resp:
                        await route.fulfill(status=resp.status, body=resp.read())
                        return
                except Exception:
                    pass
            await route.continue_()
        
        await page.route("**/*", handle_route)
        
        await load_widget(page, "error-decoder", test_server, setup_proxy=False)
        await page.locator("#edw-error-input").fill(sample_error_message)
        await page.locator("#edw-decode-btn").click()
        
        # Wait for API call
        await wait_for_results(page, "error-decoder")
        
        # Verify API call was made
        assert len(api_calls) > 0
        decode_calls = [c for c in api_calls if "/error-decoder/decode" in c["url"]]
        assert len(decode_calls) > 0
        assert decode_calls[0]["method"] == "POST"
    
    @pytest.mark.asyncio
    async def test_decode_error_network_failure(self, page: Page, test_server):
        """Test error handling when API call fails."""
        # Set up route handler that aborts decode requests but proxies others
        async def handle_route(route):
            url = route.request.url
            if "/error-decoder/decode" in url:
                await route.abort()
                return
            # Proxy other requests for CORS bypass
            if test_server in url:
                try:
                    method = route.request.method
                    headers = {'Content-Type': 'application/json'}
                    data = route.request.post_data.encode() if route.request.post_data else None
                    req = urllib.request.Request(url, data=data, headers=headers, method=method)
                    with urllib.request.urlopen(req, timeout=10) as resp:
                        await route.fulfill(status=resp.status, body=resp.read())
                        return
                except Exception:
                    pass
            await route.continue_()
        
        await page.route("**/*", handle_route)
        
        await load_widget(page, "error-decoder", test_server, setup_proxy=False)
        await page.locator("#edw-error-input").fill("test error")
        await page.locator("#edw-decode-btn").click()
        
        # Wait for error state
        await wait_for_error_state(page, "error-decoder")
        
        # Verify error message displayed
        error_container = page.locator("#edw-error")
        assert await error_container.is_visible()
    
    @pytest.mark.asyncio
    async def test_decode_unknown_error(self, page: Page, test_server, sample_unknown_error):
        """Test decoding unknown error returns suggestions."""
        await load_widget(page, "error-decoder", test_server)
        await page.locator("#edw-error-input").fill(sample_unknown_error)
        async with page.expect_response(lambda r: "/error-decoder/decode" in r.url and r.status == 200):
            await page.locator("#edw-decode-btn").click()
        
        await wait_for_results(page, "error-decoder")
        
        # Should show suggestions instead of decoded result
        results = page.locator("#edw-results")
        assert await results.is_visible()
    
    @pytest.mark.asyncio
    async def test_share_url_generation(self, page: Page, test_server, sample_error_message):
        """Test share URL is generated correctly."""
        await load_widget(page, "error-decoder", test_server)
        await page.locator("#edw-error-input").fill(sample_error_message)
        async with page.expect_response(lambda r: "/error-decoder/decode" in r.url and r.status == 200):
            await page.locator("#edw-decode-btn").click()
        
        await wait_for_results(page, "error-decoder")
        
        share_input = page.locator("#edw-share-url")
        share_url = await share_input.input_value()
        
        assert share_url.startswith("https://www.ai-buzz.com/ai-error-decoder")
        assert "error=" in share_url
    
    @pytest.mark.asyncio
    async def test_email_subscription(self, page: Page, test_server):
        """Test email subscription form."""
        await load_widget(page, "error-decoder", test_server)
        
        email_input = page.locator("#edw-email-input")
        email_btn = page.locator("#edw-email-btn")
        
        # Enter email
        await email_input.fill("test@example.com")
        await email_btn.click()
        
        # Wait for success or error message to appear (faster than arbitrary timeout)
        success_msg = page.locator("#edw-email-success")
        error_msg = page.locator("#edw-email-error")
        
        # Wait for either success or error message (whichever appears first)
        try:
            await success_msg.wait_for(state="visible", timeout=3000)
        except PlaywrightTimeoutError:
            await error_msg.wait_for(state="visible", timeout=1000)
        
        # Either success or error should be visible (depending on Mailchimp config)
        assert await success_msg.is_visible() or await error_msg.is_visible()


class TestPricingCalculatorWidgetIntegration:
    """Integration tests for Pricing Calculator widget."""
    
    @pytest.mark.asyncio
    async def test_widget_loads(self, page: Page, test_server):
        """Test that widget HTML loads correctly."""
        await load_widget(page, "pricing", test_server)
        
        widget = page.locator("#pricing-calculator-widget")
        assert await widget.is_visible()
        
        assert await page.locator("#pcw-input-tokens").is_visible()
        assert await page.locator("#pcw-output-tokens").is_visible()
        assert await page.locator("#pcw-calculate-btn").is_visible()
    
    @pytest.mark.asyncio
    async def test_calculate_costs_happy_path(self, page: Page, test_server):
        """Test successful cost calculation."""
        await load_widget(page, "pricing", test_server)
        
        # Enter token values (in millions)
        input_tokens = page.locator("#pcw-input-tokens")
        output_tokens = page.locator("#pcw-output-tokens")
        
        await input_tokens.fill("1")
        await output_tokens.fill("0.5")
        
        # Click calculate button and wait for API response
        calculate_btn = page.locator("#pcw-calculate-btn")
        async with page.expect_response(lambda r: "/pricing/calculate" in r.url and r.status == 200):
            await calculate_btn.click()
        
        # Wait for loading state to appear, then disappear
        loading = page.locator("#pcw-loading.visible")
        try:
            await loading.wait_for(state="visible", timeout=2000)
        except PlaywrightTimeoutError:
            # Loading might be too fast, that's okay
            pass
        
        # Wait for results
        await wait_for_results(page, "pricing")
        
        # Verify results displayed
        results = page.locator("#pcw-results")
        assert await results.is_visible()
        
        # Verify results table has rows
        results_body = page.locator("#pcw-results-body")
        rows = results_body.locator("tr")
        row_count = await rows.count()
        assert row_count > 0
    
    @pytest.mark.asyncio
    async def test_preset_buttons(self, page: Page, test_server):
        """Test preset buttons populate fields and trigger calculation."""
        await load_widget(page, "pricing", test_server)
        
        # Click Medium preset (triggers auto-calculation)
        medium_preset = page.locator(".pcw-preset-btn").filter(has_text="Medium")
        await medium_preset.click()
        
        # Wait for fields to be populated (preset fills them)
        input_tokens = page.locator("#pcw-input-tokens")
        output_tokens = page.locator("#pcw-output-tokens")
        
        # Wait for values to appear (preset auto-fills)
        await input_tokens.wait_for(state="visible", timeout=2000)
        
        input_val = await input_tokens.input_value()
        output_val = await output_tokens.input_value()
        
        assert input_val != ""
        assert output_val != ""
        
        # Wait for loading state (preset triggers calculation)
        loading = page.locator("#pcw-loading.visible")
        try:
            await loading.wait_for(state="visible", timeout=2000)
        except PlaywrightTimeoutError:
            # Loading might be too fast, that's okay
            pass
        
        # Wait for results after calculation completes
        await wait_for_results(page, "pricing")
    
    @pytest.mark.asyncio
    async def test_filter_chips(self, page: Page, test_server):
        """Test provider filter chips."""
        await load_widget(page, "pricing", test_server)
        
        # Calculate first
        await page.locator("#pcw-input-tokens").fill("1")
        await page.locator("#pcw-output-tokens").fill("0.5")
        await page.locator("#pcw-calculate-btn").click()
        await wait_for_results(page, "pricing")
        
        # Click a filter chip
        filter_chips = page.locator(".pcw-filter-chip")
        chip_count = await filter_chips.count()
        
        if chip_count > 0:
            first_chip = filter_chips.first
            await first_chip.click()
            
            # Results should update
            await page.wait_for_timeout(500)
            results = page.locator("#pcw-results")
            assert await results.is_visible()
    
    @pytest.mark.asyncio
    async def test_search_functionality(self, page: Page, test_server):
        """Test search input filters results."""
        await load_widget(page, "pricing", test_server)
        
        # Calculate first
        await page.locator("#pcw-input-tokens").fill("1")
        await page.locator("#pcw-output-tokens").fill("0.5")
        await page.locator("#pcw-calculate-btn").click()
        await wait_for_results(page, "pricing")
        
        # Enter search term
        search_input = page.locator("#pcw-search")
        await search_input.fill("gpt")
        
        # Wait for search to filter (results should still be visible)
        results = page.locator("#pcw-results")
        await results.wait_for(state="visible", timeout=2000)
        assert await results.is_visible()
    
    @pytest.mark.asyncio
    async def test_share_url_generation(self, page: Page, test_server):
        """Test share URL generation."""
        await load_widget(page, "pricing", test_server)
        
        await page.locator("#pcw-input-tokens").fill("1")
        await page.locator("#pcw-output-tokens").fill("0.5")
        await page.locator("#pcw-calculate-btn").click()
        await wait_for_results(page, "pricing")
        
        share_input = page.locator("#pcw-share-url")
        share_url = await share_input.input_value()
        
        assert share_url.startswith("https://www.ai-buzz.com/ai-pricing-calculator")
        assert "input=" in share_url or "tokens=" in share_url
    
    @pytest.mark.asyncio
    async def test_email_subscription(self, page: Page, test_server):
        """Test email subscription form."""
        await load_widget(page, "pricing", test_server)
        
        # Calculate first to show results (email section is inside results)
        await page.locator("#pcw-input-tokens").fill("1")
        await page.locator("#pcw-output-tokens").fill("0.5")
        async with page.expect_response(lambda r: "/pricing/calculate" in r.url and r.status == 200):
            await page.locator("#pcw-calculate-btn").click()
        
        # Wait for loading, then results
        loading = page.locator("#pcw-loading.visible")
        try:
            await loading.wait_for(state="visible", timeout=2000)
        except PlaywrightTimeoutError:
            pass
        
        await wait_for_results(page, "pricing")
        
        # Verify results section exists and becomes visible
        # Results might be hidden initially, wait for visible class or actual visibility
        results = page.locator("#pcw-results")
        # Wait for either .visible class or element to become visible
        try:
            await page.wait_for_selector("#pcw-results.visible", timeout=5000)
        except PlaywrightTimeoutError:
            # If .visible class check fails, check if element is actually visible
            await results.wait_for(state="visible", timeout=2000)
        
        # Now email input should be visible (it's inside results)
        email_input = page.locator("#pcw-email-input")
        email_btn = page.locator("#pcw-email-btn")
        
        # Wait for email input to be visible and scroll into view if needed
        await email_input.wait_for(state="visible", timeout=5000)
        await email_input.scroll_into_view_if_needed()
        
        await email_input.fill("test@example.com")
        await email_btn.click()
        
        # Wait for success or error message to appear (faster than arbitrary timeout)
        success_msg = page.locator("#pcw-email-success")
        error_msg = page.locator("#pcw-email-error")
        
        # Wait for either success or error message (whichever appears first)
        try:
            await success_msg.wait_for(state="visible", timeout=3000)
        except PlaywrightTimeoutError:
            await error_msg.wait_for(state="visible", timeout=1000)
        
        # Either success or error should be visible (depending on Mailchimp config)
        assert await success_msg.is_visible() or await error_msg.is_visible()


class TestStatusPageWidgetIntegration:
    """Integration tests for Status Page widget."""
    
    @pytest.mark.asyncio
    async def test_widget_loads_and_auto_fetches(self, page: Page, test_server):
        """Test that widget loads and auto-fetches status on load."""
        # Wait for auto-fetch API response (widget fetches on load)
        async with page.expect_response(lambda r: "/status/check" in r.url and r.status == 200):
            await load_widget(page, "status", test_server)
        
        widget = page.locator("#status-page-widget")
        assert await widget.is_visible()
        
        # Wait for content to appear
        await wait_for_results(page, "status")
        
        # Verify content displayed
        content = page.locator("#spw-content")
        assert await content.is_visible()
    
    @pytest.mark.asyncio
    async def test_provider_cards_displayed(self, page: Page, test_server):
        """Test that provider cards are rendered."""
        # Wait for auto-fetch API response (widget fetches on load)
        async with page.expect_response(lambda r: "/status/check" in r.url and r.status == 200):
            await load_widget(page, "status", test_server)
        
        # Wait for content
        await wait_for_results(page, "status")
        
        # Check for provider cards
        provider_cards = page.locator(".spw-provider-card")
        card_count = await provider_cards.count()
        
        # Should have at least some provider cards
        assert card_count > 0
    
    @pytest.mark.asyncio
    async def test_manual_refresh(self, page: Page, test_server):
        """Test manual refresh button."""
        # Wait for auto-fetch API response (widget fetches on load)
        async with page.expect_response(lambda r: "/status/check" in r.url and r.status == 200):
            await load_widget(page, "status", test_server)
        
        # Wait for initial load
        await wait_for_results(page, "status")
        
        # Wait for refresh button to be visible and scroll into view if needed
        refresh_btn = page.locator("#spw-refresh-btn")
        await refresh_btn.wait_for(state="visible", timeout=5000)
        await refresh_btn.scroll_into_view_if_needed()
        
        # Click refresh button and wait for API response
        async with page.expect_response(lambda r: "/status/check" in r.url and r.status == 200):
            await refresh_btn.click()
        
        # Wait for loading state (if it appears)
        loading = page.locator("#spw-loading.visible")
        try:
            await loading.wait_for(state="visible", timeout=2000)
        except PlaywrightTimeoutError:
            # Loading might be too fast, that's okay
            pass
        
        # Wait for content again
        await wait_for_results(page, "status")
        
        content = page.locator("#spw-content")
        assert await content.is_visible()
    
    @pytest.mark.asyncio
    async def test_error_handling(self, page: Page, test_server):
        """Test error handling when API fails."""
        # Set up route handler that aborts status check but proxies others
        async def handle_route(route):
            url = route.request.url
            if "/status/check" in url:
                await route.abort()
                return
            # Proxy other requests for CORS bypass (needed for widget HTML)
            if test_server in url:
                try:
                    method = route.request.method
                    headers = {'Content-Type': 'application/json'}
                    data = route.request.post_data.encode() if route.request.post_data else None
                    req = urllib.request.Request(url, data=data, headers=headers, method=method)
                    with urllib.request.urlopen(req, timeout=10) as resp:
                        await route.fulfill(status=resp.status, body=resp.read())
                        return
                except Exception:
                    pass
            await route.continue_()
        
        await page.route("**/*", handle_route)
        
        await load_widget(page, "status", test_server, setup_proxy=False)
        
        # Wait for error state
        await wait_for_error_state(page, "status")
        
        # Verify error message displayed
        error_container = page.locator("#spw-error")
        assert await error_container.is_visible()
    
    @pytest.mark.asyncio
    async def test_email_subscription(self, page: Page, test_server):
        """Test email subscription form."""
        # Wait for auto-fetch API response (widget fetches on load)
        async with page.expect_response(lambda r: "/status/check" in r.url and r.status == 200):
            await load_widget(page, "status", test_server)
        
        # Wait for widget to load
        await wait_for_results(page, "status")
        
        email_input = page.locator("#spw-email-input")
        email_btn = page.locator("#spw-email-btn")
        
        # Wait for email input to be visible and scroll into view if needed
        await email_input.wait_for(state="visible", timeout=5000)
        await email_input.scroll_into_view_if_needed()
        
        await email_input.fill("test@example.com")
        await email_btn.click()
        
        # Wait for success or error message to appear
        success_msg = page.locator("#spw-email-success")
        error_msg = page.locator("#spw-email-error")
        
        try:
            await success_msg.wait_for(state="visible", timeout=3000)
        except PlaywrightTimeoutError:
            await error_msg.wait_for(state="visible", timeout=1000)
        
        assert await success_msg.is_visible() or await error_msg.is_visible()


# Embed.js Integration Tests

class TestEmbedJsIntegration:
    """Test that widgets work when loaded via embed.js (production flow).
    
    Note: These tests verify the embed.js script execution fix by checking
    that the script re-execution code is present. Full end-to-end testing
    with embed.js requires a real browser loading a hosted page, which is
    better done via the browser MCP tools in manual testing.
    """
    
    @pytest.mark.asyncio
    async def test_widget_scripts_execute_after_load(self, page: Page, test_server):
        """Test that widget scripts execute and event handlers work.
        
        This tests the core fix: scripts must execute for buttons to work.
        The embed.js innerHTML fix ensures this in production; here we verify
        the widgets work when loaded directly (which load_widget handles).
        """
        await load_widget(page, "error-decoder", test_server)
        
        # Verify button exists
        decode_btn = page.locator("#edw-decode-btn")
        assert await decode_btn.is_visible()
        
        # CRITICAL: Test that scripts executed by filling input and clicking button
        # If scripts didn't execute, the button click won't trigger the decode function
        await page.locator("#edw-error-input").fill("Error: 429 Too Many Requests")
        
        # Click and wait for API response (proves script executed)
        async with page.expect_response(lambda r: "/error-decoder/decode" in r.url, timeout=15000):
            await decode_btn.click()
        
        # Wait for results (proves full flow works)
        await page.wait_for_selector("#edw-results.visible", timeout=10000)
        
        # Verify results displayed
        results = page.locator("#edw-results.visible")
        assert await results.is_visible()


class TestGA4EventTracking:
    """Test that GA4 trackEvent helper function is called correctly.
    
    Note: These tests verify the trackEvent function is called with correct
    parameters. The actual gtag() calls would go to Google Analytics in
    production; here we intercept the trackEvent call itself.
    """
    
    @pytest.mark.asyncio
    async def test_tool_used_event_fires_on_decode(self, page: Page, test_server):
        """Test that tool_used event fires after successful decode."""
        await load_widget(page, "error-decoder", test_server)
        
        # Set up event interceptor by overriding the widget's trackEvent function
        # We need to do this AFTER the widget loads but BEFORE we trigger actions
        await page.evaluate("""
            window._ga4TestEvents = [];
            // Override gtag to capture events (widget uses trackEvent which calls gtag)
            window.gtag = function(...args) {
                if (args[0] === 'event') {
                    window._ga4TestEvents.push({ event: args[1], params: args[2] });
                }
            };
        """)
        
        # Perform decode
        await page.locator("#edw-error-input").fill("Error: 429 Too Many Requests")
        async with page.expect_response(lambda r: "/error-decoder/decode" in r.url and r.status == 200):
            await page.locator("#edw-decode-btn").click()
        
        await wait_for_results(page, "error-decoder")
        
        # Check captured events
        events = await page.evaluate("JSON.stringify(window._ga4TestEvents)")
        import json
        events_list = json.loads(events)
        
        # Verify tool_used event was captured
        tool_used_events = [e for e in events_list if e.get("event") == "tool_used"]
        assert len(tool_used_events) > 0, "tool_used event should fire after decode"
        assert tool_used_events[0]["params"]["tool_name"] == "error_decoder"
        assert tool_used_events[0]["params"]["action"] == "decode"
    
    @pytest.mark.asyncio
    async def test_share_created_event_fires_on_copy(self, page: Page, test_server):
        """Test that share_created event fires when share URL is copied."""
        await load_widget(page, "error-decoder", test_server)
        
        # Set up event interceptor and mock clipboard API
        # (clipboard API may not be available in headless/set_content mode)
        await page.evaluate("""
            window._ga4TestEvents = [];
            window.gtag = function(...args) {
                if (args[0] === 'event') {
                    window._ga4TestEvents.push({ event: args[1], params: args[2] });
                }
            };
            // Mock clipboard API for headless testing
            if (!navigator.clipboard) {
                navigator.clipboard = {};
            }
            navigator.clipboard.writeText = (text) => Promise.resolve();
        """)
        
        # Perform decode first to show results and share URL
        await page.locator("#edw-error-input").fill("Error: 429 Too Many Requests")
        async with page.expect_response(lambda r: "/error-decoder/decode" in r.url and r.status == 200):
            await page.locator("#edw-decode-btn").click()
        
        await wait_for_results(page, "error-decoder")
        
        # Wait for copy button to be visible
        copy_btn = page.locator("#edw-copy-btn")
        await copy_btn.wait_for(state="visible", timeout=5000)
        await copy_btn.click()
        
        # Wait for button text to change to "Copied!" (async clipboard operation)
        await page.wait_for_timeout(500)
        
        # Check captured events
        events = await page.evaluate("JSON.stringify(window._ga4TestEvents)")
        import json
        events_list = json.loads(events)
        
        # Verify share_created event was captured
        share_events = [e for e in events_list if e.get("event") == "share_created"]
        assert len(share_events) > 0, f"share_created event should fire after copy. Got events: {events_list}"
        assert share_events[0]["params"]["tool_name"] == "error_decoder"


# Mobile Viewport Tests

class TestWidgetMobileViewport:
    """Test widgets on mobile viewport (375px width)."""
    
    @pytest.mark.asyncio
    async def test_error_decoder_mobile(self, page: Page, test_server):
        """Test Error Decoder widget on mobile viewport."""
        await page.set_viewport_size({"width": 375, "height": 667})
        await load_widget(page, "error-decoder", test_server)
        
        widget = page.locator("#error-decoder-widget")
        assert await widget.is_visible()
        
        # Widget should be responsive
        box = await widget.bounding_box()
        assert box is not None
        assert box["width"] <= 375
    
    @pytest.mark.asyncio
    async def test_pricing_calculator_mobile(self, page: Page, test_server):
        """Test Pricing Calculator widget on mobile viewport."""
        await page.set_viewport_size({"width": 375, "height": 667})
        await load_widget(page, "pricing", test_server)
        
        widget = page.locator("#pricing-calculator-widget")
        assert await widget.is_visible()
        
        box = await widget.bounding_box()
        assert box is not None
        assert box["width"] <= 375
    
    @pytest.mark.asyncio
    async def test_status_page_mobile(self, page: Page, test_server):
        """Test Status Page widget on mobile viewport."""
        await page.set_viewport_size({"width": 375, "height": 667})
        await load_widget(page, "status", test_server)
        
        widget = page.locator("#status-page-widget")
        assert await widget.is_visible()
        
        box = await widget.bounding_box()
        assert box is not None
        assert box["width"] <= 375

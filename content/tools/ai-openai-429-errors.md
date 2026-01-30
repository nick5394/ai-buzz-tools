---
title: How to Handle OpenAI 429 Errors - Fix Rate Limit Issues
slug: ai-openai-429-errors
status: publish
seo_title: How to Handle OpenAI 429 Errors - Fix Rate Limit Issues
seo_description: Fix OpenAI 429 "Too Many Requests" errors. Code examples for Python, Node.js with exponential backoff, retry logic, and rate limiting.
widget_endpoint: /error-decoder/widget
---

# How to Handle OpenAI 429 Errors - Fix Rate Limit Issues

Getting "Error 429: Too Many Requests" from OpenAI? This guide shows you exactly how to fix it with working code examples.

<script src="https://ai-buzz-tools.onrender.com/embed.js" data-tool="error-decoder"></script>

## What Does 429 Mean?

A 429 error means you've exceeded OpenAI's rate limits. The API is rejecting your requests because you're making too many calls too quickly.

**The error looks like:**

```
openai.RateLimitError: Error code: 429 - Rate limit reached for gpt-4o
```

or

```
{"error": {"message": "Rate limit reached for gpt-4o in organization org-xxx on tokens per min (TPM): Limit 30000, Used 28500, Requested 5000.", "type": "rate_limit_error"}}
```

## Quick Fixes

### 1. Wait and Retry

The simplest fix: wait a few seconds and try again. OpenAI rate limits reset every minute.

### 2. Reduce Request Frequency

If you're making parallel requests, reduce concurrency or add delays between calls.

### 3. Use a Smaller Model

GPT-4o-mini has much higher rate limits than GPT-4o. If your task doesn't require the flagship model, switch.

### 4. Check Your Tier

New accounts (Tier 1) have the lowest limits. See your [current limits](/ai-openai-rate-limits) and how to upgrade.

## Code Solutions

### Python: Exponential Backoff with tenacity

The most robust solution using the `tenacity` library:

```python
import openai
from tenacity import retry, wait_exponential, retry_if_exception_type

@retry(
    wait=wait_exponential(multiplier=1, min=1, max=60),
    retry=retry_if_exception_type(openai.RateLimitError)
)
def call_openai(prompt):
    return openai.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )

# Usage
response = call_openai("Hello, world!")
```

**How it works:**

- First retry waits 1 second
- Second retry waits 2 seconds
- Third retry waits 4 seconds
- Continues doubling up to 60 seconds max

### Python: Manual Retry Logic

If you don't want extra dependencies:

```python
import time
import random
import openai

def call_openai_with_retry(prompt, max_retries=5):
    for attempt in range(max_retries):
        try:
            return openai.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}]
            )
        except openai.RateLimitError as e:
            if attempt == max_retries - 1:
                raise  # Give up after max retries

            # Exponential backoff with jitter
            wait_time = (2 ** attempt) + random.uniform(0, 1)
            print(f"Rate limited. Retrying in {wait_time:.1f}s...")
            time.sleep(wait_time)

# Usage
response = call_openai_with_retry("Hello, world!")
```

### Node.js: Exponential Backoff

```javascript
const OpenAI = require("openai");
const openai = new OpenAI();

async function callOpenAIWithRetry(prompt, maxRetries = 5) {
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      return await openai.chat.completions.create({
        model: "gpt-4o",
        messages: [{ role: "user", content: prompt }],
      });
    } catch (error) {
      if (error.status !== 429 || attempt === maxRetries - 1) {
        throw error;
      }

      // Exponential backoff with jitter
      const waitTime = Math.pow(2, attempt) + Math.random();
      console.log(`Rate limited. Retrying in ${waitTime.toFixed(1)}s...`);
      await new Promise((resolve) => setTimeout(resolve, waitTime * 1000));
    }
  }
}

// Usage
const response = await callOpenAIWithRetry("Hello, world!");
```

### Using the Retry-After Header

OpenAI sometimes tells you exactly how long to wait:

```python
import openai
import time

def call_with_retry_header(prompt):
    while True:
        try:
            return openai.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}]
            )
        except openai.RateLimitError as e:
            # Check for Retry-After header
            retry_after = getattr(e, 'headers', {}).get('Retry-After')
            if retry_after:
                wait_time = int(retry_after)
            else:
                wait_time = 5  # Default fallback

            print(f"Rate limited. Waiting {wait_time}s...")
            time.sleep(wait_time)
```

## Rate Limiting on Your End

Instead of hitting limits and retrying, prevent 429s by limiting your own request rate.

### Python: Simple Rate Limiter

```python
import time
from threading import Lock

class RateLimiter:
    def __init__(self, requests_per_minute):
        self.min_interval = 60.0 / requests_per_minute
        self.last_request = 0
        self.lock = Lock()

    def wait(self):
        with self.lock:
            elapsed = time.time() - self.last_request
            if elapsed < self.min_interval:
                time.sleep(self.min_interval - elapsed)
            self.last_request = time.time()

# Usage: Limit to 500 RPM (Tier 1 GPT-4o limit)
limiter = RateLimiter(requests_per_minute=500)

def call_openai_limited(prompt):
    limiter.wait()  # Wait if needed
    return openai.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )
```

### Async Rate Limiter (Python)

For async code:

```python
import asyncio
import time

class AsyncRateLimiter:
    def __init__(self, requests_per_minute):
        self.min_interval = 60.0 / requests_per_minute
        self.last_request = 0
        self.lock = asyncio.Lock()

    async def wait(self):
        async with self.lock:
            elapsed = time.time() - self.last_request
            if elapsed < self.min_interval:
                await asyncio.sleep(self.min_interval - elapsed)
            self.last_request = time.time()

# Usage
limiter = AsyncRateLimiter(requests_per_minute=500)

async def call_openai_async(prompt):
    await limiter.wait()
    return await openai.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )
```

## When to Use the Batch API

If your requests aren't time-sensitive, use OpenAI's Batch API:

- **50% cheaper** than regular API calls
- **Much higher rate limits**
- Results delivered within 24 hours

Best for: bulk processing, data analysis, non-real-time tasks.

## Common Mistakes

### 1. Not Adding Jitter

Without random jitter, all your retries happen at the same time, causing "thundering herd" issues.

**Bad:**

```python
time.sleep(2 ** attempt)
```

**Good:**

```python
time.sleep((2 ** attempt) + random.uniform(0, 1))
```

### 2. Infinite Retries

Always set a max retry limit to avoid infinite loops.

### 3. Retrying Non-Retryable Errors

Only retry 429 errors. Other errors (401, 400) won't be fixed by retrying.

### 4. Ignoring TPM Limits

Even if you're under RPM limits, large prompts can exhaust TPM limits quickly.

## Preventing 429 Errors

**Best practices to avoid rate limits:**

1. **Implement caching** - Don't call the API for the same prompt twice
2. **Use smaller models** - GPT-4o-mini has 10x higher limits
3. **Batch requests** - Use the Batch API for non-urgent tasks
4. **Optimize prompts** - Shorter prompts = more requests per minute
5. **Upgrade your tier** - Spend more to automatically get higher limits

## FAQ

### Why do I keep getting 429 errors even with retry logic?

Your base request rate is too high. Add rate limiting on your end to stay under limits, not just retry when you hit them.

### Can I catch 429 errors before they happen?

Yes, track your token usage and implement your own rate limiting to stay under OpenAI's limits proactively.

### Does the Retry-After header always exist?

No. It's included sometimes but not guaranteed. Always have a fallback wait time.

### Will upgrading my account help?

Yes. Higher tiers have significantly higher rate limits. See [OpenAI Rate Limits by Tier](/ai-openai-rate-limits).

### Is this tool free?

Yes, completely free. Paste any API error above to decode it instantly.

## Related Tools

- [OpenAI Rate Limits Explained](/ai-openai-rate-limits) - Full breakdown of limits by tier
- [AI Error Decoder](/ai-error-decoder) - Decode any API error message
- [AI Error Decoder](/ai-error-decoder) - Decode any API error message
- [AI Status Page](/ai-status) - Check if OpenAI is down

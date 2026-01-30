"""
Embed Router
Serves the universal JavaScript loader for embedding widgets in WordPress.
"""

import logging
from fastapi import APIRouter
from fastapi.responses import Response

logger = logging.getLogger(__name__)

router = APIRouter()

# API base URL - can be overridden via environment variable
API_BASE = "https://ai-buzz-tools.onrender.com"

# Map tool slugs to widget endpoints
TOOL_ENDPOINTS = {
    "pricing": "/pricing/widget",
    "status": "/status/widget",
    "error-decoder": "/error-decoder/widget",
    "tools-landing": "/tools/widget",
}


@router.get("/embed.js")
async def get_embed_script():
    """
    Serve the universal JavaScript loader script.
    
    This script:
    1. Finds the script tag that loaded it
    2. Reads the data-tool attribute
    3. Creates a container with loading state
    4. Fetches widget HTML from the API
    5. Injects the HTML into the container
    6. Handles errors gracefully with retry logic
    """
    # Get API base from environment or use default
    import os
    api_base = os.getenv("API_BASE_URL", API_BASE)
    
    embed_js = f"""(function() {{
  'use strict';
  
  // Find the script tag that loaded this file
  const scripts = document.getElementsByTagName('script');
  let currentScript = null;
  for (let i = scripts.length - 1; i >= 0; i--) {{
    if (scripts[i].src && scripts[i].src.includes('embed.js')) {{
      currentScript = scripts[i];
      break;
    }}
  }}
  
  if (!currentScript) {{
    console.error('AI-Buzz embed: Could not find script tag');
    return;
  }}
  
  // Get tool name from data-tool attribute
  const toolName = currentScript.getAttribute('data-tool');
  if (!toolName) {{
    console.error('AI-Buzz embed: data-tool attribute is required');
    return;
  }}
  
  // Map tool names to endpoints
  const toolEndpoints = {{
    'pricing': '/pricing/widget',
    'status': '/status/widget',
    'error-decoder': '/error-decoder/widget',
    'tools-landing': '/tools/widget'
  }};
  
  const widgetEndpoint = toolEndpoints[toolName];
  if (!widgetEndpoint) {{
    console.error('AI-Buzz embed: Unknown tool "' + toolName + '"');
    return;
  }}
  
  // Create container div
  const container = document.createElement('div');
  container.id = 'ai-buzz-widget-container-' + toolName;
  container.style.cssText = 'max-width: 800px; margin: 20px auto; padding: 0;';
  
  // Insert container after the script tag
  if (currentScript.parentNode) {{
    currentScript.parentNode.insertBefore(container, currentScript.nextSibling);
  }} else {{
    document.body.appendChild(container);
  }}
  
  // Loading state HTML (matches widget aesthetic)
  function getLoadingHTML(message) {{
    return `
    <div style="
      max-width: 800px;
      margin: 20px auto;
      padding: 40px 20px;
      text-align: center;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
      color: #6b7280;
      background: #ffffff;
      border: 1px solid #e5e7eb;
      border-radius: 12px;
      box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    ">
      <div style="
        width: 40px;
        height: 40px;
        border: 3px solid #e5e7eb;
        border-top-color: #2563eb;
        border-radius: 50%;
        animation: spin 0.8s linear infinite;
        margin: 0 auto 12px;
      "></div>
      <p style="margin: 0; font-size: 14px;">${{message}}</p>
      <style>
        @keyframes spin {{
          to {{ transform: rotate(360deg); }}
        }}
      </style>
    </div>
  `;
  }}
  
  // Error state HTML
  const errorHTML = `
    <div style="
      max-width: 800px;
      margin: 20px auto;
      padding: 40px 20px;
      text-align: center;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
      color: #ef4444;
      background: #fef2f2;
      border: 1px solid #fecaca;
      border-radius: 12px;
    ">
      <p style="margin: 0 0 12px 0; font-size: 14px; font-weight: 600;">Tool temporarily unavailable</p>
      <p style="margin: 0; font-size: 13px; color: #6b7280;">Please refresh the page to try again.</p>
    </div>
  `;
  
  // Show loading state
  container.innerHTML = getLoadingHTML('Loading tool...');
  
  // Fetch widget HTML
  const widgetUrl = '{api_base}' + widgetEndpoint;
  let retryCount = 0;
  const maxRetries = 3;
  const retryDelays = [5000, 10000, 20000]; // Exponential backoff: 5s, 10s, 20s
  
  function fetchWidget() {{
    fetch(widgetUrl, {{
      method: 'GET',
      headers: {{
        'Accept': 'text/html'
      }},
      cache: 'no-cache'
    }})
    .then(function(response) {{
      if (!response.ok) {{
        throw new Error('HTTP ' + response.status);
      }}
      return response.text();
    }})
    .then(function(html) {{
      // Inject widget HTML and execute scripts
      container.innerHTML = html;
      
      // Scripts added via innerHTML don't execute, so we need to re-add them
      const scripts = container.querySelectorAll('script');
      scripts.forEach(function(oldScript) {{
        const newScript = document.createElement('script');
        // Copy attributes
        Array.from(oldScript.attributes).forEach(function(attr) {{
          newScript.setAttribute(attr.name, attr.value);
        }});
        // Copy content
        newScript.textContent = oldScript.textContent;
        // Replace old script with new one (this executes it)
        oldScript.parentNode.replaceChild(newScript, oldScript);
      }});
    }})
    .catch(function(error) {{
      console.error('AI-Buzz embed: Failed to load widget (attempt ' + (retryCount + 1) + ')', error);
      
      // Retry with exponential backoff (handles Render cold starts up to 35s)
      if (retryCount < maxRetries) {{
        const delay = retryDelays[retryCount];
        retryCount++;
        container.innerHTML = getLoadingHTML('Warming up... (attempt ' + retryCount + '/' + maxRetries + ')');
        setTimeout(fetchWidget, delay);
      }} else {{
        // Show error state after all retries exhausted
        container.innerHTML = errorHTML;
      }}
    }});
  }}
  
  // Start fetching
  fetchWidget();
}})();
"""
    
    return Response(
        content=embed_js,
        media_type="application/javascript",
        headers={
            "Cache-Control": "public, max-age=3600",  # Cache the loader script itself
        }
    )

#!/usr/bin/env python3
"""
Sync AI model pricing from LiteLLM's pricing database.

This script fetches the latest pricing data from LiteLLM's GitHub repository
and transforms it into the format used by our pricing calculator.

Usage:
    python scripts/sync_pricing_from_litellm.py           # Preview changes (dry run)
    python scripts/sync_pricing_from_litellm.py --apply   # Apply changes to pricing_data.json
    python scripts/sync_pricing_from_litellm.py --verbose # Show detailed output
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import requests

# LiteLLM pricing data source
LITELLM_PRICING_URL = "https://raw.githubusercontent.com/BerriAI/litellm/main/model_prices_and_context_window.json"

# Path to our pricing data file (relative to project root)
PRICING_DATA_PATH = Path(__file__).parent.parent / "data" / "pricing_data.json"

# Providers we care about and their metadata
PROVIDER_CONFIG = {
    "openai": {
        "name": "OpenAI",
        "website": "https://openai.com",
        "source": "https://openai.com/api/pricing/",
    },
    "anthropic": {
        "name": "Anthropic",
        "website": "https://www.anthropic.com",
        "source": "https://www.anthropic.com/pricing",
    },
    "google": {
        "name": "Google",
        "website": "https://ai.google.dev",
        "source": "https://ai.google.dev/pricing",
        "litellm_prefixes": ["gemini/", "vertex_ai/"],
    },
    "mistral": {
        "name": "Mistral",
        "website": "https://mistral.ai",
        "source": "https://mistral.ai/technology/",
        "litellm_prefixes": ["mistral/"],
    },
    "deepseek": {
        "name": "DeepSeek",
        "website": "https://www.deepseek.com",
        "source": "https://platform.deepseek.com/api-docs/pricing",
        "litellm_prefixes": ["deepseek/"],
    },
    "xai": {
        "name": "xAI",
        "website": "https://x.ai",
        "source": "https://docs.x.ai/docs/consumption-and-rate-limits",
        "litellm_prefixes": ["xai/"],
    },
    "meta": {
        "name": "Meta (Llama)",
        "website": "https://llama.meta.com",
        "source": "https://llama.meta.com/",
        "litellm_prefixes": ["together_ai/meta-llama/", "groq/llama"],
    },
    "cohere": {
        "name": "Cohere",
        "website": "https://cohere.com",
        "source": "https://cohere.com/pricing",
        "litellm_prefixes": ["cohere/", "cohere_chat/"],
    },
    "groq": {
        "name": "Groq",
        "website": "https://groq.com",
        "source": "https://groq.com/pricing/",
        "litellm_prefixes": ["groq/"],
    },
    "together": {
        "name": "Together AI",
        "website": "https://together.ai",
        "source": "https://www.together.ai/pricing",
        "litellm_prefixes": ["together_ai/"],
    },
}

# Models we want to include with their display names and notes
# Key format: "litellm_model_key" -> {"id": "our_id", "name": "Display Name", "notes": "..."}
MODEL_MAPPING = {
    # OpenAI models
    "gpt-4o": {"id": "gpt-4o", "name": "GPT-4o", "notes": "Flagship multimodal model"},
    "gpt-4o-mini": {"id": "gpt-4o-mini", "name": "GPT-4o Mini", "notes": "Fast and affordable"},
    "gpt-4o-mini-2024-07-18": {"id": "gpt-4o-mini", "name": "GPT-4o Mini", "notes": "Fast and affordable"},
    "o1": {"id": "o1", "name": "o1", "notes": "Advanced reasoning model"},
    "o1-preview": {"id": "o1", "name": "o1", "notes": "Advanced reasoning model"},
    "o3-mini": {"id": "o3-mini", "name": "o3-mini", "notes": "Efficient reasoning model"},
    
    # Anthropic models
    "claude-3-5-sonnet-20241022": {"id": "claude-sonnet-45", "name": "Claude Sonnet 4.5", "notes": "Best balance of speed and intelligence"},
    "claude-3-5-sonnet-latest": {"id": "claude-sonnet-45", "name": "Claude Sonnet 4.5", "notes": "Best balance of speed and intelligence"},
    "claude-3-5-haiku-20241022": {"id": "claude-haiku-45", "name": "Claude Haiku 4.5", "notes": "Fast and cost-effective"},
    "claude-3-5-haiku-latest": {"id": "claude-haiku-45", "name": "Claude Haiku 4.5", "notes": "Fast and cost-effective"},
    "claude-3-opus-20240229": {"id": "claude-opus-45", "name": "Claude Opus 4.5", "notes": "Most capable model"},
    "claude-3-opus-latest": {"id": "claude-opus-45", "name": "Claude Opus 4.5", "notes": "Most capable model"},
    
    # Google models (with gemini/ prefix in LiteLLM)
    "gemini/gemini-2.0-flash": {"id": "gemini-2-flash", "name": "Gemini 2.0 Flash", "notes": "Fast multimodal model, 1M context"},
    "gemini/gemini-2.0-flash-exp": {"id": "gemini-2-flash", "name": "Gemini 2.0 Flash", "notes": "Fast multimodal model, 1M context"},
    "gemini/gemini-2.0-flash-lite": {"id": "gemini-2-flash-lite", "name": "Gemini 2.0 Flash-Lite", "notes": "Most cost-efficient Google model"},
    "gemini/gemini-1.5-pro": {"id": "gemini-15-pro", "name": "Gemini 1.5 Pro", "notes": "Premium reasoning, 1M context"},
    "gemini/gemini-1.5-pro-latest": {"id": "gemini-15-pro", "name": "Gemini 1.5 Pro", "notes": "Premium reasoning, 1M context"},
    
    # Mistral models
    "mistral/mistral-large-latest": {"id": "mistral-large-3", "name": "Mistral Large 3", "notes": "Flagship model"},
    "mistral/mistral-large-2411": {"id": "mistral-large-3", "name": "Mistral Large 3", "notes": "Flagship model"},
    "mistral/mistral-small-latest": {"id": "mistral-small-31", "name": "Mistral Small 3.1", "notes": "Ultra cost-effective"},
    "mistral/open-mistral-nemo": {"id": "mistral-nemo", "name": "Mistral Nemo", "notes": "Budget option, cheapest Mistral"},
    "mistral/open-mistral-nemo-2407": {"id": "mistral-nemo", "name": "Mistral Nemo", "notes": "Budget option, cheapest Mistral"},
    
    # DeepSeek models
    "deepseek/deepseek-chat": {"id": "deepseek-chat", "name": "DeepSeek V3", "notes": "High performance, extremely low cost"},
    "deepseek/deepseek-reasoner": {"id": "deepseek-reasoner", "name": "DeepSeek R1", "notes": "Reasoning model"},
    
    # xAI models
    "xai/grok-2": {"id": "grok-4", "name": "Grok 4", "notes": "Flagship model from xAI"},
    "xai/grok-2-latest": {"id": "grok-4", "name": "Grok 4", "notes": "Flagship model from xAI"},
    "xai/grok-beta": {"id": "grok-41-fast", "name": "Grok 4.1 Fast", "notes": "2M context window, budget friendly"},
    
    # Meta/Llama models
    "together_ai/meta-llama/Llama-3.3-70B-Instruct-Turbo": {"id": "llama-3-3-70b", "name": "Llama 3.3 70B", "notes": "Open-source, highly capable"},
    "together_ai/meta-llama/Llama-3.2-90B-Vision-Instruct-Turbo": {"id": "llama-3-2-90b-vision", "name": "Llama 3.2 90B Vision", "notes": "Multimodal vision capabilities"},
    "together_ai/meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo": {"id": "llama-3-1-405b", "name": "Llama 3.1 405B", "notes": "Largest open model, frontier-class"},
    
    # Cohere models
    "cohere/command-r-plus": {"id": "command-r-plus", "name": "Command R+", "notes": "Enterprise RAG optimized"},
    "cohere_chat/command-r-plus": {"id": "command-r-plus", "name": "Command R+", "notes": "Enterprise RAG optimized"},
    "cohere/command-r": {"id": "command-r", "name": "Command R", "notes": "Balanced performance and cost"},
    "cohere_chat/command-r": {"id": "command-r", "name": "Command R", "notes": "Balanced performance and cost"},
    "cohere/command-r7b-12-2024": {"id": "command-r7b", "name": "Command R7B", "notes": "Ultra-fast, low latency"},
    
    # Groq models
    "groq/llama-3.3-70b-versatile": {"id": "llama-3-3-70b-groq", "name": "Llama 3.3 70B (Groq)", "notes": "Ultra-fast inference, ~500 tok/s"},
    "groq/llama-3.1-8b-instant": {"id": "llama-3-1-8b-groq", "name": "Llama 3.1 8B (Groq)", "notes": "Fastest inference, ~1000 tok/s"},
    "groq/mixtral-8x7b-32768": {"id": "mixtral-8x7b-groq", "name": "Mixtral 8x7B (Groq)", "notes": "MoE architecture, very fast"},
    
    # Together AI models
    "together_ai/meta-llama/Llama-3.3-70B-Instruct-Turbo-Free": {"id": "llama-3-3-70b-together", "name": "Llama 3.3 70B (Together)", "notes": "Serverless, auto-scaling"},
    "together_ai/Qwen/Qwen2.5-72B-Instruct-Turbo": {"id": "qwen-2-5-72b", "name": "Qwen 2.5 72B", "notes": "Strong multilingual support"},
    "together_ai/deepseek-ai/DeepSeek-V3": {"id": "deepseek-v3-together", "name": "DeepSeek V3 (Together)", "notes": "Alternative hosting for DeepSeek"},
}


def fetch_litellm_pricing() -> dict:
    """Fetch pricing data from LiteLLM's GitHub repository."""
    print(f"Fetching pricing data from LiteLLM...")
    response = requests.get(LITELLM_PRICING_URL, timeout=30)
    response.raise_for_status()
    data = response.json()
    print(f"  Found {len(data)} models in LiteLLM database")
    return data


def extract_provider_from_key(model_key: str) -> Optional[str]:
    """Determine the provider from a LiteLLM model key."""
    # Check explicit prefixes first
    for provider, config in PROVIDER_CONFIG.items():
        prefixes = config.get("litellm_prefixes", [f"{provider}/"])
        for prefix in prefixes:
            if model_key.startswith(prefix):
                return provider
    
    # OpenAI models often don't have a prefix
    if model_key.startswith(("gpt-", "o1", "o3", "davinci", "text-")):
        return "openai"
    
    # Anthropic models
    if model_key.startswith("claude"):
        return "anthropic"
    
    return None


def transform_litellm_data(litellm_data: dict, verbose: bool = False) -> dict:
    """Transform LiteLLM pricing data to our format."""
    # Start with empty providers
    providers = {}
    
    # Track which models we've found
    found_models = set()
    
    for model_key, model_data in litellm_data.items():
        # Skip if not in our mapping
        if model_key not in MODEL_MAPPING:
            continue
        
        mapping = MODEL_MAPPING[model_key]
        model_id = mapping["id"]
        
        # Skip if we've already processed this model ID (avoid duplicates from aliases)
        if model_id in found_models:
            continue
        
        # Determine provider
        provider = extract_provider_from_key(model_key)
        if not provider:
            if verbose:
                print(f"  Skipping {model_key}: unknown provider")
            continue
        
        # Get pricing - LiteLLM uses per-token, we need per-1M
        input_cost = model_data.get("input_cost_per_token", 0)
        output_cost = model_data.get("output_cost_per_token", 0)
        
        # Convert to per-1M tokens
        input_per_1m = round(input_cost * 1_000_000, 4)
        output_per_1m = round(output_cost * 1_000_000, 4)
        
        # Get context window
        context_window = model_data.get("max_input_tokens") or model_data.get("max_tokens", 128000)
        
        # Initialize provider if needed
        if provider not in providers:
            config = PROVIDER_CONFIG[provider]
            providers[provider] = {
                "name": config["name"],
                "website": config["website"],
                "models": {}
            }
        
        # Add the model
        providers[provider]["models"][model_id] = {
            "name": mapping["name"],
            "input_per_1m": input_per_1m,
            "output_per_1m": output_per_1m,
            "context_window": context_window,
            "notes": mapping["notes"]
        }
        
        found_models.add(model_id)
        
        if verbose:
            print(f"  {provider}/{model_id}: ${input_per_1m}/M input, ${output_per_1m}/M output")
    
    return providers


def load_current_pricing() -> dict:
    """Load the current pricing_data.json file."""
    if PRICING_DATA_PATH.exists():
        with open(PRICING_DATA_PATH, "r") as f:
            return json.load(f)
    return {}


def merge_pricing_data(current: dict, new_providers: dict) -> dict:
    """Merge new pricing data with current, preserving manual entries."""
    # Required fields for each model (no tier/tags - we keep it simple)
    REQUIRED_FIELDS = ["name", "input_per_1m", "output_per_1m", "context_window", "notes"]
    
    # Build the result starting with metadata
    result = {
        "_metadata": {
            "last_updated": datetime.now().strftime("%Y-%m-%d"),
            "update_frequency": "weekly",
            "notes": "Prices in USD per 1 million tokens. Auto-synced from LiteLLM with manual verification.",
            "sources": {
                provider: config["source"]
                for provider, config in PROVIDER_CONFIG.items()
            }
        },
        "providers": {}
    }
    
    # Get current providers
    current_providers = current.get("providers", {})
    
    # Process each provider
    all_providers = set(current_providers.keys()) | set(new_providers.keys())
    
    for provider in sorted(all_providers):
        if provider in new_providers:
            # Use new data but preserve any manual-only models
            result["providers"][provider] = new_providers[provider].copy()
            
            # Check for models in current that aren't in new (manual additions)
            if provider in current_providers:
                current_models = current_providers[provider].get("models", {})
                new_models = new_providers[provider].get("models", {})
                for model_id, model_data in current_models.items():
                    if model_id not in new_models:
                        # Preserve manual model, but only required fields
                        clean_model = {k: model_data[k] for k in REQUIRED_FIELDS if k in model_data}
                        result["providers"][provider]["models"][model_id] = clean_model
        elif provider in current_providers:
            # Provider not in LiteLLM, preserve current data (clean fields)
            provider_data = current_providers[provider].copy()
            clean_models = {}
            for model_id, model_data in provider_data.get("models", {}).items():
                clean_models[model_id] = {k: model_data[k] for k in REQUIRED_FIELDS if k in model_data}
            provider_data["models"] = clean_models
            result["providers"][provider] = provider_data
    
    return result


def compare_pricing(current: dict, new: dict) -> list:
    """Compare current and new pricing, return list of changes."""
    changes = []
    
    current_providers = current.get("providers", {})
    new_providers = new.get("providers", {})
    
    for provider in sorted(set(current_providers.keys()) | set(new_providers.keys())):
        if provider not in current_providers:
            changes.append(f"+ Added provider: {provider}")
            continue
        if provider not in new_providers:
            changes.append(f"- Removed provider: {provider}")
            continue
        
        current_models = current_providers[provider].get("models", {})
        new_models = new_providers[provider].get("models", {})
        
        for model_id in sorted(set(current_models.keys()) | set(new_models.keys())):
            if model_id not in current_models:
                new_model = new_models[model_id]
                changes.append(f"+ {provider}/{model_id}: NEW (${new_model['input_per_1m']}/{new_model['output_per_1m']})")
                continue
            if model_id not in new_models:
                changes.append(f"- {provider}/{model_id}: REMOVED")
                continue
            
            # Compare prices
            old = current_models[model_id]
            new = new_models[model_id]
            
            if old["input_per_1m"] != new["input_per_1m"] or old["output_per_1m"] != new["output_per_1m"]:
                changes.append(
                    f"~ {provider}/{model_id}: "
                    f"${old['input_per_1m']}/{old['output_per_1m']} -> "
                    f"${new['input_per_1m']}/{new['output_per_1m']}"
                )
    
    return changes


def save_pricing_data(data: dict):
    """Save pricing data to file."""
    with open(PRICING_DATA_PATH, "w") as f:
        json.dump(data, f, indent=2)
    print(f"Saved pricing data to {PRICING_DATA_PATH}")


def main():
    parser = argparse.ArgumentParser(description="Sync AI pricing from LiteLLM")
    parser.add_argument("--apply", action="store_true", help="Apply changes to pricing_data.json")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed output")
    args = parser.parse_args()
    
    try:
        # Fetch LiteLLM data
        litellm_data = fetch_litellm_pricing()
        
        # Transform to our format
        new_providers = transform_litellm_data(litellm_data, verbose=args.verbose)
        
        if not new_providers:
            print("No matching models found in LiteLLM data!")
            sys.exit(1)
        
        # Load current pricing
        current = load_current_pricing()
        
        # Merge data
        merged = merge_pricing_data(current, new_providers)
        
        # Compare and show changes
        changes = compare_pricing(current, merged)
        
        if not changes:
            print("\nNo pricing changes detected.")
            return
        
        print(f"\nFound {len(changes)} change(s):")
        for change in changes:
            print(f"  {change}")
        
        if args.apply:
            save_pricing_data(merged)
            print("\nPricing data updated successfully!")
        else:
            print("\nDry run - no changes applied. Use --apply to save changes.")
    
    except requests.RequestException as e:
        print(f"Error fetching LiteLLM data: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

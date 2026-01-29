"""
Pricing Calculator API Router
Handles all pricing-related endpoints.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field, EmailStr

from api.shared import load_json_data, subscribe_email, load_widget

logger = logging.getLogger(__name__)

router = APIRouter()

# ============================================================================
# Pydantic Models
# ============================================================================

class PricingModelInfo(BaseModel):
    """Single AI model pricing information."""
    name: str = Field(..., description="Display name of the model")
    input_per_1m: float = Field(..., description="Cost per 1M input tokens in USD")
    output_per_1m: float = Field(..., description="Cost per 1M output tokens in USD")
    context_window: int = Field(..., description="Maximum context window size")
    notes: str = Field(..., description="Brief description of the model")


class ProviderInfo(BaseModel):
    """AI provider with their models."""
    name: str = Field(..., description="Provider display name")
    website: str = Field(..., description="Provider website URL")
    models: Dict[str, PricingModelInfo] = Field(..., description="Available models")


class PricingDataResponse(BaseModel):
    """Response model for pricing models endpoint."""
    success: bool = Field(..., description="Whether request was successful")
    last_updated: str = Field(..., description="Date pricing was last updated")
    providers: Dict[str, ProviderInfo] = Field(..., description="All providers and models")


class CalculateRequest(BaseModel):
    """Request model for cost calculation."""
    input_tokens_monthly: int = Field(..., ge=0, description="Expected monthly input tokens")
    output_tokens_monthly: int = Field(..., ge=0, description="Expected monthly output tokens")
    selected_model: Optional[str] = Field(None, description="Selected model in format 'provider/model' for highlighting")


class CalculationResult(BaseModel):
    """Cost calculation result for a single model."""
    provider: str = Field(..., description="Provider ID")
    provider_name: str = Field(..., description="Provider display name")
    model: str = Field(..., description="Model ID")
    model_name: str = Field(..., description="Model display name")
    monthly_cost: float = Field(..., description="Total monthly cost in USD")
    input_cost: float = Field(..., description="Monthly input token cost")
    output_cost: float = Field(..., description="Monthly output token cost")
    is_selected: bool = Field(False, description="Whether this is the user-selected model")
    context_window: int = Field(..., description="Model context window")
    notes: str = Field(..., description="Model notes")
    vs_gpt4o_savings_percent: Optional[float] = Field(None, description="Percentage savings vs GPT-4o")


class CheapestModel(BaseModel):
    """Information about the cheapest model."""
    provider: str = Field(..., description="Provider ID")
    model: str = Field(..., description="Model ID")
    model_name: str = Field(..., description="Model display name")
    monthly_cost: float = Field(..., description="Monthly cost in USD")


class SavingsInfo(BaseModel):
    """Savings information when comparing selected model to cheapest."""
    has_savings: bool = Field(..., description="Whether switching would save money")
    selected_model: Optional[str] = Field(None, description="Selected model key")
    selected_model_name: Optional[str] = Field(None, description="Selected model display name")
    selected_cost: float = Field(0.0, description="Monthly cost of selected model")
    cheapest_model: str = Field(..., description="Cheapest model key")
    cheapest_model_name: str = Field(..., description="Cheapest model display name")
    cheapest_cost: float = Field(..., description="Monthly cost of cheapest model")
    monthly_savings: float = Field(0.0, description="Monthly savings if switching to cheapest")
    annual_savings: float = Field(0.0, description="Annual savings if switching to cheapest")
    savings_percentage: float = Field(0.0, description="Percentage savings")


class PricingMetadata(BaseModel):
    """Metadata about pricing data."""
    last_updated: str = Field(..., description="Date when pricing was last updated")
    model_count: int = Field(..., description="Total number of models")
    provider_count: int = Field(..., description="Total number of providers")
    update_frequency: str = Field("weekly", description="How often data is updated")


class CalculateResponse(BaseModel):
    """Response model for cost calculation."""
    success: bool = Field(..., description="Whether calculation was successful")
    calculated_at: str = Field(..., description="ISO timestamp of calculation")
    usage: Dict[str, int] = Field(..., description="Token usage summary")
    results: List[CalculationResult] = Field(..., description="Sorted results by cost")
    cheapest: CheapestModel = Field(..., description="Cheapest option")
    most_expensive: CheapestModel = Field(..., description="Most expensive option for comparison")
    savings: SavingsInfo = Field(..., description="Potential savings information")
    pricing_last_updated: str = Field(..., description="When pricing data was last updated")
    metadata: PricingMetadata = Field(..., description="Pricing data metadata")


class CompareRequest(BaseModel):
    """Request model for model comparison."""
    models: List[str] = Field(..., min_length=2, max_length=5, description="Models to compare in 'provider/model' format")
    input_tokens_monthly: int = Field(..., ge=0, description="Expected monthly input tokens")
    output_tokens_monthly: int = Field(..., ge=0, description="Expected monthly output tokens")


class ComparedModel(BaseModel):
    """Comparison data for a single model."""
    provider: str
    provider_name: str
    model: str
    model_name: str
    monthly_cost: float
    input_cost: float
    output_cost: float
    context_window: int
    notes: str
    cost_rank: int
    cost_vs_cheapest: float
    cost_vs_cheapest_amount: float


class CompareResponse(BaseModel):
    """Response model for model comparison."""
    success: bool
    models: List[ComparedModel]
    cheapest: str
    most_expensive: str
    max_savings: float
    usage: Dict[str, int]


class SubscribeRequest(BaseModel):
    """Request model for email subscription."""
    email: EmailStr = Field(..., description="Email address for price alerts")


class SubscribeResponse(BaseModel):
    """Response model for email subscription."""
    success: bool = Field(..., description="Whether subscription was successful")
    message: str = Field(..., description="Status message")
    mailchimp_synced: bool = Field(False, description="Whether synced to Mailchimp")


# ============================================================================
# Helper Functions
# ============================================================================

def calculate_model_cost(
    input_tokens: int,
    output_tokens: int,
    input_per_1m: float,
    output_per_1m: float
) -> Dict[str, float]:
    """Calculate cost for a specific model based on token usage."""
    input_cost = (input_tokens / 1_000_000) * input_per_1m
    output_cost = (output_tokens / 1_000_000) * output_per_1m
    
    return {
        "input_cost": round(input_cost, 4),
        "output_cost": round(output_cost, 4),
        "total": round(input_cost + output_cost, 4)
    }


# ============================================================================
# API Endpoints
# ============================================================================

@router.get("/models", response_model=PricingDataResponse)
async def get_pricing_models():
    """
    Get all AI providers and models with pricing information.
    Used to populate dropdowns and display pricing tables.
    """
    try:
        pricing_data = load_json_data("pricing_data.json")
        
        providers_response = {}
        for provider_id, provider_data in pricing_data.get("providers", {}).items():
            models_response = {}
            for model_id, model_data in provider_data.get("models", {}).items():
                models_response[model_id] = PricingModelInfo(
                    name=model_data["name"],
                    input_per_1m=model_data["input_per_1m"],
                    output_per_1m=model_data["output_per_1m"],
                    context_window=model_data["context_window"],
                    notes=model_data["notes"]
                )
            
            providers_response[provider_id] = ProviderInfo(
                name=provider_data["name"],
                website=provider_data.get("website", ""),
                models=models_response
            )
        
        return PricingDataResponse(
            success=True,
            last_updated=pricing_data.get("_metadata", {}).get("last_updated", "unknown"),
            providers=providers_response
        )
    
    except FileNotFoundError:
        logger.error("pricing_data.json not found")
        raise HTTPException(status_code=500, detail="Pricing data not available.")
    except Exception as e:
        logger.error(f"Error loading pricing data: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error loading pricing data: {str(e)}")


@router.post("/calculate", response_model=CalculateResponse)
async def calculate_pricing(request: CalculateRequest):
    """
    Calculate monthly costs for all AI models based on expected token usage.
    Returns results sorted by cost (cheapest first).
    """
    try:
        pricing_data = load_json_data("pricing_data.json")
        
        input_tokens = request.input_tokens_monthly
        output_tokens = request.output_tokens_monthly
        selected_model = request.selected_model
        
        results = []
        gpt4o_cost = None
        
        # First pass: calculate costs for all models and find GPT-4o cost
        for provider_id, provider_data in pricing_data.get("providers", {}).items():
            for model_id, model_data in provider_data.get("models", {}).items():
                costs = calculate_model_cost(
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    input_per_1m=model_data["input_per_1m"],
                    output_per_1m=model_data["output_per_1m"]
                )
                
                model_key = f"{provider_id}/{model_id}"
                is_selected = selected_model == model_key if selected_model else False
                
                # Track GPT-4o cost for comparison
                if provider_id == "openai" and model_id == "gpt-4o":
                    gpt4o_cost = costs["total"]
                
                results.append(CalculationResult(
                    provider=provider_id,
                    provider_name=provider_data["name"],
                    model=model_id,
                    model_name=model_data["name"],
                    monthly_cost=costs["total"],
                    input_cost=costs["input_cost"],
                    output_cost=costs["output_cost"],
                    is_selected=is_selected,
                    context_window=model_data["context_window"],
                    notes=model_data["notes"],
                    vs_gpt4o_savings_percent=None
                ))
        
        # Second pass: calculate savings vs GPT-4o for each model
        if gpt4o_cost is not None and gpt4o_cost > 0:
            for result in results:
                if result.provider == "openai" and result.model == "gpt-4o":
                    result.vs_gpt4o_savings_percent = None
                else:
                    savings = ((gpt4o_cost - result.monthly_cost) / gpt4o_cost) * 100
                    result.vs_gpt4o_savings_percent = round(savings, 1)
        
        # Sort by monthly cost (ascending)
        results.sort(key=lambda x: x.monthly_cost)
        
        # Find cheapest and most expensive
        cheapest = results[0] if results else None
        most_expensive = results[-1] if results else None
        
        cheapest_info = CheapestModel(
            provider=cheapest.provider if cheapest else "unknown",
            model=cheapest.model if cheapest else "unknown",
            model_name=cheapest.model_name if cheapest else "Unknown",
            monthly_cost=cheapest.monthly_cost if cheapest else 0.0
        )
        
        most_expensive_info = CheapestModel(
            provider=most_expensive.provider if most_expensive else "unknown",
            model=most_expensive.model if most_expensive else "unknown",
            model_name=most_expensive.model_name if most_expensive else "Unknown",
            monthly_cost=most_expensive.monthly_cost if most_expensive else 0.0
        )
        
        # Calculate savings information
        selected_result = None
        if selected_model:
            selected_result = next((r for r in results if f"{r.provider}/{r.model}" == selected_model), None)
        
        comparison_result = selected_result if selected_result else most_expensive
        
        if comparison_result and cheapest:
            monthly_savings = comparison_result.monthly_cost - cheapest.monthly_cost
            annual_savings = monthly_savings * 12
            savings_percentage = (monthly_savings / comparison_result.monthly_cost * 100) if comparison_result.monthly_cost > 0 else 0
            
            savings_info = SavingsInfo(
                has_savings=monthly_savings > 0.01,
                selected_model=f"{selected_result.provider}/{selected_result.model}" if selected_result else None,
                selected_model_name=selected_result.model_name if selected_result else None,
                selected_cost=selected_result.monthly_cost if selected_result else 0.0,
                cheapest_model=f"{cheapest.provider}/{cheapest.model}",
                cheapest_model_name=cheapest.model_name,
                cheapest_cost=cheapest.monthly_cost,
                monthly_savings=round(monthly_savings, 2),
                annual_savings=round(annual_savings, 2),
                savings_percentage=round(savings_percentage, 1)
            )
        else:
            savings_info = SavingsInfo(
                has_savings=False,
                cheapest_model="unknown",
                cheapest_model_name="Unknown",
                cheapest_cost=0.0
            )
        
        # Calculate metadata
        provider_count = len(pricing_data.get("providers", {}))
        model_count = sum(
            len(p.get("models", {})) 
            for p in pricing_data.get("providers", {}).values()
        )
        
        metadata = PricingMetadata(
            last_updated=pricing_data.get("_metadata", {}).get("last_updated", "unknown"),
            model_count=model_count,
            provider_count=provider_count,
            update_frequency=pricing_data.get("_metadata", {}).get("update_frequency", "weekly")
        )
        
        return CalculateResponse(
            success=True,
            calculated_at=datetime.utcnow().isoformat() + "Z",
            usage={"input_tokens": input_tokens, "output_tokens": output_tokens},
            results=results,
            cheapest=cheapest_info,
            most_expensive=most_expensive_info,
            savings=savings_info,
            pricing_last_updated=pricing_data.get("_metadata", {}).get("last_updated", "unknown"),
            metadata=metadata
        )
    
    except FileNotFoundError:
        logger.error("pricing_data.json not found")
        raise HTTPException(status_code=500, detail="Pricing data not available.")
    except Exception as e:
        logger.error(f"Error calculating pricing: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error calculating pricing: {str(e)}")


@router.get("/calculate")
async def calculate_pricing_get(
    input_tokens: int = 1000000,
    output_tokens: int = 500000,
    selected_model: Optional[str] = None
):
    """
    GET version of calculate endpoint for shareable URLs.
    Example: /pricing/calculate?input_tokens=1000000&output_tokens=500000
    """
    request = CalculateRequest(
        input_tokens_monthly=input_tokens,
        output_tokens_monthly=output_tokens,
        selected_model=selected_model
    )
    return await calculate_pricing(request)


@router.post("/compare", response_model=CompareResponse)
async def compare_models(request: CompareRequest):
    """
    Compare 2-5 specific models side-by-side.
    Returns detailed comparison with cost differences.
    """
    try:
        pricing_data = load_json_data("pricing_data.json")
        
        input_tokens = request.input_tokens_monthly
        output_tokens = request.output_tokens_monthly
        model_keys = request.models
        
        compared_models = []
        
        for model_key in model_keys:
            if "/" not in model_key:
                raise HTTPException(status_code=400, detail=f"Invalid model format: {model_key}. Use 'provider/model'")
            
            provider_id, model_id = model_key.split("/", 1)
            
            if provider_id not in pricing_data.get("providers", {}):
                raise HTTPException(status_code=400, detail=f"Unknown provider: {provider_id}")
            
            provider_data = pricing_data["providers"][provider_id]
            if model_id not in provider_data.get("models", {}):
                raise HTTPException(status_code=400, detail=f"Unknown model: {model_key}")
            
            model_data = provider_data["models"][model_id]
            costs = calculate_model_cost(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                input_per_1m=model_data["input_per_1m"],
                output_per_1m=model_data["output_per_1m"]
            )
            
            compared_models.append({
                "provider": provider_id,
                "provider_name": provider_data["name"],
                "model": model_id,
                "model_name": model_data["name"],
                "monthly_cost": costs["total"],
                "input_cost": costs["input_cost"],
                "output_cost": costs["output_cost"],
                "context_window": model_data["context_window"],
                "notes": model_data["notes"],
            })
        
        # Sort by cost to determine ranks
        compared_models.sort(key=lambda x: x["monthly_cost"])
        
        cheapest_cost = compared_models[0]["monthly_cost"]
        cheapest_key = f"{compared_models[0]['provider']}/{compared_models[0]['model']}"
        most_expensive_key = f"{compared_models[-1]['provider']}/{compared_models[-1]['model']}"
        max_savings = compared_models[-1]["monthly_cost"] - cheapest_cost
        
        # Add comparison metrics
        result_models = []
        for rank, model in enumerate(compared_models, 1):
            cost_vs_cheapest_amount = model["monthly_cost"] - cheapest_cost
            cost_vs_cheapest = (cost_vs_cheapest_amount / cheapest_cost * 100) if cheapest_cost > 0 else 0
            
            result_models.append(ComparedModel(
                **model,
                cost_rank=rank,
                cost_vs_cheapest=round(cost_vs_cheapest, 1),
                cost_vs_cheapest_amount=round(cost_vs_cheapest_amount, 2)
            ))
        
        return CompareResponse(
            success=True,
            models=result_models,
            cheapest=cheapest_key,
            most_expensive=most_expensive_key,
            max_savings=round(max_savings, 2),
            usage={"input_tokens": input_tokens, "output_tokens": output_tokens}
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error comparing models: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error comparing models: {str(e)}")


@router.post("/alerts/subscribe", response_model=SubscribeResponse)
async def subscribe_alerts(request: SubscribeRequest):
    """
    Subscribe to AI API price change alerts.
    Integrates with Mailchimp if configured.
    """
    result = subscribe_email(
        email=request.email,
        tool_name="pricing-calculator",
        interest_tags=["interest:price-alerts"],
        success_message="Successfully subscribed to price alerts!"
    )
    
    return SubscribeResponse(**result)


@router.get("/widget", response_class=HTMLResponse)
async def get_pricing_widget():
    """
    Serve the Pricing Calculator widget HTML.
    For embedding in WordPress/Bricks.
    """
    try:
        widget_html = load_widget("pricing_calculator_widget.html")
        return HTMLResponse(content=widget_html, status_code=200)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Widget file not found")

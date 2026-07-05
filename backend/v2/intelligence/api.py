from fastapi import APIRouter
from typing import List
from v2.intelligence.models import StrategyProposal, RevenueForecast

router = APIRouter(prefix="/api/intelligence", tags=["Intelligence"])

@router.get("/forecast", response_model=RevenueForecast)
async def get_revenue_forecast(tenant_id: str):
    """
    Returns the hybrid Revenue Forecast for the Executive Dashboard.
    Combines deterministic CRM metrics with statistical models and AI narrative.
    """
    # Stubbed response
    return RevenueForecast(
        tenant_id=tenant_id,
        ai_narrative="Based on the recent 15% drop-off in pricing objections, we forecast a slight dip in Q3 pipeline. Implementing the pending Strategy Proposals is recommended."
    )

@router.get("/proposals", response_model=List[StrategyProposal])
async def get_strategy_proposals(tenant_id: str):
    """
    Returns a list of AI-generated Strategy Proposals awaiting human review.
    """
    # In reality, this fetches from the DB
    return []

@router.post("/proposals/{proposal_id}/approve")
async def approve_strategy_proposal(proposal_id: str):
    """
    Human-in-the-loop approval. 
    Applies the AI's proposed changes directly to the versioned Business Brain.
    """
    return {"status": "approved", "message": "Business Brain updated successfully."}

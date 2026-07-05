from typing import Optional, Dict
from pydantic import BaseModel

from .base_agent import BaseAgent
from ..prompts.registry import prompt_registry
from ..schemas import PromptSchema, Capability

from typing import List, Optional
from pydantic import BaseModel, Field

class ExecutiveSummary(BaseModel):
    overall_growth_score: int
    growth_potential: str
    revenue_opportunity: str
    ai_confidence: str
    time_to_results: str
    wow_statement: str

class IntelligencePoint(BaseModel):
    value: str
    source_type: str = Field(description="Must be 'Observed', 'Estimated', or 'Inferred'")

class BusinessIntelligence(BaseModel):
    industry: IntelligencePoint
    business_model: IntelligencePoint
    products: IntelligencePoint
    services: IntelligencePoint
    pricing_model: IntelligencePoint
    target_market: IntelligencePoint
    company_stage: IntelligencePoint
    estimated_team_size: IntelligencePoint
    estimated_acv: IntelligencePoint
    estimated_sales_cycle: IntelligencePoint
    buying_committee: IntelligencePoint
    revenue_model: IntelligencePoint
    primary_differentiator: IntelligencePoint

class HealthScore(BaseModel):
    score: int
    reason: str
    impact: str
    recommendation: str

class WebsiteHealth(BaseModel):
    messaging: HealthScore
    trust: HealthScore
    conversion: HealthScore
    clarity: HealthScore
    ux: HealthScore
    authority: HealthScore
    ai_readiness: HealthScore
    sales_readiness: HealthScore

class AIUnderstanding(BaseModel):
    problem_solved: str
    target_buyers: str
    why_buy: str
    why_buy_now: str
    value_received: str
    emotional_outcome: str

class RankedICP(BaseModel):
    name: str
    match_percentage: str
    company_size: str
    revenue: str
    decision_makers: str
    pain: str
    buying_trigger: str
    urgency: str
    expected_deal_size: str
    likelihood: str

class BuyerPersona(BaseModel):
    title: str
    problems: str
    goals: str
    kpis: str
    budget_authority: str
    objections: str
    buying_motivation: str
    preferred_outreach: str

class PainPointDiscovery(BaseModel):
    business_pain: str
    operational_pain: str
    technical_pain: str
    financial_pain: str
    competitive_pain: str
    growth_pain: str

class Competitor(BaseModel):
    name: str
    strength: str
    weakness: str
    positioning: str
    pricing: str
    market_share_estimate: str
    opportunity: str
    confidence_score: str

class CompetitorIntelligence(BaseModel):
    known_competitors: List[Competitor]
    likely_competitors: List[Competitor]
    emerging_competitors: List[Competitor]
    alternative_solutions: List[Competitor]

class PositioningAnalysis(BaseModel):
    current_position: str
    market_position: str
    brand_perception: str
    differentiation: str
    unique_value: str
    missing_messaging: str
    recommended_positioning_statement: str

class TrustAudit(BaseModel):
    testimonials: str
    case_studies: str
    social_proof: str
    logos: str
    security: str
    compliance: str
    pricing_transparency: str
    founder_visibility: str
    team_visibility: str
    contact_information: str
    reviews: str
    guarantees: str
    trust_score: int

class ConversionAudit(BaseModel):
    homepage: str
    cta: str
    forms: str
    navigation: str
    pricing: str
    lead_capture: str
    offer: str
    website_copy: str
    speed: str
    friction: str
    current_estimated_conversion_rate: str
    potential_estimated_conversion_rate: str

class RevenueOpportunity(BaseModel):
    opportunity_name: str
    expected_revenue: str
    difficulty: str
    roi: str
    confidence: str
    time_required: str

class GrowthRoadmap(BaseModel):
    week_1: str
    week_2: str
    week_3: str
    week_4: str
    month_2: str
    month_3: str

class AISalesStrategy(BaseModel):
    ideal_outreach_cold_email: str
    ideal_outreach_linkedin: str
    ideal_outreach_calls: str
    ideal_outreach_referral: str
    ideal_outreach_content: str
    ideal_outreach_events: str
    recommended_campaign: str
    expected_meetings: str
    expected_replies: str
    expected_pipeline: str

class BusinessBrain(BaseModel):
    products: List[str]
    industries: List[str]
    icp: List[str]
    competitors: List[str]
    buying_signals: List[str]
    objections: List[str]
    keywords: List[str]
    differentiators: List[str]
    goals: List[str]

class WebsiteAnalysisResult(BaseModel):
    executive_summary: ExecutiveSummary
    business_intelligence: BusinessIntelligence
    website_health: WebsiteHealth
    ai_understanding: AIUnderstanding
    icp_discovery: List[RankedICP]
    buyer_personas: List[BuyerPersona]
    pain_points: PainPointDiscovery
    competitors: CompetitorIntelligence
    positioning: PositioningAnalysis
    trust_audit: TrustAudit
    conversion_audit: ConversionAudit
    revenue_opportunities: List[RevenueOpportunity]
    growth_roadmap: GrowthRoadmap
    sales_strategy: AISalesStrategy
    biggest_growth_risks: List[str]
    business_brain: BusinessBrain
    final_recommendation_vp_sales: str

class ResearchAgent(BaseAgent):
    """
    Agent responsible for company research and website analysis.
    """
    
    async def analyze_website(self, url: str, scraped_text: str) -> WebsiteAnalysisResult:
        # Register prompt if not exists (in a real app this would be pre-registered)
        prompt_id = "website_analysis_v2"
        if not prompt_registry.get_prompt(prompt_id):
            prompt_registry._prompts[prompt_id] = PromptSchema(
                id=prompt_id,
                version=2,
                description="Perform a deep AI Growth Strategy Audit on a company website.",
                system_instruction="You are a McKinsey consultant, CRO, Sales Director, and AI Strategist combined. Perform a deep, comprehensive Growth Strategy Audit of the provided company based on their website. Do not just summarize the website. Infer, estimate, and hypothesize where data is missing, clearly stating it is an estimate. Quantify your opportunities.",
                supported_capabilities=[Capability.JSON_SCHEMA, Capability.FAST]
            )
            
        context = f"Website URL: {url}\n\nWebsite Snippet:\n{scraped_text}"
        
        result = await self.execute_task(
            task_name="analyze_website",
            prompt_id=prompt_id,
            context=context,
            schema=WebsiteAnalysisResult
        )
        return result

    async def research_company(self, prompt: str) -> 'CompanyResearchResult':
        prompt_id = "company_research_v1"
        if not prompt_registry.get_prompt(prompt_id):
            prompt_registry._prompts[prompt_id] = PromptSchema(
                id=prompt_id,
                version=1,
                description="Research a company and output structured facts and estimates.",
                system_instruction="You are an expert market researcher. Return facts and estimates in JSON format.",
                supported_capabilities=[Capability.JSON_SCHEMA, Capability.REASONING]
            )
            
        result = await self.execute_task(
            task_name="research_company",
            prompt_id=prompt_id,
            context=prompt,
            schema=CompanyResearchResult
        )
        return result

class ResearchFact(BaseModel):
    fact: str
    source: str
    url: str

class ResearchEstimate(BaseModel):
    estimate: str
    confidence: str

class CompanyResearchResult(BaseModel):
    sourced_facts: list[ResearchFact]
    estimates: list[ResearchEstimate]

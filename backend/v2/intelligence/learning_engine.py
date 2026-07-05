import structlog
from v2.intelligence.models import StrategyProposal
from v2.foundation.events.memory_adapter import event_bus
from v2.foundation.events.bus import BaseDomainEvent

logger = structlog.get_logger("learning_engine")

class LearningEngine:
    """
    The background AI supervisor.
    It subscribes to telemetry and mission events (like AIEvaluationGenerated or CallCompleted).
    If it detects systemic failure (e.g., 3 calls dropped at the pricing objection), 
    it generates a StrategyProposal to update the Business Brain.
    """
    
    def __init__(self):
        # Subscribe to relevant events
        event_bus.subscribe("AIEvaluationGenerated", self._handle_evaluation_event)
        event_bus.subscribe("CallCompleted", self._handle_call_completed)
        
        # Internal state to track rolling anomalies (in prod, use Redis/Timeseries DB)
        self._anomaly_counters = {}

    async def _handle_evaluation_event(self, event: BaseDomainEvent):
        """Analyzes Agent Execution performance."""
        payload = event.payload
        if payload.get("status") == "failed":
            logger.warning("learning_engine_detected_failure", agent_id=payload.get("agent_id"))
            # Logic to flag bad prompt versions
            
    async def _handle_call_completed(self, event: BaseDomainEvent):
        """Analyzes Business Outcomes."""
        payload = event.payload
        outcome = payload.get("outcome")
        
        # Example Anomaly Detection logic
        if outcome == "objection_pricing":
            tenant_id = event.tenant_id
            self._anomaly_counters[tenant_id] = self._anomaly_counters.get(tenant_id, 0) + 1
            
            if self._anomaly_counters[tenant_id] >= 3:
                await self._generate_strategy_proposal(tenant_id, "Pricing Objection Spike")
                self._anomaly_counters[tenant_id] = 0 # reset
                
    async def _generate_strategy_proposal(self, tenant_id: str, trigger_reason: str):
        """
        Creates an explainable proposal for the human user to approve.
        In a real system, this would call the LLMGateway to draft the new rebuttal.
        """
        logger.info("generating_strategy_proposal", tenant_id=tenant_id, reason=trigger_reason)
        
        proposal = StrategyProposal(
            tenant_id=tenant_id,
            title="Optimize Pricing Objection Rebuttal",
            description="The AI has failed to overcome the pricing objection 3 times today.",
            evidence=[trigger_reason],
            proposed_changes={
                "objections": {
                    "action": "update",
                    "theme": "pricing",
                    "new_rebuttal": "Instead of defending the price, immediately pivot to the ROI..."
                }
            }
        )
        
        # In a real system, persist this to a repository and emit an event to the Command Center UI
        logger.info("strategy_proposal_generated", proposal_id=proposal.id)

# Initialize the engine to attach subscriptions
learning_engine = LearningEngine()

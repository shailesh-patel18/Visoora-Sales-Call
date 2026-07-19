from .metrics_registry import global_metrics_registry

class ProviderScorer:
    """
    Computes a real-time mathematical score based on data from global_metrics_registry.
    Score = (Success_Rate * W1) - (Latency * W2) - (Cost * W3)
    """

    def __init__(self, weight_success=100.0, weight_latency=0.01, weight_cost=10.0):
        self.weight_success = weight_success
        self.weight_latency = weight_latency
        self.weight_cost = weight_cost

    def calculate_score(self, provider_name: str, base_cost: float = 0.0) -> float:
        """
        Retrieves the provider metrics and computes the score.
        If a provider is completely down or has never succeeded after some attempts, score is severely penalized.
        """
        metrics_list = global_metrics_registry.get_all_metrics()
        provider_data = next((m for m in metrics_list if m["name"] == provider_name), None)

        if not provider_data:
            # New provider, no metrics yet. Give it an optimistic starting score.
            return 80.0 - (base_cost * self.weight_cost)

        status = provider_data["status"]
        if status != "healthy":
            return -1000.0  # Dead provider

        success_rate = provider_data["success_rate"]
        latency = provider_data["latency"]
        total_requests = provider_data["success_count"] + provider_data["failure_count"]

        # If we have low volume, be optimistic
        if total_requests < 5:
            success_rate = max(success_rate, 0.8) # assume 80% success if not proven otherwise
            latency = latency if latency > 0 else 200.0

        score = (success_rate * self.weight_success) - (latency * self.weight_latency) - (base_cost * self.weight_cost)
        return round(score, 2)

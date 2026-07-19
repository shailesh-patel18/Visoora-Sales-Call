from server.prospecting.scoring import ProviderScorer
from server.prospecting.metrics_registry import global_metrics_registry

def test_scoring():
    print("--- TESTING PROVIDER SCORING ---")
    scorer = ProviderScorer()
    
    # 1. No metrics yet (MockProvider)
    score1 = scorer.calculate_score("Mock", base_cost=0.0)
    print(f"Mock (New, Free): {score1}")
    
    # 2. Perfect record, low latency (HunterProvider)
    global_metrics_registry.record("Hunter", success=True, latency_ms=150.0)
    global_metrics_registry.record("Hunter", success=True, latency_ms=130.0)
    score2 = scorer.calculate_score("Hunter", base_cost=0.02)
    print(f"Hunter (Perfect, 140ms, $0.02): {score2}")

    # 3. Failing record, high latency (ApolloProvider)
    global_metrics_registry.record("Apollo", success=False, latency_ms=400.0)
    global_metrics_registry.record("Apollo", success=False, latency_ms=450.0)
    score3 = scorer.calculate_score("Apollo", base_cost=0.05)
    print(f"Apollo (Failing, 425ms, $0.05): {score3}")
    
    # 4. Dead provider
    global_metrics_registry.set_status("DeadProvider", "unhealthy")
    score4 = scorer.calculate_score("DeadProvider", base_cost=0.0)
    print(f"DeadProvider (Unhealthy): {score4}")
    
    assert score1 > score3, "Mock should beat failing Apollo"
    assert score2 > score3, "Hunter should easily beat failing Apollo"
    assert score4 == -1000.0, "DeadProvider should have penalty score"

if __name__ == "__main__":
    test_scoring()

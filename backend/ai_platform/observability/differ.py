from typing import Dict, Any
from server.storage_manager import supabase_admin_client as supabase_client

class MissionDiffer:
    """
    Compares two missions to benchmark planner improvements over time.
    """
    def compare(self, mission_id_a: str, mission_id_b: str) -> Dict[str, Any]:
        """
        Fetches mission records and audit events to compare performance.
        Returns a diff report.
        """
        res_a = supabase_client.table("missions").select("*").eq("id", mission_id_a).execute()
        res_b = supabase_client.table("missions").select("*").eq("id", mission_id_b).execute()
        
        if not res_a.data or not res_b.data:
            raise ValueError("One or both missions not found.")
            
        m_a = res_a.data[0]
        m_b = res_b.data[0]
        
        # In a real implementation, we'd also fetch events to compare latency per node.
        # Here we just compare memory state.
        
        leads_a = m_a.get("memory_snapshot", {}).get("decision_makers", [])
        leads_b = m_b.get("memory_snapshot", {}).get("decision_makers", [])
        
        return {
            "mission_a": mission_id_a,
            "mission_b": mission_id_b,
            "leads_found_diff": len(leads_b) - len(leads_a),
            "planner_a_version": m_a.get("planner_version"),
            "planner_b_version": m_b.get("planner_version"),
            "execution_time_diff_ms": (m_b.get("execution_time_ms") or 0.0) - (m_a.get("execution_time_ms") or 0.0)
        }

import asyncio
import uuid
import logging
from backend.ai_platform.orchestration.graph import ExecutionGraph

logging.basicConfig(level=logging.INFO)

async def test_resume():
    from backend.ai_platform.events.bus import global_event_bus
    global_event_bus.start()
    
    print("--- TESTING GRAPH RESUME ---")
    mission_id = str(uuid.uuid4())
    graph = ExecutionGraph(mission_id)
    
    # We pretend node A and B already ran, and node C needs to run
    previous_results = {
        "task_a": "Done A",
        "task_b": "Done B"
    }
    
    executed_nodes = []
    
    async def task_a(context, results):
        executed_nodes.append("task_a")
        return "Done A"
        
    async def task_b(context, results):
        executed_nodes.append("task_b")
        return "Done B"
        
    async def task_c(context, results):
        executed_nodes.append("task_c")
        return f"{results['task_a']} and {results['task_b']} -> Done C"

    graph.add_node("task_a", task_a)
    graph.add_node("task_b", task_b)
    graph.add_node("task_c", task_c, dependencies=["task_a", "task_b"])
    
    print("Executing graph with previous results...")
    results = await graph.execute(previous_results=previous_results)
    
    print(f"Executed nodes: {executed_nodes}")
    print(f"Final results: {results}")
    
    assert "task_a" not in executed_nodes, "task_a should have been skipped"
    assert "task_b" not in executed_nodes, "task_b should have been skipped"
    assert "task_c" in executed_nodes, "task_c should have run"
    assert results["task_c"] == "Done A and Done B -> Done C"
    
    print("Resume test passed!")

if __name__ == "__main__":
    asyncio.run(test_resume())

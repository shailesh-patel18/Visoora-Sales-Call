import asyncio
import uuid
from ai_platform.memory.mission import MissionMemory
from ai_platform.orchestration.graph import ExecutionGraph

async def test_graph():
    print("--- TESTING EXECUTION GRAPH ---")
    graph = ExecutionGraph()
    memory = MissionMemory(mission_id=str(uuid.uuid4()))
    
    async def task_a(context, results):
        print("Task A (Company Info) running...")
        await asyncio.sleep(1)
        return {"name": "TestCorp", "domain": "testcorp.com"}
        
    async def task_b(context, results):
        print("Task B (People Info) running...")
        await asyncio.sleep(1)
        return [{"name": "Alice"}, {"name": "Bob"}]
        
    async def task_c(context, results):
        print("Task C (Emails) running (depends on B)...")
        people = results.get("task_b", [])
        await asyncio.sleep(0.5)
        return [f"{p['name'].lower()}@testcorp.com" for p in people]

    graph.add_node("task_a", task_a)
    graph.add_node("task_b", task_b)
    graph.add_node("task_c", task_c, dependencies=["task_b"])
    
    import time
    start = time.time()
    results = await graph.execute()
    elapsed = time.time() - start
    
    print(f"Graph completed in {elapsed:.2f}s (Expected ~1.5s because A and B run in parallel)")
    print(f"Results: {results}")
    
    assert elapsed < 2.0, "Graph took too long, nodes didn't run in parallel"
    assert len(results["task_c"]) == 2

if __name__ == "__main__":
    asyncio.run(test_graph())

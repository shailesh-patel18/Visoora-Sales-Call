import asyncio
import logging
import time
from typing import Dict, List, Callable, Any, Awaitable
from ..events.bus import global_event_bus
from ..events.models import NodeStarted, NodeCompleted, NodeFailed

logger = logging.getLogger(__name__)

class MissionPausedException(Exception):
    pass

class ExecutionGraph:
    """
    Directed Acyclic Graph (DAG) executor for running mission tasks concurrently.
    Allows specifying nodes (tasks) and their dependencies, supporting pause/resume.
    """
    def __init__(self, mission_id: str):
        self.mission_id = mission_id
        self.nodes: Dict[str, dict] = {}
        self.results: Dict[str, Any] = {}
        
    def add_node(self, name: str, func: Callable[..., Awaitable[Any]], dependencies: List[str] = None):
        """
        Adds a new node to the graph.
        :param func: An async function that accepts (context, results_dict)
        """
        self.nodes[name] = {
            "func": func,
            "dependencies": dependencies or [],
            "event": asyncio.Event(),
            "task": None
        }

    async def _run_node(self, name: str, context: Any):
        node = self.nodes[name]
        
        # Check if already completed (from a checkpoint)
        if name in self.results:
            logger.info(f"ExecutionGraph: Node '{name}' already completed in checkpoint. Skipping.")
            node["event"].set()
            return
            
        # Wait for all dependencies to complete
        for dep in node["dependencies"]:
            if dep in self.nodes:
                await self.nodes[dep]["event"].wait()
                if isinstance(self.results.get(dep), Exception):
                    # If dependency failed, skip this node
                    logger.warning(f"ExecutionGraph: Skipping '{name}' because dependency '{dep}' failed or paused.")
                    self.results[name] = Exception(f"Dependency {dep} failed/paused")
                    node["event"].set()
                    return
            
        logger.info(f"ExecutionGraph: Starting node '{name}'")
        global_event_bus.publish(NodeStarted(self.mission_id, name))
        start_time = time.time()
        
        try:
            # Execute node function, passing context and previously computed results
            result = await node["func"](context, self.results)
            duration = (time.time() - start_time) * 1000
            
            self.results[name] = result
            logger.info(f"ExecutionGraph: Finished node '{name}'")
            global_event_bus.publish(NodeCompleted(self.mission_id, name, duration, result))
            
        except MissionPausedException as e:
            logger.info(f"ExecutionGraph: Node '{name}' requested mission pause.")
            self.results[name] = {"status": "paused", "reason": str(e)}
            from ..events.models import MissionPaused
            global_event_bus.publish(MissionPaused(self.mission_id))
            
        except Exception as e:
            logger.error(f"ExecutionGraph: Node '{name}' failed with error: {e}")
            self.results[name] = {"status": "error", "reason": str(e)}
            global_event_bus.publish(NodeFailed(self.mission_id, name, str(e)))
            
        finally:
            node["event"].set()

    async def execute(self, context: Any = None, previous_results: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Executes the graph and returns the results.
        If previous_results is provided, skips execution of nodes already present.
        """
        self.results = previous_results or {}
        
        # Create tasks for all nodes
        for name in self.nodes:
            self.nodes[name]["event"].clear()
            self.nodes[name]["task"] = asyncio.create_task(self._run_node(name, context))
            
        # Wait for all tasks to complete
        tasks = [node["task"] for node in self.nodes.values()]
        if tasks:
            await asyncio.gather(*tasks)
            
        return self.results

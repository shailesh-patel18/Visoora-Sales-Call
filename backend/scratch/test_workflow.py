import asyncio
import os
import sys

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ai_platform.workflow.engine import WorkflowEngine
from ai_platform.telemetry import telemetry_tracker

async def main():
    print("Testing WorkflowEngine...")
    
    # Initialize Engine
    engine = WorkflowEngine(tenant_id="test_tenant_123", user_id="user_abc")
    
    # Path to YAML
    yaml_path = "ai_platform/workflow/templates/business_understanding_v1.yaml"
    
    # Context
    context = {
        "website_url": "https://www.visoora.com"
    }
    
    print(f"Executing workflow: {yaml_path}")
    state = await engine.execute(yaml_path, initial_context=context, mode="sync")
    
    print(f"\nExecution ID: {state.execution_id}")
    print(f"Status: {state.status}")
    print(f"Goal: {state.goal}")
    print(f"Completed Steps: {state.completed_steps}")
    print(f"Errors: {state.context.errors}")
    print("\nArtifacts produced:")
    for k, v in state.context.artifacts.items():
        if k != "website_url": # Don't print the input
            print(f"- {k}: [Data Length: {len(str(v))}]")
            
    print("\nCheck local sqlite db 'recordings/local_telemetry.db' to see telemetry events.")

if __name__ == "__main__":
    asyncio.run(main())

import os
import sys
import subprocess
import time

PHASES = [
    {"name": "1. Infrastructure Validation", "path": "tests/01_infrastructure_test.py"},
    {"name": "2. Business Brain Validation", "path": "tests/02_business_brain_test.py"},
    {"name": "3. Sales Pipeline Validation", "path": "tests/03_sales_pipeline_test.py"},
    {"name": "4. Delivery Validation", "path": "tests/04_delivery_test.py"}
]

def print_header(title):
    print(f"\n{'='*50}")
    print(f" {title} ")
    print(f"{'='*50}")

def run_tests():
    print_header("VISOORA PRODUCTION READINESS REPORT")
    
    overall_success = True
    
    for phase in PHASES:
        print(f"\nRunning: {phase['name']}...")
        
        # We assume pytest is installed
        result = subprocess.run(["pytest", phase['path'], "-q"], capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"[PASS] - {phase['name']}")
        else:
            print(f"[FAIL] - {phase['name']}")
            print(f"Details:\n{result.stdout}")
            overall_success = False
            break # Stop executing if previous phase fails
            
    if overall_success:
        print_header("Phase 1-4 Passed. Running Phase 5 (Full Journey)")
        os.environ["RUN_E2E"] = "true"
        result = subprocess.run(["pytest", "tests/05_customer_journey_test.py", "-q"], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("[PASS] - 5. Full Customer Journey")
            print_header("ALL SYSTEMS GO. READY FOR PRODUCTION.")
            sys.exit(0)
        else:
            print("[FAIL] - 5. Full Customer Journey")
            print(f"Details:\n{result.stdout}")
            print_header("[DEPLOYMENT BLOCKED]")
            sys.exit(1)
    else:
        print_header("[DEPLOYMENT BLOCKED] - Fix earlier phases first")
        sys.exit(1)

if __name__ == "__main__":
    # Ensure we run from backend dir
    if not os.path.exists("tests/01_infrastructure_test.py"):
        print("Please run this script from the 'backend' directory.")
        sys.exit(1)
        
    run_tests()

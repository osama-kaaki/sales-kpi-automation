import json
from datetime import datetime
from pathlib import Path
import subprocess
import sys


# Project paths
project_dir = Path(__file__).resolve().parents[1]
scripts_dir = project_dir / "scripts"

logs_dir = project_dir / "logs"
logs_dir.mkdir(exist_ok=True)

status_file = logs_dir / "latest_pipeline_run.json"

clean_script = scripts_dir / "clean_sales_data.py"
kpi_script = scripts_dir  / "calculate_kpis.py"

def write_status(status, stage, message):
    run_status = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "status": status,
        "stage": stage,
        "message": message
    }

    with open(status_file, "w", encoding="utf-8") as file:
        json.dump(run_status, file, indent=4)

    print(f"Run status saved to: {status_file}")

print("\n=== SALES KPI AUTOMATION PIPELINE ===")


#Step 1: Clean and validate data
print("\n[1/2] Running data cleaning and validation...")

clean_result = subprocess.run(
    [sys.executable, str(clean_script)]
)

if clean_result.returncode != 0:
    print("\nPIPELINE STOPPED.")
    print("Cleaning or validation failed.")
    print("KPI calculation was NOT executed.")

    write_status(
        "FAILED",
        "Cleaning / Validation",
        "Cleaning or validation failed, KPI calculation was not executed"
    )

    sys.exit(1)

print("\nCleaning and validation completed successfully.")


# Step 2: Calculate KPIs
print("\n[2/2] Running KPI calculation...")

kpi_result = subprocess.run(
    [sys.executable, str(kpi_script)]
)

if kpi_result.returncode != 0:
    print("\nPIPELINE STOPPED.")
    print(" KPI calculation failed.")

    write_status(
        "FAILED",
        "KPI Calculation",
        "KPI calculation failed."
    )

    sys.exit(1)

write_status(
    "SUCCESS",
    "Completed",
    "Cleaning, validation, and KPI calculation completed successfully."
)

print("\n=== PIPELINE COMPLETED SUCCESSFULLY ===")


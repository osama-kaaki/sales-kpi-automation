import json
import sys
import shutil
import subprocess
import traceback
from pathlib import Path
from datetime import datetime


# Project paths
project_dir = Path(__file__).resolve().parents[1]

config_file = project_dir / "config" / "settings.json"


# Load configuration
with open(config_file, "r", encoding="utf-8") as file:
    config = json.load(file)


workflow_config = config["workflow"]

incoming_dir = project_dir / workflow_config["incoming_dir"]
archive_dir = project_dir / workflow_config["archive_dir"]
delivery_dir = project_dir / workflow_config["delivery_dir"]
logs_dir = project_dir / workflow_config["logs_dir"]
failed_dir = project_dir / workflow_config["failed_dir"]

accepted_extensions = [
    extension.lower()
    for extension in workflow_config["accepted_extensions"]
]

# Make sure workflow folders exist
for folder in [
    incoming_dir,
    archive_dir,
    delivery_dir,
    failed_dir,
    logs_dir
]:
    folder.mkdir(exist_ok=True)

# Ovarall production workflow status
status_file = logs_dir / "latest_run.json"

def write_status(status, stage, message):
    run_status = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "status": status,
        "stage": stage,
        "message": message
    }

    temporary_file = status_file.with_suffix(".tmp")

    with open(temporary_file, "w", encoding="utf-8") as file:
        json.dump(run_status, file, indent=4)

    temporary_file.replace(status_file)

    print(f"workflow status saved to: {status_file}")

try:
    write_status(
        "RUNNING",
        "Input Discovery",
        "Production workflow started. Checking incoming files."
    )


    # Find valid incoming files
    incoming_files = [
        file
        for file in incoming_dir.iterdir()
        if file.is_file()
        and file.suffix.lower() in accepted_extensions
        and not file.name.startswith("~$")
    ]



    print("\n=== PRODUCTION WORKFLOW ===")
    print("Incoming directory:", incoming_dir)
    print("Accepted extensions", accepted_extensions)
    print("Valid incoming files:", len(incoming_files))


    # Safety Gate: no input
    if len (incoming_files) == 0:
        print("\nWORKFLOW STOPPED.")
        print("No valid input file found in incoming folder.")
        
        write_status(
            "STOPPED",
            "Input Discovery",
            "No valid input file fiound in incoming folder."
        )

        sys.exit(1)

    # Saftey Gate: abiguous input
    if len(incoming_files) > 1:
        print("\nWORKFLOW STOPPED.")
        print("Multiple valid input files found:")

        for file in incoming_files:
            print("-", file.name)

        print("Only one input file is allowed per run.")

        write_status(
            "STOPPED",
            "Input Discovery",
            "Multiple valid input files found: "
            + ", ".join(file.name for file in incoming_files)
            + ". Only one input file is allowed per run."
        )

        sys.exit(1)


    selected_input = incoming_files[0]

    print("\nInput file selected successfully:")
    print(selected_input)

    # Prepare selected client file for the python engine 
    engine_input = project_dir / config["files"]["raw_sales_data"]

    shutil.copy2(
        selected_input,
        engine_input
    )

    print("\nInput file staged successfully for the engine:")
    print(engine_input)

    # Run the core pipeline 
    pipeline_script = project_dir / "scripts" / "run_pipeline.py"

    # Create timestamp for production outputs
    timestamp  = datetime.now().strftime("%Y%m%d_%H%M%S")

    print("\nStarting core pipeline...")

    pipeline_result = subprocess.run(
        [sys.executable, str(pipeline_script)]
    )

    if pipeline_result.returncode != 0:
        print("\nPRODUCTION WORKFLOW FAILED.")
        print("Core pipeline failed.")

        # Create a dedicated folder for this failed run
        failed_run_dir = failed_dir / f"failed_run_{timestamp}"
        failed_run_dir.mkdir(exist_ok=True)

        # Move original client input into quarantine
        failed_input = failed_run_dir / selected_input.name

        shutil.move(
            selected_input,
            failed_input
        )

        print("\nFailed client input moved to quarantine:")
        print(failed_input)

        # Copy validation report if it exists
        validation_report = (
            project_dir / config["files"]["validation_report"]
        )

        if validation_report.exists():
            shutil.copy2(
                validation_report,
                failed_run_dir / validation_report.name
            )

            print("\nValidation report copied to failed run folder.")

        # Copy audit report if it exists
        audit_report = (
            project_dir / config["files"]["audit_report"]
        )

        if audit_report.exists():
            shutil.copy2(
                audit_report,
                failed_run_dir / audit_report.name
            )

            print("\nAudit report copied to failed run folder")

        if engine_input.exists():
            engine_input.unlink()

            print("\nStaged engine input removed after failure.")

        write_status(
            "FAILED",
            "Core Pipeline",
            "Core Pipeline failed. Input quarantined, available reports "
            "copied, and staged input removed. See latest_pipeline_run.json "
            "for pipeline failure details."
        )
        sys.exit(1)

    print("\nCore pipeline completed successfully.")

    # Prepare KPI report for client delivery
    kpi_report = project_dir / config["files"]["kpi_report"]

    if not kpi_report.exists():
        print("\nPRODUCTION WORKFLOW FAILED.")
        print("Expected KPI report was not found.")

        write_status(
            "FAILED",
            "Report Verification",
            "Core pipeline returned success, but the expected KPI report "
            "was not found. No report delivered. Input remains in incoming."
        )

        if engine_input.exists():
            engine_input.unlink()
            print("\nStaged engine input removed after missing report.")

        sys.exit(1)


    delivery_file = (
        delivery_dir
        / f"sales_kpi_report_{timestamp}.xlsx"
    )

    shutil.copy2(
        kpi_report,
        delivery_file
    )

    print("\nKPI report copied to delivery:")
    print(delivery_file)


    #Archive processed client input
    archive_file = (
        archive_dir
        / f"{selected_input.stem}_{timestamp}{selected_input.suffix}"
    )

    shutil.move(
        selected_input,
        archive_file
    )

    print("\nClient input archived successfully:")
    print(archive_file)

    if engine_input.exists():
        engine_input.unlink()

        print("\nStaged engine input removed after successful run.")

    write_status(
        "SUCCESS",
        "Completed",
        "Production workflow completed successfully. "
        "KPI report copied to delivery, original input archived, "
        "and staged input removed."
    )

except Exception as error:
    print("\nPRODUCTION WORKFLOW FAILED: unexpected error.")
    traceback.print_exc()

    try:
        write_status(
            "FAILED",
            "Workflow Execution",
            f"{type(error).__name__}: {error}. "
            "Workflow may be partially completed. "
            "Review files and terminal output before retrying."
        )

    except Exception as logging_error:
        print(f"Could not save  FAILED status: {logging_error}")

    sys.exit(1)
# Sales KPI Automation & Performance Reporting System

> Portfolio demonstration project built with sample sales data.

An end-to-end sales reporting and business automation solution built with **Python, Excel, Power BI, data validation, and scheduled local workflow execution**.

The project transforms incoming Excel sales data into validated reporting outputs, blocks unsafe datasets before KPI calculation, generates management KPIs, organizes delivery and archive files, and supports an interactive Power BI management dashboard.

## Key Features

- Automated Excel data intake and processing
- Data cleaning and validation safety gates
- Automatic pipeline stop when critical validation rules fail
- Sales KPI calculation and Excel reporting
- Delivery, archive, failed-run, and logging workflow
- Scheduled local execution using Windows Task Scheduler
- Interactive Power BI management dashboard
- Salesperson target and performance analysis
- Drill-through salesperson detail pages
- Context-sensitive Power BI tooltips
- Target-period and breakdown safeguards

## Technology Stack

**Python • Pandas • OpenPyXL • Excel • Power BI • DAX • JSON • Windows Task Scheduler**

## Documentation

For a detailed walkthrough of the business problem, validation logic, production workflow, KPI engine, Power BI dashboard, and project outcomes:

[View the full project case study](documentation/CASE_STUDY.md)

[Client Input Template](documentation/CLIENT_INPUT_TEMPLATE.md)

## Workflow

```
Incoming Excel File
        |
        v
Input Discovery & Staging
        |
        v
Data Cleaning & Validation
        |
        +--------------------------+
        |                          |
   Validation Pass            Validation Fail
        |                          |
        v                          v
Clean Dataset             Validation / Audit Reports
        |                          |
        |                          v
        |                    Failed Run Folder
        |                          |
        |                     Pipeline Stops
        |
        +--------------------+
        |                    |
        v                    v
KPI Calculation      Power BI Management Dashboard
        |              (separate refresh)
        v
Excel KPI Report
        |
        v
Delivery + Archive + Logs

```

## Dashboard Preview

![Sales Performance Dashboard](<documentation/screenshots/Sales Overview.png>)

The Power BI dashboard provides management with a consolidated view of sales performance, profitability, pipeline value, target achievement, salesperson performance, and sales trends.

For a detailed walkthrough of the dashboard logic, drill-through analysis, validation workflow, and project outcomes, see the [full case study](documentation/CASE_STUDY.md).

## Project Structure

```
Sales_KPI_Automation/
│
├── config/
│   └── settings.json
│
├── data_raw/
│   └── Raw and test sales datasets
│
├── data_processed/
│   └── Generated clean data and reporting outputs
│
├── incoming/
│   └── Incoming client files waiting for processing
│
├── delivery/
│   └── Successfully generated KPI reports
│
├── archive/
│   └── Successfully processed source files
│
├── failed/
│   └── Failed runs and validation evidence
│
├── logs/
│   └── Runtime workflow status files
│
├── scripts/
│   ├── data_profile.py
│   ├── clean_sales_data.py
│   ├── calculate_kpis.py
│   ├── run_pipeline.py
│   └── production_workflow.py
│
├── powerbi/
│   └── Sales_Performance_Dashboard_Project/
│       ├── Sales_Performance_Dashboard_Project.pbip
│       ├── Sales_Performance_Dashboard_Project.Report/
│       └── Sales_Performance_Dashboard_Project.SemanticModel/
│
├── documentation/
│   ├── CASE_STUDY.md
│   ├── Sales KPI Production Workflow.xml
│   └── screenshots/
│
├── requirements.txt
└── README.md
```

## Requirements

- Python 3.13
- Microsoft Excel or another application capable of opening `.xlsx` files
- Power BI Desktop for the interactive dashboard
- Windows Task Scheduler for optional scheduled local execution

### Python Dependencies

Install the required Python packages from the project root:

```powershell
pip install -r requirements.txt
```

The project currently uses:

- pandas 3.0.5
- openpyxl 3.1.5

## How to Run

### 1. Prepare the Input

Place **one `.xlsx` sales file** inside the `incoming/` folder.

The production workflow expects a single valid input file. If no file is found, or if multiple valid input files are present, the workflow stops without processing.

### 2. Run the Production Workflow

From the project root, activate the Python virtual environment if required, then run:

```powershell
python scripts/production_workflow.py
```

The workflow will:

1. Discover the incoming Excel file
2. Stage it for processing
3. Clean and validate the dataset
4. Stop automatically if critical validation rules fail
5. Calculate KPIs when validation passes
6. Generate the Excel KPI report
7. Copy the completed report to `delivery/`
8. Archive the processed source file
9. Save workflow status information to `logs/`

### 3. Review the Output

After a successful run:

- Generated KPI reports are available in `delivery/`
- Processed source files are moved to `archive/`
- Workflow status is recorded in `logs/`

If validation fails:

- KPI calculation is blocked
- Validation evidence is generated
- The failed input and related evidence are preserved under `failed/`

### 4. Refresh Power BI

After a successful production workflow run, open:

```text
powerbi/Sales_Performance_Dashboard_Project/Sales_Performance_Dashboard_Project.pbip
```

Before refreshing the report:

1. Open **Transform data → Manage Parameters** in Power BI Desktop.
2. Select `DataFilePath`.
3. Set its value to the local absolute path of:

```text
data_processed/clean_sales_data.xlsx
```

For example:

```text
C:\Path\To\Sales_KPI_Automation\data_processed\clean_sales_data.xlsx
```

4. Apply the change and refresh the report.

> The repository uses a placeholder path for `DataFilePath` so that no machine-specific user path is stored in source control.

> Power BI refresh is currently separate from the scheduled Python production workflow.
# Sales KPI Automation & Performance Reporting System

**Portfolio demonstration project built with sample sales data.**

**Python • Excel • Power BI • Data Validation • Automated Reporting**

## Project Overview

This project is an end-to-end sales reporting and automation solution designed to transform raw Excel sales data into validated, management-ready reports and interactive Power BI insights.

The workflow checks incoming files, validates and cleans the data, blocks invalid datasets before KPI calculation, calculates sales performance metrics, generates Excel reporting outputs, archives processed files, and supports an interactive Power BI dashboard for management analysis.

## The Business Problem

Sales reporting is often handled through manually maintained Excel files. This creates several operational problems:

- Inconsistent or incorrect data can reach management reports.
- KPI calculations may depend on repetitive manual work.
- Sales managers may struggle to compare salesperson performance against targets.
- Reporting becomes harder to repeat consistently as data grows.
- Errors may only be discovered after reports have already been produced.

The objective was to create a repeatable reporting workflow that validates the data first, automates KPI calculation, and gives management a clear view of sales performance.

## The Solution

The solution was designed as a controlled reporting workflow rather than a single reporting script.

It combines four main layers:

- **Production intake and scheduling** — incoming Excel files can be processed through a repeatable local production workflow, with scheduled execution available through Windows Task Scheduler.
- **Data validation and safety controls** — incoming data is checked for schema issues, missing required values, duplicate lead IDs, invalid statuses, and other business-rule violations before KPI calculation.
- **Automated KPI reporting** — validated data is cleaned and standardized, then used to calculate sales, profitability, conversion, pipeline, salesperson, lead-source, and product performance metrics.
- **Management reporting** — processed results support an interactive Power BI dashboard with salesperson targets, rankings, performance status, intervention priority, trends, and drill-through analysis.

## Solution Architecture

```
Incoming Excel File
        |
        v
Production Workflow
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
The workflow is intentionally designed to stop when critical validation rules fail. This prevents invalid data from continuing into KPI calculation and management reporting.

## Safety & Validation

A key part of the solution is preventing unreliable data from reaching management reporting.

Before KPI calculation begins, the workflow validates the incoming dataset against required structural and business rules. The checks include:

- Required columns and values
- Duplicate Lead IDs
- Allowed lead statuses
- Required close dates for closed deals (Won/Lost)
- Required cost values for won deals
- Standardized lead-source and product/service values
- Data-type and date validation

If a critical validation rule fails, the workflow stops automatically. A validation report and audit information are preserved, KPI calculation is not executed, and the failed input is isolated for investigation.

This safety gate helps prevent incorrect or unsupported records from producing misleading sales KPIs.

![Validation Failure - Safety Gate](<screenshots/Validation Failure - Safety Gate.png>)

*Safety Gate in action: an invalid lead status is detected, the validation report is generated, KPI calculation is blocked, and the production workflow stops before invalid data reaches management reporting.*

## Automated Production Workflow

The reporting process is designed to run as a repeatable local production workflow rather than relying on manual script execution.

The workflow can be scheduled through Windows Task Scheduler. When triggered, it checks the incoming folder, selects the valid input file, stages it for processing, runs the validation and KPI pipeline, delivers the generated report, archives the original input, and records the workflow status in log files.

### Scheduled Execution

![Scheduled Production Workflow](<screenshots/Scheduled Production Workflow.png>)

*The production workflow is configured in Windows Task Scheduler and has been successfully executed through a scheduled task.*

### Successful Production Run

**Power BI refresh note:** The local production workflow automates data validation, KPI processing, delivery, archiving, and logging. Power BI refresh is currently performed separately in Power BI Desktop and is not part of the scheduled local workflow.

![Successful Production Run](<screenshots/Successful Production Run.png>)

*After successful validation and KPI processing, the generated report is copied to the delivery folder, the client input is archived, the staged processing file is removed, and the workflow status is saved.*

## KPI Engine & Reporting Outputs

After the dataset passes validation, the KPI engine calculates management-ready sales metrics and exports the results to Excel.

The KPI output includes:

- Total Leads
- Won Deals
- Lost Deals
- Open Deals
- Pending Deals
- Lead Conversion Rate
- Closed Deal Win Rate
- Total Sales
- Total Cost
- Gross Profit
- Average Won Deal Value
- Salesperson performance
- Lead-source performance
- Product/service performance

The generated Excel report contains structured KPI outputs that can be reviewed directly, while the validated cleaned dataset supports the Power BI reporting layer.

For the demonstration dataset, the validated output produced:

- **14 total leads**
- **8 won deals**
- **3 lost deals**
- **2 open deals**
- **1 pending deal**
- **SAR 104,300 total sales**
- **SAR 50,500 total cost**
- **SAR 53,800 gross profit**
- **57.14% lead conversion rate**
- **72.73% closed-deal win rate**

These results were validated against the Power BI dashboard to confirm that the reporting layer and automation engine were producing consistent results.

## Power BI Management Dashboard

The validated cleaned dataset supports an interactive Power BI dashboard designed for management review, with DAX measures providing the management KPI and performance analysis layer.

The dashboard provides:

- Executive KPI cards for leads, sales, cost, gross profit, conversion, win rate, pipeline value, MTD, and YTD sales
- Sales performance by salesperson
- Target achievement and target gap analysis
- Sales contribution and ranking
- Performance status and intervention priority
- Sales trends and month-over-month growth
- Sales breakdown by region, lead source, and product/service
- Interactive filtering
- Salesperson drill-through analysis
- Context-sensitive tooltips
- Target evaluation is enabled only when the full May–June 2026 target period is selected
- Target comparison is disabled for Region, Lead Source, and Product/Service breakdowns because targets are allocated at salesperson level

### Sales Overview

![Sales Overview](<screenshots/Sales Overview.png>)

*The main management dashboard provides a consolidated view of sales performance, targets, profitability, pipeline value, trends, and salesperson performance.*

### Salesperson Detail Analysis

![Salesperson Details - Sara](<screenshots/Salesperson Details – Sara.png>)

*The drill-through detail page provides salesperson-level analysis, target achievement, target gap, profitability, transaction details, and management assessment.*

### Interactive Salesperson Tooltip

![Salesperson Tooltip - Sara](<screenshots/Salesperson Tooltip – Sara.png>)

*Interactive tooltips provide quick access to salesperson performance, target achievement, performance status, and intervention priority without leaving the main dashboard.*

## Business Value

This project demonstrates how a manual sales reporting process can be transformed into a controlled and repeatable reporting workflow.

The solution provides several practical benefits:

- Reduces repetitive manual KPI calculation
- Adds validation before management reporting
- Prevents invalid datasets from reaching KPI outputs
- Creates a consistent reporting process for recurring sales files
- Preserves failed-run diagnostics for troubleshooting
- Automatically separates delivery, archive, failed, and log outputs
- Provides management with clear sales, profitability, pipeline, and target insights
- Supports salesperson-level performance review and intervention decisions
- Creates a reporting structure that can be extended as business requirements grow

The solution was built as a demonstration project using sample sales data, so no unverified claims about time savings or financial impact are made.

## Technical Stack

The project combines multiple tools and technologies to create the end-to-end reporting workflow:

- **Python** — data cleaning, validation, KPI calculation, workflow control, logging, and file handling
- **Pandas** — Excel data processing and transformation
- **OpenPyXL** — Excel report generation and workbook handling
- **JSON Configuration** — centralized business rules, file settings, allowed statuses, mappings, and workflow configuration
- **Microsoft Excel** — source data and generated KPI reporting outputs
- **Power BI** — interactive management dashboard, DAX measures, targets, rankings, drill-through analysis, and tooltips
- **Windows Task Scheduler** — scheduled local execution of the production workflow
- **Visual Studio Code** — development and testing environment

The project structure separates configuration, raw data, processed outputs, incoming files, delivery files, archives, failed runs, logs, documentation, scripts, and Power BI assets to make the workflow easier to maintain and extend.

## Project Outcome

The final solution demonstrates a complete local sales reporting workflow that moves beyond manual spreadsheet reporting.

The project combines data validation, automated KPI calculation, structured Excel outputs, scheduled execution, workflow logging, failure handling, and interactive Power BI reporting in one repeatable process.

The completed solution demonstrates the ability to:

- Turn raw Excel data into validated reporting outputs
- Apply business rules before KPI calculation
- Stop unsafe or invalid runs automatically
- Generate repeatable management KPIs
- Organize delivery, archive, failed-run, and log outputs
- Support scheduled local workflow execution
- Build an interactive Power BI management dashboard
- Support salesperson-level performance analysis and management intervention

This project is intended as a portfolio demonstration of end-to-end data reporting and business automation capabilities.
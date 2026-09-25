# Client Input Template

This document defines the expected structure of the client sales input file used by the Sales KPI Automation & Performance Reporting System.

## Accepted File Format

The production workflow accepts:

- `.xlsx` Excel files
- One valid input file per production run

Temporary Excel files beginning with `~$` are ignored.

If no valid input file is found, the workflow stops.
If more than one valid input file is found, the workflow also stops rather than selecting a file automatically.

## Required Columns

The client input file must contain the following columns:

| Column | Purpose |
|---|---|
| `Lead_ID` | Unique identifier for each lead |
| `Lead_Date` | Date the lead was created |
| `Close_Date` | Date the lead was closed, when applicable |
| `Customer_Name` | Customer or prospect name |
| `Salesperson` | Salesperson responsible for the lead |
| `Product_Service` | Product or service associated with the lead |
| `Lead_Source` | Source of the lead |
| `Lead_Status` | Current lead or deal status |
| `Deal_Value` | Deal value |
| `Cost` | Associated cost |
| `Target` | Sales target |
| `Region` | Sales region |

## Supported Lead Statuses

The current workflow supports the following statuses:

- `Won`
- `Lost`
- `Open`
- `Pending`

Unrecognized or ambiguous statuses may cause validation to fail.

The validation layer may automatically correct selected safe status variations when explicitly configured.

For example:

- `Wonn` → `Won`

Ambiguous statuses such as `Completed` are not automatically interpreted.

## Conditional Requirements

Some columns must exist in the input file but are conditionally required at row level.

### Cost

`Cost` must be provided for records where:

```text
Lead_Status = Won
```

### Close Date

`Close_Date` must be provided for records where:

```text
Lead_Status = Won
```

or:

```text
Lead_Status = Lost
```

Open or Pending leads may therefore have a blank `Close_Date`.

## Data Quality Rules

The validation layer checks for issues including:

- Missing required columns
- Duplicate `Lead_ID` values
- Missing required values
- Unsupported lead statuses
- Won deals without cost
- Won or Lost deals without close dates
- Invalid numeric values
- Invalid dates
- Negative `Deal_Value`
- Negative `Cost`
- Negative `Target`

Critical validation failures stop KPI processing.

## Client Preparation Checklist

Before submitting a file:

1. Use the required column names exactly.
2. Keep one row per lead.
3. Make sure every `Lead_ID` is unique.
4. Use supported lead statuses.
5. Provide `Cost` for Won deals.
6. Provide `Close_Date` for Won and Lost deals.
7. Use valid dates and numeric values.
8. Do not use negative values for `Deal_Value`, `Cost`, or `Target`.
9. Submit only one `.xlsx` file for each production run.

## Processing Flow

A valid client file is processed through the following sequence:

```text
Client Excel File
        ↓
Input Discovery
        ↓
Data Cleaning
        ↓
Validation
        ↓
KPI Calculation
        ↓
Excel KPI Report
        ↓
Delivery / Archive / Logging
```

If validation fails, KPI calculation is blocked and validation evidence is preserved for review.

## Implementation Note

The sample project currently uses demonstration-specific date rules in its configuration.

These rules must be reviewed and adjusted before onboarding a new client so that the allowed date ranges match the client's actual reporting period.
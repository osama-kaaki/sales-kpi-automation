import json
from pathlib import Path
import pandas as pd
import re
import sys

# Project paths
project_dir = Path(__file__).resolve().parents[1]

config_file = project_dir / "config" / "settings.json"

with open(config_file, "r", encoding="utf-8") as file:
    config = json.load(file)

print("Configuration loaded successfully.")
print("Allowed statuses:", config["allowed_statuses"])

input_file = project_dir / config["files"]["raw_sales_data"]
output_file = project_dir / config["files"]["clean_sales_data"]
validation_report_file = project_dir / config ["files"]["validation_report"]
audit_report_file = project_dir / config ["files"]["audit_report"]
kpi_report_file = project_dir / config ["files"]["kpi_report"]

# Remove stale run-specific outputs from previous runs
for stale_file in [
    validation_report_file,
    kpi_report_file,
    audit_report_file
]:
    print(f"Checking stale file: {stale_file}")

    if stale_file.exists():
        print(f"Deleting stale file: {stale_file}")
        stale_file.unlink()
        print(f"Deleted successfully: {not stale_file.exists()}")
    else:
        print("file does not exist.")

#Load raw data
df = pd.read_excel(input_file)

#Validated required columns before cleaning
required_schema_columns = config["required_schema_columns"]

missing_columns = [
    column
    for column in required_schema_columns
    if column not in df.columns
]

if missing_columns:
    print("\n--- SCHEMA VALIDATION FAILED ---")
    print(
        "Missing required columns: "
        + ", ".join(missing_columns)
    )

    sys.exit(1)

print("Schema validation passed.")

print("Rows before cleaning:", len(df))

#Convert cells that contain only spaces into missing values
df = df.replace(r"^\s*$", pd.NA, regex=True)

#Remove completely empty rows
df = df.dropna(how="all")

print("Rows after removing blank rows:", len(df))

#Remove exact duplication rows
df = df.drop_duplicates()

print("Rows after removing duplicates:", len(df))

#Clean text columns
text_columns = [
    "Customer_Name",
    "Salesperson",
    "Product_Service",
    "Lead_Source",
    "Lead_Status",
    "Region"
]

for column in text_columns:
    df[column] = (
        df[column]
        .astype("string")
        .str.replace("\u200b", "", regex=False)     # zero-width space
        .str.replace("\ufeff", "", regex=False)     # hidden BOM
        .str.replace("\u00a0", "", regex=False)     # non-breaking space
        .str.strip()
        .str.replace(r"\s+", " ", regex=True)
    )

#Standardize salesperson names
df["Salesperson"] = df["Salesperson"].str.title()

#Standardize lead status
df["Lead_Status"] = df["Lead_Status"].str.title()

# Track safe automatic corrections
autofix_log = []

# Safe automatic fixes for known Lead_Status types
safe_status_fixes = config["safe_status_corrections"]

for original_value, corrected_value in safe_status_fixes.items():

    fix_mask = df["Lead_Status"] == original_value

    rows_to_fix = df.loc[
        fix_mask,
        ["Lead_ID", "Customer_Name", "Lead_Status"]
    ]

    for _, row in rows_to_fix.iterrows():
        autofix_log.append({
            "Lead_ID": row["Lead_ID"],
            "Customer_Name": row["Customer_Name"],
            "Field": "Lead_Status",
            "Original_Value": original_value,
            "Corrected_Value": corrected_value,
            "Action": "Auto-Fixed",
            "Reason": "Approved exact typo correction"
        })

df["Lead_Status"] = df["Lead_Status"].replace(
    safe_status_fixes
)

if autofix_log:
    print("\n--- SAFE AUTO-FIXES APPLIED ---")

    autofix_df = pd.DataFrame(autofix_log)

    print(
        autofix_df.to_string(index=False)
    )

#Standardize lead source
df["Lead_Source"] = df["Lead_Source"].str.title()

#Fix brand name formatting
df["Lead_Source"] = df["Lead_Source"].replace(
    config["lead_source_corrections"]
    )

print("\nLead source values after cleaning:")
print(df["Lead_Source"].unique())

print("\nSalesperson values after cleaning:")
print(df["Salesperson"].unique())

print("\nLead status values after cleaning:")
print(df["Lead_Status"].unique())

#Standardize product/service names
service_key = (
        df["Product_Service"]
        .str.lower()
        .str.replace(r"\s+", "", regex=True)
    )
service_map = config["product_service_map"]

df["Product_Service"] = (
        service_key
        .map(service_map)
        .fillna(df["Product_Service"])
    )

# Preserve original Deal_Value for validation/audit
original_deal_value = df["Deal_Value"].copy()

#Clean Deal_Value
df["Deal_Value"] = (
        df["Deal_Value"]
        .astype("string")
        .str.replace("SAR", "", case=False, regex=False)
        .str.replace(",", "", regex=False)
        .str.strip()
    )

df["Deal_Value"] = pd.to_numeric(
        df["Deal_Value"],
        errors="coerce"
    )

# Detect values that existed in raw data but could not be converted to numbers
invalid_deal_value_mask = (
    original_deal_value.notna()
    & df["Deal_Value"].isna()
)

invalid_deal_value_rows = df.loc[
    invalid_deal_value_mask,
    ["Lead_ID", "Customer_Name"]
].copy()

invalid_deal_value_rows["Field"] = "Deal_Value"
invalid_deal_value_rows["Original_Value"] = (
    original_deal_value.loc[invalid_deal_value_mask].astype("string").values
)
invalid_deal_value_rows["Issue"] = "Invalid numeric value"

# Detect negative Deal_Value
negative_deal_value_rows = df.loc[
    df["Deal_Value"].notna()
    & (df["Deal_Value"] < 0),
    [
        "Lead_ID",
        "Customer_Name",
        "Salesperson",
        "Lead_Status",
        "Deal_Value"
    ]
].copy()

negative_deal_value_rows["Field"] = "Deal_Value"
negative_deal_value_rows["Issue"] = "Negative value not allowed"

print("\nProduct service values after cleaning:")
print(df["Product_Service"].unique())

print("\nDeal value values after cleaning:")
print(df["Deal_Value"].unique())
print("\nDeal_Value data after cleaning:")
print(df["Deal_Value"].dtype)

from datetime import datetime

def clean_date(value, start_date=None, end_date=None):
    if pd.isna(value):
        return pd.NaT

    candidates = []

    # Excel already loaded the value as a real date
    if isinstance(value, (datetime, pd.Timestamp)):
        date_value = pd.Timestamp(value)
        candidates.append(date_value)

        # Also try swapping month/day for ambiguous Excel dates
        try:
            swapped_date = pd.Timestamp(
                year=date_value.year,
                month=date_value.day,
                day=date_value.month
            )

            if swapped_date not in candidates:
                candidates.append(swapped_date)

        except ValueError:
            pass

    else:
        text_value = str(value).strip()

        possible_formats = [
            "%Y-%m-%d",
            "%Y/%m/%d",
            "%d/%m/%Y",
            "%d-%m-%Y",
            "%m/%d/%Y",
            "%m-%d-%Y",
            "%d/%m/%y",
            "%d-%m-%y",
            "%m/%d/%y",
            "%m-%d-%y",
            "%d %b %Y",
            "%d %B %Y",
            "%b %d %Y",
            "%B %d %Y",
        ]

        for fmt in possible_formats:
            parsed_date = pd.to_datetime(
                text_value,
                format=fmt,
                errors="coerce"
            )

            if not pd.isna(parsed_date):
                if parsed_date not in candidates:
                    candidates.append(parsed_date)

    if not candidates:
        return pd.NaT

    # If business date limits were supplied,
    # choose the interpretation that fits them
    if start_date is not None and end_date is not None:
        for candidate in candidates:
            if start_date <= candidate <= end_date:
                return candidate

        return pd.NaT

    return candidates[0]

# Business date rules for the current dateset
date_rules = {
    column: {
        "start": pd.Timestamp(rules["start"]),
        "end": pd.Timestamp(rules["end"])
    }
    for column, rules in config["date_rules"].items()
}

# Preserve original Lead_Date for validation/audit
original_leaad_date = df["Lead_Date"].copy()
original_close_date = df["Close_Date"].copy()

#Clean dates
df["Lead_Date"] = df["Lead_Date"].apply(
    lambda x: clean_date(
        x,
        date_rules["Lead_Date"]["start"],
        date_rules["Lead_Date"]["end"]
    )
)

df["Close_Date"] = df["Close_Date"].apply(
    lambda x: clean_date(
        x,
        date_rules["Close_Date"]["start"],
        date_rules["Close_Date"]["end"]
    )
)

print("\nLead dates after cleaning:")
print(df["Lead_Date"].unique())

print("\nClose dates after cleaning:")
print(df["Close_Date"].unique())

print("\nDate data type:")
print(df[["Lead_Date", "Close_Date"]].dtypes)

# Detect Lead_Date values that existed but could not be converted to valid dates
invalid_lead_date_mask = (
    original_leaad_date.notna()
    & df["Lead_Date"].isna()
)

invalid_lead_date_rows = df.loc[
    invalid_lead_date_mask,
    [
        "Lead_ID",
        "Customer_Name",
        "Salesperson"
    ]
].copy()

invalid_lead_date_rows["Field"] = "Lead_Date"

invalid_lead_date_rows["Original_Value"] = (
    original_leaad_date.loc[invalid_lead_date_mask]
    .astype("string")
    .values
)

invalid_lead_date_rows["Issue"] = "Invalid date value"

# Detect Close_Date values that existed but could not be converted
invalid_close_date_mask = (
    original_close_date.notna()
    & df["Close_Date"].isna()
)

invalid_close_date_rows = df.loc[
    invalid_close_date_mask,
    [
        "Lead_ID",
        "Customer_Name",
        "Salesperson"
    ]
].copy()

invalid_close_date_rows["Field"] = "Close_Date"

invalid_close_date_rows["Original_Value"] = (
    original_close_date.loc[invalid_close_date_mask]
    .astype("string")
    .values
)

invalid_close_date_rows["Issue"] = "invalid date value"

# Preserve original Cost for validation/audit
original_cost = df["Cost"].copy()

# Preserve original Target for validation/audit
original_target =df["Target"].copy()

# Clean numeric columns
df["Cost"] = pd.to_numeric(df["Cost"], errors="coerce")
df["Target"] = pd.to_numeric(df["Target"],errors="coerce")

#Detect Cost values that existed but could not  be converted to numbers
invalid_cost_mask = (
    original_cost.notna()
    & df["Cost"].isna()
)

invalid_cost_rows =df.loc[
    invalid_cost_mask,
    [
        "Lead_ID",
        "Customer_Name",
        "Salesperson",
        "Lead_Status"
    ]
].copy()

invalid_cost_rows["Field"] = "Cost"

invalid_cost_rows["Original_Value"] = (
    original_cost.loc[invalid_cost_mask]
    .astype("string")
    .values
)

invalid_cost_rows["Issue"] = "Invalid numeric value"

# Detect Target values that existed but could not be converted to numbers
invalid_target_mask = (
    original_target.notna()
    & df["Target"].isna()
)

invalid_target_rows = df.loc[
    invalid_target_mask,
    [
        "Lead_ID",
        "Customer_Name",
        "Salesperson"
    ]
].copy()

invalid_target_rows["Field"] = "Target"

invalid_target_rows["Original_Value"] = (
    original_target.loc[invalid_target_mask]
    .astype("string")
    .values
)

invalid_target_rows["Issue"] = "Invalid numeric value"

# Detect negative Cost
negative_cost_rows = df.loc[
    df["Cost"].notna()
    & (df["Cost"] < 0),
    [
        "Lead_ID",
        "Customer_Name",
        "Salesperson",
        "Lead_Status",
        "Cost"
    ]
].copy()

negative_cost_rows["Field"] = "Cost"
negative_cost_rows["Issue"] = "Negative value not allowed"

# Detect negative Target
negative_target_rows = df.loc[
    df["Target"].notna()
    & (df["Target"] < 0),
    [
        "Lead_ID",
        "Customer_Name",
        "Salesperson",
        "Target"
    ]
].copy()

negative_target_rows["Field"] = "Target"
negative_target_rows["Issue"] = "Negative value not allowed"

#Standardize region names
df["Region"] = df["Region"].str.title()

#Final validation
print("\n--- Final Validation ---")

print("Rows:", len(df))
print("Duplicated Lead IDs:", df["Lead_ID"].duplicated().sum())

required_value_columns = config["required_value_columns"]

print("\nMissing values in required columns:")
print(df[required_value_columns].isna().sum())

#Validate allowed lead statuses
allowed_statuses = config["allowed_statuses"]

status_roles = config["status_roles"]

won_status = status_roles["won"]
lost_status = status_roles["lost"]

invalid_statuses = df[
    ~df["Lead_Status"].isin(allowed_statuses)
]

print("\nInvalid Lead Status rows:", len(invalid_statuses))

#Won deals should have a cost
missing_cost = df[
    (df["Lead_Status"] == won_status)
    & (df["Cost"].isna())
    & (~invalid_cost_mask)
]

print(
    "Won deals missing Cost:",
    len(missing_cost)
)

#Won/Lost deals should have a Close_date
missing_close_date = df[
    df["Lead_Status"].isin([won_status, lost_status])
    & df["Close_Date"].isna()
    & ~invalid_close_date_mask
]

print(
    "Won/Lost deals missing Close_date:",
    len(missing_close_date)
)

# Stop pipeline if validation fails
validation_errors = []

duplicate_lead_ids = df["Lead_ID"].duplicated().sum()

missing_required_values = (
    df[required_value_columns].isna().sum().sum()
    - len(invalid_deal_value_rows)
    - len(invalid_target_rows)
    - len(invalid_lead_date_rows)
)

missing_required_rows = []

for column in required_value_columns:
    missing_mask = df[column].isna()

    if column == "Deal_Value":
        missing_mask = missing_mask & ~invalid_deal_value_mask

    if column == "Target":
        missing_mask = missing_mask & ~invalid_target_mask

    if column == "Lead_Date":
        missing_mask = missing_mask & ~invalid_lead_date_mask

    for _, row in df.loc[missing_mask].iterrows():
        missing_required_rows.append({
            "Lead_ID": row.get("Lead_ID", ""),
            "Customer_Name": row.get("Customer_Name", ""),
            "Field": column,
            "Issue": "Missing required value"
        })

if len(invalid_deal_value_rows) > 0:
    validation_errors.append(
        f"Invalid Deal_Value numeric rows: {len(invalid_deal_value_rows)}"
    )

if len(invalid_target_rows) > 0:
    validation_errors.append(
        f"Invalid Target numeric rows: {len(invalid_target_rows)}"
    )

if len(invalid_lead_date_rows) > 0:
    validation_errors.append(
        f"Invalid Lead_Date rows: {len(invalid_lead_date_rows)}"
    )

if len(invalid_close_date_rows) > 0:
    validation_errors.append(
        f"Invalid Close_Date rows: {len(invalid_close_date_rows)}"
    )

if len(negative_deal_value_rows) > 0:
    validation_errors.append(
        f"Negative Deal_Value rows: {len(negative_deal_value_rows)}"
    )

if len(negative_target_rows) > 0:
    validation_errors.append(
        f"Negative Target rows: {len(negative_target_rows)}"
    )

if len(negative_cost_rows) > 0:
    validation_errors.append(
        f"Negative Cost rows: {len(negative_cost_rows)}"
    )

if len(invalid_cost_rows) > 0:
    validation_errors.append(
        f"Invalid Cost numeric rows: {len(invalid_cost_rows)}"
    )

missing_required_df = pd.DataFrame(missing_required_rows)

if duplicate_lead_ids > 0:
    validation_errors.append(
        f"Duplicate Lead IDs: {duplicate_lead_ids}"
    )

if missing_required_values > 0:
    validation_errors.append(
        f"Missing required values: {missing_required_values}"
    )

if len(invalid_statuses) > 0:
    validation_errors.append(
        f"invalid Lead Status rows: {len(invalid_statuses)}"
    )

if len(missing_cost) > 0:
    validation_errors.append(
        f"Won deals missing Cost: {len(missing_cost)}"
    )

if len(missing_close_date) > 0:
    validation_errors.append(
        f"Won/Lost deals missing Close_date: {len(missing_close_date)}"
    )
# Detailed validation report
duplicate_lead_rows = df[
    df["Lead_ID"].duplicated(keep=False)
][
    [
        "Lead_ID",
        "Lead_Date",
        "Customer_Name",
        "Salesperson",
        "Product_Service",
        "Lead_Status",
        "Deal_Value",
        "Close_Date",
        "Region"
    ]
]

invalid_status_row = df[
    ~df["Lead_Status"].isin(allowed_statuses)
][
    ["Lead_ID", "Customer_Name", "Salesperson", "Lead_Status"]
]

# Log validation issues that were not auto-fixed
validation_issue_log = []

for _, row in invalid_status_row.iterrows():
    validation_issue_log.append({
        "Lead_ID": row["Lead_ID"],
        "Customer_Name": row["Customer_Name"],
        "Field": "Lead_Status",
        "Original_Value": row["Lead_Status"],
        "Corrected_Value": "",
        "Action": "Blocked",
        "Reason": "Invalid or ambiguous Lead_Status"
    })

# Combine auto-fixes and blocked validation issues
audit_log = autofix_log + validation_issue_log

if audit_log:
    audit_df = pd.DataFrame(audit_log)

    audit_df.to_excel(
        audit_report_file,
        sheet_name="Audit_Log",
        index=False
    )

    print("\nAudit report created:")
    print(audit_report_file)

if not duplicate_lead_rows.empty:
    print("\n--- DUPLICATE LEAD ID DETAILS ---")
    print(duplicate_lead_rows.to_string(index=False))

if not invalid_status_row.empty:
    print("\n--- INVALID LEAD STATUS DETAILS ---")
    print(invalid_status_row.to_string(index=False))

if validation_errors:
    print("\n--- VALIDATION FAILED ---")

    for error in validation_errors:
        print("-", error)

    summary_df = pd.DataFrame({
        "Validation_Error": validation_errors
})

    with pd.ExcelWriter(
        validation_report_file,
        engine="openpyxl"
    ) as writer:

        summary_df.to_excel(
            writer,
            sheet_name="Summary",
            index=False
        )

        if not negative_deal_value_rows.empty:
            negative_deal_value_rows.to_excel(
                writer,
                sheet_name="Negative_Deal_Value",
                index=False
            )

        if not negative_target_rows.empty:
            negative_target_rows.to_excel(
                writer,
                sheet_name="Negative_Target",
                index=False
            )

        if not negative_cost_rows.empty:
            negative_cost_rows.to_excel(
                writer,
                sheet_name="Negative_cost",
                index=False
            )

        if not invalid_cost_rows.empty:
            invalid_cost_rows.to_excel(
                writer,
                sheet_name="Invalid_Cost",
                index=False
            )

        if not missing_required_df.empty:
            missing_required_df.to_excel(
                writer,
                sheet_name="Missing_Required",
                index=False
            )

        if not invalid_deal_value_rows.empty:
            invalid_deal_value_rows.to_excel(
                writer,
                sheet_name="Invalid_Deal_Value",
                index=False
            )

        if not invalid_target_rows.empty:
            invalid_target_rows.to_excel(
                writer,
                sheet_name="Invalid_Target",
                index=False
            )

        if not invalid_lead_date_rows.empty:
            invalid_lead_date_rows.to_excel(
                writer,
                sheet_name="Invalid Lead_Date",
                index=False
            )

        if not invalid_close_date_rows.empty:
            invalid_close_date_rows.to_excel(
                writer,
                sheet_name="Invalid Close_Date",
                index=False
            )
        

        if not duplicate_lead_rows.empty:
            duplicate_lead_rows.to_excel(
                writer,
                sheet_name="Duplicate_Lead_IDs",
                index=False
            )

        if not invalid_status_row.empty:
            invalid_status_row.to_excel(
                writer,
                sheet_name="Invalid_Status",
                index=False
            )

        if not missing_cost.empty:
            missing_cost[
                [
                    "Lead_ID",
                    "Customer_Name",
                    "Salesperson",
                    "Lead_Status",
                    "Deal_Value",
                    "Cost"
                ]
            ].to_excel(
                writer,
                sheet_name="Missing_Won_Cost",
                index=False
            )

        if not missing_close_date.empty:
            missing_close_date[
                [
                    "Lead_ID",
                    "Customer_Name",
                    "Salesperson",
                    "Lead_Status",
                    "Deal_Value",
                    "Close_Date"
                ]
            ].to_excel(
                writer,
                sheet_name="Missing_Close_Date",
                index=False
            )

    print("\nValidation report created:")
    print(validation_report_file)

    print(
        "\nData validation failed. "
        "Clean dataset was NOT exported."
    )

    sys.exit(1)

else:
    print("\n--- VALIDATION PASSED ---")

    #Reset row numbers after cleaning
    df = df.reset_index(drop=True)

    #Export cleaned dataset
    df.to_excel(
        output_file,
        index=False
    )

    print("\nClean dataset exported successfully!")
    print("Output file:", output_file)
import json
from pathlib import Path
import pandas as pd

#Project paths
project_dir = Path(__file__).resolve().parents[1]

config_file = project_dir / "config" / "settings.json"

with open(config_file, "r", encoding="utf-8") as file:
    config = json.load(file)

status_roles = config["status_roles"]

won_status = status_roles["won"]
lost_status = status_roles["lost"]
open_status = status_roles["open"]
pending_status = status_roles["pending"]

input_file = project_dir / config["files"]["clean_sales_data"]
output_file = project_dir / config["files"]["kpi_report"]

# Load clean data
df = pd.read_excel(input_file)

print("Clean dataset loaded successfully!")
print("Rows:", len(df))

#Basic lead counts
total_leads = len(df)

won_deals = (df["Lead_Status"] == won_status).sum()
lost_deals = (df["Lead_Status"] == lost_status).sum()
open_deals = (df["Lead_Status"] == open_status).sum()
pending_deals = (df["Lead_Status"] == pending_status).sum()

print("\n--- Lead KPIs ---")
print("Total Leads:", total_leads)
print("Won Deals:", won_deals)
print("Lost Deals", lost_deals)
print("Open Deals", open_deals)
print("Pending Deals", pending_deals)

#Filter won deals
won_df = df[df["Lead_Status"] == won_status].copy()

#Conversion metrics
lead_conversion_rate = (won_deals / total_leads) * 100

closed_deals = won_deals + lost_deals
win_rate = (won_deals / closed_deals) * 100

#Financial KPIs
total_sales = won_df["Deal_Value"].sum()
average_deal_value = won_df["Deal_Value"].mean()
total_cost = won_df["Cost"].sum()
gross_profit = total_sales - total_cost

print("\n--- Financial KPIs ---")

print(
    "Lead Conversion Rate:",
    round(lead_conversion_rate, 2),
    "%"
)

print(
    "Closed Deal Win Rate:",
    round(win_rate, 2),
    "%"
)

print("Total Sales:", total_sales)
print("Average Won Deal Value:", round(average_deal_value, 2))
print("Total Cost:", total_cost)
print("Gross profit:", gross_profit)

#Salesperson performance
salesperson_performance = (
    df.groupby("Salesperson")
    .agg(
        Total_Leads=("Lead_ID", "count"),
        Won_Deals=("Lead_Status", lambda x: (x == won_status).sum())
    )
)

#Sales revenue from won deals only
sales_by_person = (
    won_df.groupby("Salesperson")["Deal_Value"]
    .sum()
)

salesperson_performance["Total_Sales"] = sales_by_person

#Fill missing sales with 0 if someone has no won deals
salesperson_performance["Total_Sales"] = (
    salesperson_performance["Total_Sales"]
    .fillna(0)
)

#Calculate conversion rate per salespersion
salesperson_performance["Conversion_Rate"] = (
    salesperson_performance["Won_Deals"]
    / salesperson_performance["Total_Leads"]
    * 100
)

salesperson_performance["Conversion_Rate"] = (
    salesperson_performance["Conversion_Rate"].round(2)
)

print("\n--- Salesperson Performance ---")
print(salesperson_performance)

#Lead source performance
source_performance = (
    df.groupby("Lead_Source")
    .agg(
        Total_Leads=("Lead_ID", "count"),
        Won_Deals=("Lead_Status", lambda x: (x == won_status).sum())
    )
)

source_sales = (
    won_df.groupby("Lead_Source")["Deal_Value"]
    .sum()
)

source_performance["Total_Sales"] = source_sales

source_performance["Total_Sales"] = (
    source_performance["Total_Sales"]
    .fillna(0)
)

source_performance["Conversion_Rate"] = (
    source_performance["Won_Deals"]
    / source_performance["Total_Leads"]
    * 100
).round(2)

print("\n--- Lead Source Performance ---")
print(source_performance)

# Product / Service performance
product_performance = (
    df.groupby("Product_Service")
    .agg(
        Total_Leads=("Lead_ID", "count"),
        Won_Deals=("Lead_Status", lambda x: (x == won_status).sum())
    )
)

product_sales = (
    won_df.groupby("Product_Service")["Deal_Value"]
    .sum()
)
product_performance["Total_Sales"] = product_sales

product_performance["Total_Sales"] = (
    product_performance["Total_Sales"]
    .fillna(0)
)
product_performance["Conversion_Rate"] = (
    product_performance["Won_Deals"]
    / product_performance["Total_Leads"]
    * 100
).round(2)

print("\n--- Product / Service Performance ---")
print(product_performance)

# Create KPI summary table
kpi_summary = pd.DataFrame({
    "KPI": [
        "Total Leads",
        "Won Deals",
        "Lost Deals",
        "Open Deals",
        "Pending Deals",
        "Lead Conversion Rate",
        "Closed Deal Win Rate",
        "Total Sales",
        "Average Won Deal Value",
        "Total Cost",
        "Gross Profit"
    ],
    "Value": [
        total_leads,
        won_deals,
        lost_deals,
        open_deals,
        pending_deals,
        round(lead_conversion_rate, 2),
        round(win_rate, 2),
        total_sales,
        round(average_deal_value, 2),
        total_cost,
        gross_profit
    ]
})

# Export KPI tables to excel
with pd.ExcelWriter(output_file, engine="openpyxl") as writer:

    kpi_summary.to_excel(
        writer,
        sheet_name="KPI_Summary",
        index=False
    )

    salesperson_performance.reset_index().to_excel(
        writer,
        sheet_name="Salesperson_Performance",
        index=False
    )

    source_performance.reset_index().to_excel(
        writer,
        sheet_name="Lead_Source_Performance",
        index=False
    )

    product_performance.reset_index().to_excel(
        writer,
        sheet_name="Product_Performance",
        index=False
    )

print("\nKPI report created successfully!")
print("Saved to:", output_file)
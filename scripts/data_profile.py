import json
from pathlib import Path
import pandas as pd

project_dir = Path(__file__).resolve().parents[1]

config_file = project_dir / "config" / "settings.json"
with open(config_file, "r", encoding="utf-8") as file:
    config = json.load(file)

file_path = project_dir / config["files"]["raw_sales_data"]

df = pd.read_excel(file_path)

print("Dataset loaded successfully!")
print("Rows:", df.shape[0])
print("Columns", df.shape[1])

print("\n--- Lead IDs ---")
print(df[["Lead_ID", "Customer_Name"]].to_string(index=False))

print("\n--- Missing Values ---")
print(df.isna().sum())

print("\n--- Duplicate Rows ---")
print("Duplicate count:", df.duplicated().sum())

print("\n--- Repeated Lead IDs ---")
lead_counts = df["Lead_ID"].value_counts()
print(lead_counts[lead_counts > 1])

print("\n--- Rows With Missing Lead ID ---")
print(df[df["Lead_ID"].isna()].to_string(index=False))

print("\n--- Data Types ---")
print(df.dtypes)

print("\n--- Salesperson Values ---")
print(df["Salesperson"].unique())

print("\n--- Lead Status Values ---")
print(df["Lead_Status"].unique())

print("\n--- Lead Source Values ---")
print(df["Lead_Source"].unique())

print("\n--- Product Service Values ---")
print(df["Product_Service"].unique())

print("\n--- Deal Value Values")
print(df["Deal_Value"].unique())

print("\n--- Lead Date Values ---")
print(df["Lead_Date"].unique())

print("\n--- Close Date Values ---")
print(df["Close_Date"].unique())
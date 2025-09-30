#!/usr/bin/env python3
"""
Script to create sample input files for insurance data conversion
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os


def generate_sample_data(num_records=50):
    """Generate sample insurance data"""
    
    # Insurance-related data generators
    cities = ["Sydney", "Melbourne", "Brisbane", "Perth", "Adelaide", "Canberra"]
    states = ["NSW", "VIC", "QLD", "WA", "SA", "ACT"]
    construction_types = ["Brick", "Concrete", "Timber", "Steel Frame", "Mixed"]
    fire_protection = ["Sprinkler System", "Fire Alarm", "Hydrant System", "None", "Combined"]
    occupancy_types = ["Commercial", "Residential", "Industrial", "Mixed Use", "Warehouse"]
    risk_categories = ["Low", "Medium", "High", "Very High"]
    coverage_types = ["Fire", "Comprehensive", "Business Interruption", "Property Damage"]
    policy_statuses = ["Active", "Inactive", "Pending", "Cancelled"]
    
    data = []
    
    for i in range(num_records):
        # Generate random dates
        inception_date = datetime(2023, 1, 1) + timedelta(days=random.randint(0, 365))
        expiry_date = inception_date + timedelta(days=365)
        
        record = {
            "policy_number": f"POL{1000 + i:04d}",
            "inception_date": inception_date.strftime("%Y-%m-%d"),
            "expiry_date": expiry_date.strftime("%Y-%m-%d"),
            "insured_name": f"Customer {i+1} Pty Ltd",
            "premium_amount": round(random.uniform(1000, 50000), 2),
            "sum_insured": round(random.uniform(100000, 5000000), 2),
            "building_construction_type": random.choice(construction_types),
            "fire_protection_factor": random.choice(fire_protection),
            "occupancy_type": random.choice(occupancy_types),
            "building_age": random.randint(1, 100),
            "number_of_floors": random.randint(1, 20),
            "building_area_sqft": round(random.uniform(1000, 50000), 2),
            "location_city": random.choice(cities),
            "location_state": random.choice(states),
            "risk_category": random.choice(risk_categories),
            "deductible_amount": round(random.uniform(1000, 50000), 2),
            "coverage_type": random.choice(coverage_types),
            "policy_status": random.choice(policy_statuses),
            "agent_code": f"AGT{random.randint(100, 999)}",
            "underwriting_year": random.randint(2020, 2024)
        }
        
        # Make some optional fields empty for realism
        if random.random() < 0.2:  # 20% chance to be missing
            record["building_construction_type"] = ""
        if random.random() < 0.3:  # 30% chance to be missing
            record["fire_protection_factor"] = ""
        if random.random() < 0.1:  # 10% chance to be missing
            record["building_age"] = ""
        
        data.append(record)
    
    return pd.DataFrame(data)


def create_sample_files():
    """Create sample Excel and CSV input files"""
    
    # Create directories
    os.makedirs("data/input", exist_ok=True)
    os.makedirs("data/output", exist_ok=True)
    
    # Generate sample data
    df = generate_sample_data(50)
    
    # Save as Excel file
    excel_path = "data/input/sample_data.xlsx"
    df.to_excel(excel_path, index=False)
    print(f"Sample Excel file created: {excel_path}")
    
    # Save as CSV file (with some variations for testing)
    csv_path = "data/input/sample_data.csv"
    
    # Create a slightly different CSV version for testing
    csv_df = df.copy()
    # Add some variations to test flexibility
    csv_df.columns = [col.replace('_', ' ') for col in csv_df.columns]  # Use spaces instead of underscores
    
    csv_df.to_csv(csv_path, index=False)
    print(f"Sample CSV file created: {csv_path}")
    
    # Create a second CSV with different column names to test mapping flexibility
    csv2_path = "data/input/sample_data_variation.csv"
    csv2_df = df.copy()
    # Use completely different column names
    csv2_df.columns = [
        "Policy No", "Start Date", "End Date", "Client Name", "Premium", 
        "Cover Amount", "Construction", "Fire Safety", "Usage Type", 
        "Age of Building", "Floors", "Area", "City", "State", 
        "Risk Level", "Excess", "Cover Type", "Status", "Agent", "Year"
    ]
    csv2_df.to_csv(csv2_path, index=False)
    print(f"Sample CSV variation created: {csv2_path}")
    
    print(f"\nSample data summary:")
    print(f"Total records: {len(df)}")
    print(f"Columns: {list(df.columns)}")
    print(f"File sizes:")
    print(f"  - Excel: {os.path.getsize(excel_path)} bytes")
    print(f"  - CSV: {os.path.getsize(csv_path)} bytes")
    print(f"  - CSV Variation: {os.path.getsize(csv2_path)} bytes")


if __name__ == "__main__":
    create_sample_files()

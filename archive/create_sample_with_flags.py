#!/usr/bin/env python3
"""
Script to create sample input files with fire protection flag columns for testing LIST functionality
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os


def generate_sample_data_with_flags(num_records=20):
    """Generate sample insurance data with fire protection flags"""
    
    # Insurance-related data generators
    cities = ["Sydney", "Melbourne", "Brisbane", "Perth", "Adelaide"]
    states = ["NSW", "VIC", "QLD", "WA", "SA"]
    construction_types = ["Brick", "Concrete", "Timber", "Steel Frame", "Mixed"]
    occupancy_types = ["Commercial", "Residential", "Industrial", "Mixed Use", "Warehouse"]
    risk_categories = ["Low", "Medium", "High", "Very High"]
    coverage_types = ["Fire", "Comprehensive", "Business Interruption", "Property Damage"]
    policy_statuses = ["Active", "Inactive", "Pending", "Cancelled"]
    
    data = []
    
    for i in range(num_records):
        # Generate random dates
        inception_date = datetime(2023, 1, 1) + timedelta(days=random.randint(0, 365))
        expiry_date = inception_date + timedelta(days=365)
        
        # Generate fire protection flags (1 or 0)
        smoke_alarm = random.choice([0, 1])
        fire_extinguisher = random.choice([0, 1])
        fire_blanket = random.choice([0, 1])
        sprinkler_system = random.choice([0, 1])
        fire_hydrant = random.choice([0, 1])
        
        record = {
            "policy_number": f"POL{2000 + i:04d}",
            "inception_date": inception_date.strftime("%Y-%m-%d"),
            "expiry_date": expiry_date.strftime("%Y-%m-%d"),
            "insured_name": f"Customer {i+1} Pty Ltd",
            "premium_amount": round(random.uniform(1000, 50000), 2),
            "sum_insured": round(random.uniform(100000, 5000000), 2),
            
            # Fire protection flags
            "smoke_alarm": smoke_alarm,
            "fire_extinguisher": fire_extinguisher,
            "fire_blanket": fire_blanket,
            "sprinkler_system": sprinkler_system,
            "fire_hydrant": fire_hydrant,
            
            "building_construction_type": random.choice(construction_types),
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
        
        data.append(record)
    
    return pd.DataFrame(data)


def create_sample_files_with_flags():
    """Create sample Excel and CSV input files with fire protection flags"""
    
    # Create directories
    os.makedirs("data/input", exist_ok=True)
    os.makedirs("data/output", exist_ok=True)
    
    # Generate sample data with flags
    df = generate_sample_data_with_flags(20)
    
    # Save as Excel file
    excel_path = "data/input/sample_data_with_flags.xlsx"
    df.to_excel(excel_path, index=False)
    print(f"Sample Excel file with flags created: {excel_path}")
    
    # Save as CSV file
    csv_path = "data/input/sample_data_with_flags.csv"
    df.to_csv(csv_path, index=False)
    print(f"Sample CSV file with flags created: {csv_path}")
    
    print(f"\nSample data with flags summary:")
    print(f"Total records: {len(df)}")
    print(f"Columns: {list(df.columns)}")
    print(f"Fire protection flag columns:")
    print(f"  - smoke_alarm: {df['smoke_alarm'].sum()} records with flag=1")
    print(f"  - fire_extinguisher: {df['fire_extinguisher'].sum()} records with flag=1")
    print(f"  - fire_blanket: {df['fire_blanket'].sum()} records with flag=1")
    print(f"  - sprinkler_system: {df['sprinkler_system'].sum()} records with flag=1")
    print(f"  - fire_hydrant: {df['fire_hydrant'].sum()} records with flag=1")


if __name__ == "__main__":
    create_sample_files_with_flags()

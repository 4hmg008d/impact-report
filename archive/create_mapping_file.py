#!/usr/bin/env python3
"""
Script to create the column mapping Excel file for insurance data conversion
"""

import pandas as pd


def create_mapping_file():
    """Create the column mapping Excel file"""
    
    # Define the mapping data for insurance company data
    mapping_data = [
        # Original Column, New Column, Data Type, Optional
        ["policy_number", "POLICY_NUMBER", "TEXT", "NO"],
        ["inception_date", "INCEPTION_DATE", "TEXT", "NO"],
        ["expiry_date", "EXPIRY_DATE", "TEXT", "NO"],
        ["insured_name", "INSURED_NAME", "TEXT", "NO"],
        ["premium_amount", "PREMIUM_AMOUNT", "BIGDEC", "NO"],
        ["sum_insured", "SUM_INSURED", "BIGDEC", "NO"],
        ["building_construction_type", "BUILDING_CONSTRUCTION_TYPE", "TEXT", "YES"],
        ["fire_protection_factor", "FIRE_PROTECTION_FACTOR", "TEXT", "YES"],
        ["occupancy_type", "OCCUPANCY_TYPE", "TEXT", "YES"],
        ["building_age", "BUILDING_AGE", "INTEGER", "YES"],
        ["number_of_floors", "NUMBER_OF_FLOORS", "INTEGER", "YES"],
        ["building_area_sqft", "BUILDING_AREA_SQFT", "BIGDEC", "YES"],
        ["location_city", "LOCATION_CITY", "TEXT", "YES"],
        ["location_state", "LOCATION_STATE", "TEXT", "YES"],
        ["risk_category", "RISK_CATEGORY", "TEXT", "YES"],
        ["deductible_amount", "DEDUCTIBLE_AMOUNT", "BIGDEC", "YES"],
        ["coverage_type", "COVERAGE_TYPE", "TEXT", "YES"],
        ["policy_status", "POLICY_STATUS", "TEXT", "YES"],
        ["agent_code", "AGENT_CODE", "TEXT", "YES"],
        ["underwriting_year", "UNDERWRITING_YEAR", "INTEGER", "YES"]
    ]
    
    # Create DataFrame
    df = pd.DataFrame(mapping_data, columns=[
        "Original Column", 
        "New Column", 
        "Data Type", 
        "Optional"
    ])
    
    # Create directory if it doesn't exist
    import os
    os.makedirs("mapping", exist_ok=True)
    
    # Save to Excel file
    output_path = "mapping/column_mapping.xlsx"
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name="column mapping", index=False)
        
        # Auto-adjust column widths
        worksheet = writer.sheets["column mapping"]
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            worksheet.column_dimensions[column_letter].width = adjusted_width
    
    print(f"Mapping file created successfully: {output_path}")
    print(f"Total mappings: {len(mapping_data)}")
    print("\nMapping Summary:")
    print(f"Required columns: {len([m for m in mapping_data if m[3] == 'NO'])}")
    print(f"Optional columns: {len([m for m in mapping_data if m[3] == 'YES'])}")


if __name__ == "__main__":
    create_mapping_file()

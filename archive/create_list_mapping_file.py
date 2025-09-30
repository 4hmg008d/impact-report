#!/usr/bin/env python3
"""
Script to create a mapping file that demonstrates LIST data type functionality
for fire protection factors
"""

import pandas as pd


def create_list_mapping_file():
    """Create mapping file with LIST data type example"""
    
    # Define the mapping data including LIST type for fire protection factors
    mapping_data = [
        # Original Column, New Column, Data Type, Optional
        ["policy_number", "POLICY_NUMBER", "TEXT", "NO"],
        ["inception_date", "INCEPTION_DATE", "TEXT", "NO"],
        ["expiry_date", "EXPIRY_DATE", "TEXT", "NO"],
        ["insured_name", "INSURED_NAME", "TEXT", "NO"],
        ["premium_amount", "PREMIUM_AMOUNT", "BIGDEC", "NO"],
        ["sum_insured", "SUM_INSURED", "BIGDEC", "NO"],
        
        # Fire protection factors - multiple columns mapping to same LIST column
        ["smoke_alarm", "FIRE_PROTECTION", "LIST", "YES"],
        ["fire_extinguisher", "FIRE_PROTECTION", "LIST", "YES"],
        ["fire_blanket", "FIRE_PROTECTION", "LIST", "YES"],
        ["sprinkler_system", "FIRE_PROTECTION", "LIST", "YES"],
        ["fire_hydrant", "FIRE_PROTECTION", "LIST", "YES"],
        
        ["building_construction_type", "BUILDING_CONSTRUCTION_TYPE", "TEXT", "YES"],
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
    output_path = "mapping/column_mapping_list.xlsx"
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
    
    print(f"LIST mapping file created successfully: {output_path}")
    print(f"Total mappings: {len(mapping_data)}")
    print("\nLIST Feature Demonstration:")
    print("Multiple fire protection flag columns will be combined into FIRE_PROTECTION list:")
    print("- smoke_alarm, fire_extinguisher, fire_blanket, sprinkler_system, fire_hydrant")
    print("→ All map to FIRE_PROTECTION with data type LIST")


if __name__ == "__main__":
    create_list_mapping_file()

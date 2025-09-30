"""
Mapping processor module for data conversion tool using Pandas
"""

import pandas as pd
import os
from typing import Dict, List, Any


class MappingProcessor:
    """Processes column mapping rules using Pandas"""
    
    def __init__(self, config_loader):
        self.config_loader = config_loader
    
    def load_mapping_rules(self) -> pd.DataFrame:
        """Load mapping rules from Excel file"""
        mapping_config = self.config_loader.get_mapping_config()
        mapping_file_path = mapping_config.get('file_path')
        sheet_name = mapping_config.get('sheet_name', 'column mapping')
        
        if not mapping_file_path:
            raise ValueError("Mapping file path not specified in configuration")
        
        if not os.path.exists(mapping_file_path):
            raise FileNotFoundError(f"Mapping file not found: {mapping_file_path}")
        
        try:
            mapping_df = pd.read_excel(mapping_file_path, sheet_name=sheet_name)
            print(f"Loaded {len(mapping_df)} mapping rules from {sheet_name}")
            return mapping_df
        except Exception as e:
            raise ValueError(f"Failed to load mapping file: {e}")
    
    def validate_mapping_rules(self, mapping_df: pd.DataFrame) -> bool:
        """Validate mapping rules structure"""
        required_columns = ['Original Column', 'New Column', 'Data Type', 'List', 'Required']
        missing_columns = [col for col in required_columns if col not in mapping_df.columns]
        
        if missing_columns:
            raise ValueError(f"Mapping file missing required columns: {missing_columns}")
        
        # Validate data types
        valid_data_types = ['CODE', 'INTEGE', 'DECIMA', 'DATE']
        invalid_types = mapping_df[~mapping_df['Data Type'].str.upper().isin(valid_data_types)]
        
        if len(invalid_types) > 0:
            invalid_list = invalid_types['Data Type'].unique().tolist()
            raise ValueError(f"Invalid data types found: {invalid_list}. Valid types: {valid_data_types}")
        
        # Validate List column values
        valid_list_values = ['Y', 'N']
        invalid_list = mapping_df[~mapping_df['List'].astype(str).str.upper().isin(valid_list_values)]
        
        if len(invalid_list) > 0:
            invalid_list_values = invalid_list['List'].unique().tolist()
            raise ValueError(f"Invalid List values found: {invalid_list_values}. Valid values: {valid_list_values}")
        
        # Validate Required column values
        valid_required_values = ['YES', 'NO', 'Y', 'N']
        invalid_required = mapping_df[~mapping_df['Required'].astype(str).str.upper().isin(valid_required_values)]
        
        if len(invalid_required) > 0:
            invalid_required_values = invalid_required['Required'].unique().tolist()
            raise ValueError(f"Invalid Required values found: {invalid_required_values}. Valid values: {valid_required_values}")
        
        return True
    
    def get_column_mapping(self, mapping_df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
        """Create column mapping dictionary"""
        mapping_dict = {}
        
        for _, row in mapping_df.iterrows():
            mapping_dict[str(row['Original Column']).strip()] = {
                'new_column': str(row['New Column']).strip().upper(),  # Ensure uppercase
                'data_type': str(row['Data Type']).strip().upper(),    # Ensure uppercase
                'list_flag': str(row['List']).strip().upper() == 'Y',  # Convert to boolean
                'optional': str(row['Required']).strip().upper() in ['NO', 'FALSE', '0', 'N']  # Negate Required logic
            }
        
        return mapping_dict
    
    def get_required_columns(self, mapping_df: pd.DataFrame) -> List[str]:
        """Get list of required columns (Required = YES)"""
        required_df = mapping_df[
            mapping_df['Required'].astype(str).str.upper().isin(['YES', 'TRUE', '1', 'Y'])
        ]
        required_columns = required_df['Original Column'].astype(str).str.strip().tolist()
        
        return required_columns
    
    def load_value_mappings(self, mapping_file_path: str) -> Dict[str, Dict[str, str]]:
        """Load individual value mappings from separate tabs"""
        value_mappings = {}
        
        try:
            # Get all sheet names in the mapping file
            excel_file = pd.ExcelFile(mapping_file_path)
            sheet_names = excel_file.sheet_names
            
            # Skip the main mapping sheet
            main_sheet = self.config_loader.get_mapping_config().get('sheet_name', 'column mapping')
            value_sheets = [sheet for sheet in sheet_names if sheet != main_sheet]
            
            for sheet_name in value_sheets:
                try:
                    # Load the value mapping sheet
                    value_df = pd.read_excel(mapping_file_path, sheet_name=sheet_name)
                    
                    # Validate the value mapping structure
                    if 'From' in value_df.columns and 'To' in value_df.columns:
                        # Create a mapping dictionary for this column
                        value_mapping = {}
                        for _, row in value_df.iterrows():
                            from_value = str(row['From']).strip()
                            to_value = str(row['To']).strip()
                            value_mapping[from_value] = to_value
                        
                        value_mappings[sheet_name] = value_mapping
                        print(f"Loaded value mapping for '{sheet_name}': {len(value_mapping)} mappings")
                    else:
                        print(f"Warning: Value mapping sheet '{sheet_name}' missing 'From' or 'To' columns")
                        
                except Exception as e:
                    print(f"Warning: Failed to load value mapping from sheet '{sheet_name}': {e}")
        
        except Exception as e:
            print(f"Warning: Failed to load value mappings: {e}")
        
        return value_mappings
    
    def process_mapping(self) -> Dict[str, Any]:
        """Process and validate mapping rules"""
        mapping_df = self.load_mapping_rules()
        self.validate_mapping_rules(mapping_df)
        
        column_mapping = self.get_column_mapping(mapping_df)
        required_columns = self.get_required_columns(mapping_df)
        
        # Load individual value mappings
        mapping_config = self.config_loader.get_mapping_config()
        mapping_file_path = mapping_config.get('file_path')
        value_mappings = self.load_value_mappings(mapping_file_path)
        
        return {
            'mapping_df': mapping_df,
            'column_mapping': column_mapping,
            'required_columns': required_columns,
            'value_mappings': value_mappings
        }

"""
Data loader module for data conversion tool using Pandas
"""

import pandas as pd
import os
from typing import Dict, Any


class DataLoader:
    """Loads and validates input data using Pandas"""
    
    def __init__(self, config_loader):
        self.config_loader = config_loader
    
    def _detect_file_type(self, file_path: str) -> str:
        """Detect file type from extension"""
        ext = os.path.splitext(file_path)[1].lower()
        if ext in ['.xlsx', '.xls']:
            return 'excel'
        elif ext == '.csv':
            return 'csv'
        else:
            raise ValueError(f"Unsupported file type: {ext}")
    
    def load_input_data(self, file_path: str, file_type: str = 'auto') -> pd.DataFrame:
        """Load input data from file"""
        if file_type == 'auto':
            file_type = self._detect_file_type(file_path)
        
        try:
            if file_type == 'excel':
                df = pd.read_excel(file_path)
            elif file_type == 'csv':
                df = pd.read_csv(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
            
            print(f"Successfully loaded data from {file_path}")
            return df
            
        except Exception as e:
            raise ValueError(f"Failed to load input file {file_path}: {e}")
    
    def _find_matching_column(self, target_col: str, actual_columns: set) -> str:
        """Find matching column name with case-insensitive and space/underscore variations"""
        if target_col in actual_columns:
            return target_col
        
        # Try to find a matching column (case-insensitive, space/underscore variations)
        for actual_col in actual_columns:
            normalized_target = target_col.lower().replace('_', ' ').strip()
            normalized_actual = actual_col.lower().replace('_', ' ').strip()
            if normalized_target == normalized_actual:
                return actual_col
        return None
    
    def validate_input_data(self, df: pd.DataFrame, column_mapping: Dict[str, Dict[str, Any]]) -> None:
        """Validate input data against mapping requirements"""
        missing_columns = []
        actual_columns = set(df.columns)
        
        # Group mappings by new column to handle LIST type validation
        grouped_mappings = {}
        for original_col, mapping_info in column_mapping.items():
            new_col = mapping_info['new_column']
            if new_col not in grouped_mappings:
                grouped_mappings[new_col] = []
            grouped_mappings[new_col].append((original_col, mapping_info))
        
        # Validate required columns
        for new_col, mappings in grouped_mappings.items():
            # For LIST type, we need at least one of the source columns
            if len(mappings) > 1:
                # This is a LIST type mapping - check if we have at least one source column
                found_any = False
                for original_col, mapping_info in mappings:
                    if not mapping_info['optional']:
                        if self._find_matching_column(original_col, actual_columns) is not None:
                            found_any = True
                            break
                
                if not found_any and any(not m[1]['optional'] for m in mappings):
                    missing_columns.extend([m[0] for m in mappings if not m[1]['optional']])
            else:
                # Single column mapping - validate normally
                original_col, mapping_info = mappings[0]
                if not mapping_info['optional']:
                    if self._find_matching_column(original_col, actual_columns) is None:
                        missing_columns.append(original_col)
        
        if missing_columns:
            raise ValueError(f"Input data missing required columns: {missing_columns}")
        
        print("Input data validation passed")

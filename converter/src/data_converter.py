"""
Data converter module for data conversion tool using Pandas
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any


class DataConverter:
    """Converts data types and handles LIST type processing using Pandas"""
    
    def __init__(self, config_loader):
        self.config_loader = config_loader
    
    def _validate_code(self, value: str) -> str:
        """Validate CODE type: all capital letters, max 12 chars including spaces"""
        if pd.isna(value):
            return value
        
        value_str = str(value).strip()
        
        # Check if all characters are uppercase letters, numbers, or spaces
        if not all(c.isupper() or c.isdigit() or c.isspace() for c in value_str):
            raise ValueError(f"CODE value must be all uppercase letters and numbers: '{value_str}'")
        
        # Check length
        if len(value_str) > 12:
            raise ValueError(f"CODE value exceeds 12 characters: '{value_str}' ({len(value_str)} chars)")
        
        return value_str
    
    def _validate_intege(self, value) -> int:
        """Validate INTEGE type: max 12 digits, raise error if longer"""
        if pd.isna(value):
            return value
        
        # Convert to integer
        try:
            int_value = int(float(value))
        except (ValueError, TypeError):
            raise ValueError(f"INTEGE value must be a valid number: '{value}'")
        
        # Check digit length
        digit_length = len(str(abs(int_value)))
        if digit_length > 12:
            raise ValueError(f"INTEGE value exceeds 12 digits: '{int_value}' ({digit_length} digits)")
        
        return int_value
    
    def _validate_decima(self, value) -> float:
        """Validate DECIMA type: max 12 total digits, max 4 decimal places"""
        if pd.isna(value):
            return value
        
        # Convert to float
        try:
            float_value = float(value)
        except (ValueError, TypeError):
            raise ValueError(f"DECIMA value must be a valid number: '{value}'")
        
        # Round to 4 decimal places
        float_value = round(float_value, 4)
        
        # Check total digit length (excluding decimal point and negative sign)
        str_value = str(float_value).replace('-', '').replace('.', '')
        if len(str_value) > 12:
            raise ValueError(f"DECIMA value exceeds 12 total digits: '{float_value}' ({len(str_value)} digits)")
        
        return float_value
    
    def _convert_date(self, value) -> str:
        """Convert DATE type: convert to 'dd/mm/yyyy' format"""
        if pd.isna(value):
            return value
        
        # If value is already a string in date format, try to parse it
        if isinstance(value, str):
            try:
                # Try to parse various date formats
                if '/' in value:
                    # Already in date format, try to standardize
                    parts = value.split('/')
                    if len(parts) == 3:
                        day, month, year = parts
                        # Ensure proper formatting
                        day = day.zfill(2)
                        month = month.zfill(2)
                        year = year.zfill(4)
                        return f"{day}/{month}/{year}"
                # Try pandas date parsing
                parsed_date = pd.to_datetime(value, errors='coerce')
                if not pd.isna(parsed_date):
                    return parsed_date.strftime('%d/%m/%Y')
            except:
                pass
        
        # If value is numeric (Excel date serial number)
        try:
            # Excel uses 1900-01-01 as day 1 (with some exceptions)
            excel_origin = pd.Timestamp('1899-12-30')
            date_value = excel_origin + pd.Timedelta(days=float(value))
            return date_value.strftime('%d/%m/%Y')
        except (ValueError, TypeError):
            raise ValueError(f"DATE value cannot be converted: '{value}'")
        
        raise ValueError(f"DATE value cannot be converted: '{value}'")
    
    def _convert_flags_to_list(self, flag_columns: List[pd.Series], column_names: List[str], list_format: str, data_type: str) -> pd.Series:
        """Convert multiple flag columns (1/0) into a list of 0 and 1 values"""
        result = []
        
        for i in range(len(flag_columns[0])):
            active_items = []
            for j, col_series in enumerate(flag_columns):
                # Get the actual flag value (0 or 1)
                flag_value = col_series.iloc[i] if i < len(col_series) else 0
                if pd.notna(flag_value):
                    # Convert to the appropriate data type
                    try:
                        if data_type == 'CODE':
                            # For CODE type, just use the flag value (0 or 1) as string
                            validated_value = str(int(flag_value))
                        elif data_type == 'INTEGE':
                            validated_value = int(flag_value)
                        elif data_type == 'DECIMA':
                            validated_value = float(flag_value)
                        elif data_type == 'DATE':
                            validated_value = self._convert_date(flag_value)
                        else:
                            validated_value = flag_value
                        
                        active_items.append(validated_value)
                    except Exception as e:
                        # Skip invalid values
                        print(f"Warning: Value '{flag_value}' failed validation for data type {data_type}: {e}")
            
            # Convert list to appropriate format
            if list_format == "list_in_single_string":
                if active_items:
                    result.append(";".join(str(item) for item in active_items))
                else:
                    result.append("")
            else:  # list_in_multiple_rows
                if active_items:
                    result.append(str(active_items))
                else:
                    result.append("")
        
        return pd.Series(result)
    
    def _explode_list_column(self, df: pd.DataFrame, list_column: str, id_col: str) -> pd.DataFrame:
        """Explode a list column into separate rows, keeping first row with all values, others with NA"""
        exploded_rows = []
        
        for idx, row in df.iterrows():
            policy_number = row[id_col]
            list_value = row[list_column]
            
            # Parse the list string back to actual list
            if isinstance(list_value, str) and list_value.startswith('[') and list_value.endswith(']'):
                try:
                    # Simple parsing for the list format we created
                    items = list_value.strip('[]').replace("'", "").split(', ')
                    items = [item.strip() for item in items if item.strip()]
                except:
                    items = []
            else:
                items = []
            
            if items:
                # First row: keep all original values with the first list item
                first_row = row.copy()
                first_row[list_column] = items[0]
                exploded_rows.append(first_row)
                
                # Additional rows: keep only policy number and list item, set others to NA
                for item in items[1:]:
                    new_row = row.copy()
                    # Set all columns to NA except policy number and the list item
                    for col in new_row.index:
                        if col != id_col and col != list_column:
                            new_row[col] = np.nan
                    # Set the list column to the individual item
                    new_row[list_column] = item
                    exploded_rows.append(new_row)
            else:
                # If no items, keep the original row unchanged
                exploded_rows.append(row.copy())
        
        return pd.DataFrame(exploded_rows)
    
    def _apply_value_mapping(self, col_data: pd.Series, column_name: str, value_mappings: Dict[str, Dict[str, str]]) -> pd.Series:
        """Apply individual value mappings to a column if available"""
        if column_name in value_mappings:
            value_mapping = value_mappings[column_name]
            return col_data.apply(lambda x: value_mapping.get(str(x).strip(), x) if pd.notna(x) else x)
        return col_data
    
    def convert_data_types(self, df: pd.DataFrame, column_mapping: Dict[str, Dict[str, Any]], value_mappings: Dict[str, Dict[str, str]] = None) -> pd.DataFrame:
        """Convert data types according to mapping specifications"""
        converted_df = pd.DataFrame()
        actual_columns = set(df.columns)
        
        # Group mappings by new column name to handle list columns
        grouped_mappings = {}
        for original_col, mapping_info in column_mapping.items():
            new_col = mapping_info['new_column']
            if new_col not in grouped_mappings:
                grouped_mappings[new_col] = []
            grouped_mappings[new_col].append((original_col, mapping_info))
        
        for new_col, mappings in grouped_mappings.items():
            # Check if this is a list column (multiple mappings or list_flag=True)
            is_list_column = len(mappings) > 1 or any(m[1]['list_flag'] for m in mappings)
            
            if not is_list_column:
                # Single column mapping - process normally
                original_col, mapping_info = mappings[0]
                data_type = mapping_info['data_type']
                
                # Find the actual column name that matches the mapping
                actual_col_name = self._find_matching_column(original_col, actual_columns)
                
                # Skip optional columns that don't exist in input
                if actual_col_name is None and mapping_info['optional']:
                    print(f"Warning: Optional column '{original_col}' not found in input data")
                    continue
                elif actual_col_name is None and not mapping_info['optional']:
                    raise ValueError(f"Required column '{original_col}' not found in input data")
                
                # Get the column data
                if actual_col_name is not None:
                    col_data = df[actual_col_name]
                else:
                    col_data = pd.Series([np.nan] * len(df))
                
                # Convert data type with validation (skip validation for optional columns)
                try:
                    if mapping_info['optional']:
                        # For optional columns, just convert without validation
                        if data_type == 'CODE':
                            converted_data = col_data.astype(str).replace('nan', np.nan)
                        elif data_type == 'INTEGE':
                            converted_data = pd.to_numeric(col_data, errors='coerce').astype('Int64')
                        elif data_type == 'DECIMA':
                            converted_data = pd.to_numeric(col_data, errors='coerce').astype('float64')
                        elif data_type == 'DATE':
                            converted_data = col_data.apply(lambda x: self._convert_date(x) if pd.notna(x) else x)
                        else:
                            raise ValueError(f"Unknown data type: {data_type}")
                    else:
                        # For required columns, apply full validation
                        if data_type == 'CODE':
                            # Apply value mapping first if available
                            if value_mappings:
                                col_data = self._apply_value_mapping(col_data, original_col, value_mappings)
                            # Apply CODE validation to each value
                            converted_data = col_data.apply(lambda x: self._validate_code(x) if pd.notna(x) else x)
                        elif data_type == 'INTEGE':
                            # Apply value mapping first if available
                            if value_mappings:
                                col_data = self._apply_value_mapping(col_data, original_col, value_mappings)
                            # Apply INTEGE validation to each value
                            converted_data = col_data.apply(lambda x: self._validate_intege(x) if pd.notna(x) else x)
                        elif data_type == 'DECIMA':
                            # Apply value mapping first if available
                            if value_mappings:
                                col_data = self._apply_value_mapping(col_data, original_col, value_mappings)
                            # Apply DECIMA validation to each value
                            converted_data = col_data.apply(lambda x: self._validate_decima(x) if pd.notna(x) else x)
                        elif data_type == 'DATE':
                            # Apply value mapping first if available
                            if value_mappings:
                                col_data = self._apply_value_mapping(col_data, original_col, value_mappings)
                            # Apply DATE conversion to each value
                            converted_data = col_data.apply(lambda x: self._convert_date(x) if pd.notna(x) else x)
                        else:
                            raise ValueError(f"Unknown data type: {data_type}")
                    
                    converted_df[new_col] = converted_data
                    
                except Exception as e:
                    raise ValueError(f"Failed to convert column '{original_col}' to {data_type}: {e}")
            
            else:
                # List column - handle multiple source columns
                print(f"Processing list column for {new_col} with {len(mappings)} source columns")
                
                # Collect all matching columns
                flag_columns = []
                column_names = []
                
                for original_col, mapping_info in mappings:
                    data_type = mapping_info['data_type']
                    
                    # Find the actual column name that matches the mapping
                    actual_col_name = self._find_matching_column(original_col, actual_columns)
                    
                    if actual_col_name is not None:
                        flag_columns.append(df[actual_col_name])
                        column_names.append(original_col)
                    elif not mapping_info['optional']:
                        raise ValueError(f"Required column '{original_col}' not found in input data")
                
                if flag_columns:
                    # Convert multiple flag columns to list
                    try:
                        list_format = self.config_loader.get_processing_config().get('list_format', 'list_in_multiple_rows')
                        # Get the data type from the first mapping (all should be the same for list columns)
                        data_type = mappings[0][1]['data_type']
                        converted_data = self._convert_flags_to_list(flag_columns, column_names, list_format, data_type)
                        converted_df[new_col] = converted_data
                    except Exception as e:
                        raise ValueError(f"Failed to convert columns to list for {new_col}: {e}")
                else:
                    # No matching columns found, but all were optional
                    list_format = self.config_loader.get_processing_config().get('list_format', 'list_in_multiple_rows')
                    converted_df[new_col] = pd.Series([""] * len(df))
        
        return converted_df
    
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
    
    def _find_list_columns(self, column_mapping: Dict[str, Dict[str, Any]]) -> List[str]:
        """Find columns that are list type in the mapping using list_flag"""
        list_columns = set()
        for mapping_info in column_mapping.values():
            if mapping_info.get('list_flag', False):
                list_columns.add(mapping_info['new_column'])
        return list(list_columns)
    
    
    def _explode_multiple_list_columns(self, df: pd.DataFrame, list_columns: List[str], id_col: str) -> pd.DataFrame:
        """Explode multiple list columns simultaneously, matching the longest list length"""
        exploded_rows = []
        
        for idx, row in df.iterrows():
            policy_number = row[id_col]
            
            # Parse all list columns to get their items
            list_items = {}
            max_length = 0
            
            for list_col in list_columns:
                list_value = row[list_col]
                items = []
                
                # Parse the list string back to actual list
                if isinstance(list_value, str) and list_value.startswith('[') and list_value.endswith(']'):
                    try:
                        # Simple parsing for the list format we created
                        items = list_value.strip('[]').replace("'", "").split(', ')
                        items = [item.strip() for item in items if item.strip()]
                    except:
                        items = []
                elif isinstance(list_value, str) and ';' in list_value:
                    # Handle list_in_single_string format
                    items = [item.strip() for item in list_value.split(';') if item.strip()]
                else:
                    items = []
                
                list_items[list_col] = items
                max_length = max(max_length, len(items))
            
            # If no lists have items, keep the original row
            if max_length == 0:
                exploded_rows.append(row.copy())
                continue
            
            # Create rows for each position in the lists
            for i in range(max_length):
                new_row = row.copy()
                
                # For each list column, set the value at position i
                for list_col in list_columns:
                    items = list_items[list_col]
                    if i < len(items):
                        new_row[list_col] = items[i]
                    else:
                        # If this list is shorter than the longest, set to empty
                        new_row[list_col] = ""
                
                # For the first row, keep all original values
                if i > 0:
                    # For additional rows, set non-list columns to NA except policy number
                    for col in new_row.index:
                        if col != id_col and col not in list_columns:
                            new_row[col] = np.nan
                
                exploded_rows.append(new_row)
        
        return pd.DataFrame(exploded_rows)
    
    def process_list_columns(self, df: pd.DataFrame, column_mapping: Dict[str, Dict[str, Any]]) -> pd.DataFrame:
        """Process LIST columns according to the configured format"""
        list_format = self.config_loader.get_processing_config().get('list_format', 'list_in_multiple_rows')
        
        if list_format == "list_in_multiple_rows":
            list_columns = self._find_list_columns(column_mapping)
            # Use the first column in column_mapping as the ID column
            id_col = list(column_mapping.values())[0]['new_column']
            
            if list_columns:
                print(f"Found LIST columns to explode: {list_columns}")
                print(f"Using ID column for fill down: {id_col}")
                
                if len(list_columns) > 1:
                    # Explode multiple list columns simultaneously
                    print(f"Exploding {len(list_columns)} list columns simultaneously")
                    df = self._explode_multiple_list_columns(df, list_columns, id_col)
                    print(f"After simultaneous explosion: {len(df)} rows")
                else:
                    # Single list column - use original method
                    list_col = list_columns[0]
                    if list_col in df.columns:
                        print(f"Exploding LIST column: {list_col}")
                        df = self._explode_list_column(df, list_col, id_col)
                        print(f"After explosion: {len(df)} rows")
        else:
            print(f"Using list format: {list_format} - no explosion needed")
        
        return df

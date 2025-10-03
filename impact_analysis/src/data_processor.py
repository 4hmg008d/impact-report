"""
Data processing module for impact analysis tool using Pandas
"""

import pandas as pd
from typing import Dict, List, Tuple
import os


class DataProcessor:
    """Processes benchmark and target data using Pandas"""
    
    def __init__(self, config_loader):
        self.config_loader = config_loader
    
    def load_and_deduplicate_file(self, file_path: str, id_column: str) -> pd.DataFrame:
        """Load file and keep only first row for each ID value using Pandas"""
        try:
            df = pd.read_excel(file_path)
            print(f"Loaded {len(df)} rows from {file_path}")
            
            # Keep only first row for each ID value using Pandas
            df_deduped = df.drop_duplicates(subset=[id_column], keep='first')
            print(f"After deduplication: {len(df_deduped)} rows")
            
            return df_deduped
        except Exception as e:
            raise ValueError(f"Failed to load file {file_path}: {e}")
    
    def process_data(self) -> Tuple[pd.DataFrame, Dict[str, Dict]]:
        """Execute the complete data processing pipeline with new step-based approach"""
        # Load mapping data
        mapping_df = self.config_loader.load_mapping_data()
        if len(mapping_df) == 0:
            raise ValueError("No mapping data found")
        
        print("Mapping data loaded:")
        print(mapping_df[['Item', 'Step', 'StepName', 'File', 'Column']].head(10))
        
        # Get ID column and unique files
        id_column = mapping_df.iloc[0]['ID']
        print(f"ID Column: {id_column}")
        
        # Clean up file paths and load all files
        file_data = {}
        unique_files = set()
        for _, row in mapping_df.iterrows():
            file_path = row['File']
            # Clean up file path - remove impact_analysis/ prefix if it exists
            if file_path.startswith('impact_analysis/'):
                file_path = file_path[len('impact_analysis/'):]
            unique_files.add(file_path)
        
        # Load and deduplicate all files
        for file_path in unique_files:
            resolved_path = self.config_loader._resolve_path(file_path)
            file_data[file_path] = self.load_and_deduplicate_file(resolved_path, id_column)
        
        # Step 1: Start with the first file as base and merge only specified columns with new naming
        # Group by Item and Step to understand the structure
        items = mapping_df['Item'].unique()
        
        # Build the merged dataframe with renamed columns
        merged_df = None
        comparison_data = {}
        
        for item in items:
            item_mapping = mapping_df[mapping_df['Item'] == item].sort_values('Step')
            comparison_data[item] = {
                'steps': {},
                'step_names': {},
                'columns': {}
            }
            
            for _, row in item_mapping.iterrows():
                step = row['Step']
                step_name = row['StepName']
                file_path = row['File']
                column = row['Column']
                
                # Clean up file path
                if file_path.startswith('impact_analysis/'):
                    file_path = file_path[len('impact_analysis/'):]
                
                # Create new column name: {Column}_{Item}_{Step}
                new_col_name = f"{column}_{item}_{step}"
                
                # Store step information
                comparison_data[item]['steps'][step] = {
                    'file_path': file_path,
                    'original_column': column,
                    'renamed_column': new_col_name,
                    'step_name': step_name
                }
                comparison_data[item]['step_names'][step] = step_name
                comparison_data[item]['columns'][step] = new_col_name
        
        # Start with the first step of the first item to establish the base dataframe
        first_item = items[0]
        first_step_info = comparison_data[first_item]['steps'][1]
        first_file = first_step_info['file_path']
        
        # Start with ALL columns from the first file (not just ID column)
        merged_df = file_data[first_file].copy()
        print(f"Starting with all columns from first file: {first_file}")
        print(f"Base columns: {list(merged_df.columns)}")
        
        # Get list of columns that will be used for comparison (to rename them)
        comparison_columns = set()
        for item in items:
            for step in comparison_data[item]['steps'].keys():
                step_info = comparison_data[item]['steps'][step]
                if step_info['file_path'] == first_file:
                    comparison_columns.add(step_info['original_column'])
        
        # Rename comparison columns in the base dataframe
        first_file_rename_map = {}
        for item in items:
            for step in sorted(comparison_data[item]['steps'].keys()):
                step_info = comparison_data[item]['steps'][step]
                if step_info['file_path'] == first_file:
                    orig_col = step_info['original_column']
                    new_col = step_info['renamed_column']
                    first_file_rename_map[orig_col] = new_col
        
        if first_file_rename_map:
            merged_df.rename(columns=first_file_rename_map, inplace=True)
            print(f"Renamed columns in base file: {first_file_rename_map}")
        
        # Add comparison columns from other files
        for item in items:
            for step in sorted(comparison_data[item]['steps'].keys()):
                step_info = comparison_data[item]['steps'][step]
                file_path = step_info['file_path']
                orig_col = step_info['original_column']
                new_col = step_info['renamed_column']
                
                # Skip if this column is already in merged_df (from first file)
                if new_col in merged_df.columns:
                    continue
                
                if orig_col in file_data[file_path].columns:
                    # Merge this specific column
                    temp_df = file_data[file_path][[id_column, orig_col]].copy()
                    temp_df = temp_df.rename(columns={orig_col: new_col})
                    merged_df = merged_df.merge(temp_df, on=id_column, how='outer')
                    print(f"Added column {new_col} from {file_path}")
        
        print(f"Merged data: {len(merged_df)} rows")
        print(f"Merged columns: {list(merged_df.columns)}")
        
        # Step 2: Calculate step-by-step differences (step 2 vs step 1, step 3 vs step 2, etc.)
        for item in items:
            steps = sorted(comparison_data[item]['steps'].keys())
            
            for i in range(1, len(steps)):
                prev_step = steps[i-1]
                curr_step = steps[i]
                
                prev_col = comparison_data[item]['columns'][prev_step]
                curr_col = comparison_data[item]['columns'][curr_step]
                
                # Create difference column: diff_{Item}_step_{higher_step}
                diff_col = f"diff_{item}_step_{curr_step}"
                merged_df[diff_col] = merged_df[curr_col] - merged_df[prev_col]
                
                print(f"Calculated {diff_col}: {curr_col} - {prev_col}")
                
                # Store difference column info
                if 'differences' not in comparison_data[item]:
                    comparison_data[item]['differences'] = {}
                comparison_data[item]['differences'][curr_step] = {
                    'diff_column': diff_col,
                    'from_step': prev_step,
                    'to_step': curr_step,
                    'from_column': prev_col,
                    'to_column': curr_col
                }
        
        print(f"Final merged data columns: {list(merged_df.columns)}")
        
        return merged_df, comparison_data

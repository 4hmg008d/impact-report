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
        mapping_df = self.config_loader.load_mapping_data().sort_values(by=['Item', 'Step'])
        if len(mapping_df) == 0:
            raise ValueError("No mapping data found")
        
        print("Mapping data loaded:")
        print(mapping_df[['Item', 'Step', 'StepName', 'File', 'Column']].head(10))
        
        # Get ID column and unique files
        id_column = mapping_df.iloc[0]['ID']
        print(f"ID Column: {id_column}")

        # Get full file paths
        mapping_df['File'] = mapping_df['File'].apply(self.config_loader._abs_path)
        
        #TODO: put the requirement in md file and remove this check
        # Clean up file paths and load all files
        dict_data = {}
        unique_file_paths = mapping_df['File'].unique()
        
        # Load and deduplicate all files
        for file_path in unique_file_paths:
            dict_data[file_path] = self.load_and_deduplicate_file(file_path, id_column)
        
        # Step 1: Start with the first file as base and merge only specified columns with new naming
        # Group by Item and Step to understand the structure
        impact_items = mapping_df['Item'].unique()
        
        # Build the merged dataframe with renamed columns
        merged_df = None
        comparison_mapping = {}

        for item in impact_items:
            item_mapping = mapping_df[mapping_df['Item'] == item].sort_values('Step')
            comparison_mapping[item] = {
                'steps': {},
                'step_names': {},
                'columns': {}
            }
            
            for _, row in item_mapping.iterrows():
                step = row['Step']
                step_name = row['StepName']
                file_path = row['File']
                column = row['Column']
                
                #TODO: put the requirement in md file and remove this check
                # Clean up file path
                if file_path.startswith('impact_analysis/'):
                    file_path = file_path[len('impact_analysis/'):]
                
                # Create new column name: {Item}_{Step}
                new_col_name = f"{item}_{step}"
                
                # Store step information
                comparison_mapping[item]['steps'][step] = {
                    'file_path': file_path,
                    'original_column': column,
                    'renamed_column': new_col_name,
                    'step_name': step_name
                }
                comparison_mapping[item]['step_names'][step] = step_name
                comparison_mapping[item]['columns'][step] = new_col_name
        
        # Start with the first step of the first item to establish the base dataframe
        first_item = impact_items[0]
        first_step_info = comparison_mapping[first_item]['steps'][1]
        first_file = first_step_info['file_path']
        
        # Start with ALL columns from the first file (not just ID column)
        merged_df = dict_data[first_file].copy()
        print(f"Starting with all columns from first file: {first_file}")
        print(f"Base columns: {list(merged_df.columns)}")
        
        # Rename comparison columns in the base dataframe
        first_file_rename_map = {}
        for item in impact_items:
            for step in sorted(comparison_mapping[item]['steps'].keys()):
                step_info = comparison_mapping[item]['steps'][step]
                if step_info['file_path'] == first_file:
                    orig_col = step_info['original_column']
                    new_col = step_info['renamed_column']
                    first_file_rename_map[orig_col] = new_col
        
        if first_file_rename_map:
            merged_df.rename(columns=first_file_rename_map, inplace=True)
            print(f"Renamed columns in base file: {first_file_rename_map}")
        
        # Add comparison columns from other files
        for item in impact_items:
            for step in sorted(comparison_mapping[item]['steps'].keys()):
                step_info = comparison_mapping[item]['steps'][step]
                file_path = step_info['file_path']
                orig_col = step_info['original_column']
                new_col = step_info['renamed_column']
                
                # Skip if this column is already in merged_df (from first file)
                if new_col in merged_df.columns:
                    continue
                
                if orig_col in dict_data[file_path].columns:
                    # Merge this specific column
                    temp_df = dict_data[file_path][[id_column, orig_col]].copy()
                    temp_df = temp_df.rename(columns={orig_col: new_col})
                    merged_df = merged_df.merge(temp_df, on=id_column, how='inner')
                    print(f"Added column {new_col} from {file_path}")
        
        print(f"Merged data: {len(merged_df)} rows")
        print(f"Merged columns: {list(merged_df.columns)}")
        
        # Step 2: Calculate step-by-step differences (step 2 vs step 1, step 3 vs step 2, etc.)
        for item in impact_items:
            steps = sorted(comparison_mapping[item]['steps'].keys())

            for i in range(1, len(steps)):

                # TODO: check if need first_step
                prev_step = steps[i-1]
                curr_step = steps[i]
                first_step = steps[0]
                
                prev_col = comparison_mapping[item]['columns'][prev_step]
                curr_col = comparison_mapping[item]['columns'][curr_step]
                first_col = comparison_mapping[item]['columns'][first_step]
                
                # Create difference column: diff_{Item}_step_{higher_step}
                diff_col = f"diff_{item}_step_{curr_step}"
                merged_df[diff_col] = merged_df[curr_col] - merged_df[prev_col]

                diff_col_percent = f"percent_diff_{item}_step_{curr_step}"
                # Avoid division by zero
                merged_df[diff_col_percent] = merged_df.apply(
                    lambda row: (row[diff_col] / row[prev_col] * 100) if row[prev_col] != 0 else None, axis=1
                )
                
                # Debug print
                # print(f"Calculated {diff_col}: {curr_col} - {prev_col}")
                
                # Store difference column info
                if 'differences' not in comparison_mapping[item]:
                    comparison_mapping[item]['differences'] = {}

                comparison_mapping[item]['differences'][curr_step] = {
                    'diff_column': diff_col,
                    'percent_diff_column': diff_col_percent,
                    'from_step': prev_step,
                    'to_step': curr_step,
                    'from_column': prev_col,
                    'to_column': curr_col
                }
        
        print(f"Final merged data columns: {list(merged_df.columns)}")
        
        return merged_df, comparison_mapping

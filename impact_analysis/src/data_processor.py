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
    
    def generate_comparison_mapping(self) -> Dict[str, Dict]:
        """Generate comparison mapping from configuration data
        
        Returns:
            Dictionary mapping items to their step information (without 'differences' component)
        """
        # Load mapping data
        mapping_df = self.config_loader.load_mapping_data().sort_values(by=['Item', 'Step'])
        if len(mapping_df) == 0:
            raise ValueError("No mapping data found")
        
        print("Mapping data loaded:")
        print(mapping_df[['Item', 'Step', 'StepName', 'File', 'Column']].head(10))
        
        # Get full file paths
        mapping_df['File'] = mapping_df['File'].apply(self.config_loader._abs_path)
        
        # Group by Item and Step to understand the structure
        impact_items = mapping_df['Item'].unique()
        
        # Build comparison mapping
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
        
        return comparison_mapping
    
    def load_and_merge_data(self, comparison_mapping: Dict[str, Dict]) -> pd.DataFrame:
        """Load and merge data files based on comparison mapping
        
        Args:
            comparison_mapping: Mapping containing step information for each item
            
        Returns:
            Merged DataFrame with renamed columns
        """
        # Load mapping data to get ID column
        mapping_df = self.config_loader.load_mapping_data()
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
        
        # Get all items
        impact_items = list(comparison_mapping.keys())
        
        # Start with the first step of the first item to establish the base dataframe
        first_item = impact_items[0]
        first_step_info = comparison_mapping[first_item]['steps'][1]
        first_file = first_step_info['file_path']
        
        # Start with ALL columns from the first file (not just ID column)
        merged_df = dict_data[first_file].copy()
        
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
        
        print(f"Merged data: {len(merged_df)} rows")
        print(f"Merged columns: {list(merged_df.columns)}")
        
        return merged_df
    
    def generate_differences(self, merged_df: pd.DataFrame, comparison_mapping: Dict[str, Dict]) -> Dict[str, Dict]:
        """Generate difference columns and add 'differences' component to comparison mapping
        
        Args:
            merged_df: Merged DataFrame
            comparison_mapping: Mapping containing step information for each item
            
        Returns:
            Updated comparison_mapping with 'differences' component added
        """
        # Get all items
        impact_items = list(comparison_mapping.keys())
        merged_df_w_diff = merged_df.copy()
        
        # Calculate step-by-step differences
        for item in impact_items:
            steps = sorted(comparison_mapping[item]['steps'].keys())

            # Initialize differences dictionary
            if 'differences' not in comparison_mapping[item]:
                comparison_mapping[item]['differences'] = {}
            
            # Calculate overall difference (last step vs first step)
            if len(steps) >= 2:
                first_step = steps[0]
                last_step = steps[-1]
                first_col = comparison_mapping[item]['columns'][first_step]
                last_col = comparison_mapping[item]['columns'][last_step]
                
                # Create overall difference column: diff_{Item}_step_all
                overall_diff_col = f"diff_{item}_step_all"
                merged_df_w_diff[overall_diff_col] = merged_df_w_diff[last_col] - merged_df_w_diff[first_col]
                
                overall_diff_col_percent = f"percent_diff_{item}_step_all"
                # Avoid division by zero
                merged_df_w_diff[overall_diff_col_percent] = merged_df_w_diff.apply(
                    lambda row: (row[overall_diff_col] / row[first_col] * 100) if row[first_col] != 0 else None, axis=1
                )

                # Store overall difference as step 1 with name "All Steps"
                comparison_mapping[item]['differences'][1] = {
                    'diff_column': overall_diff_col,
                    'percent_diff_column': overall_diff_col_percent,
                    'from_step': first_step,
                    'to_step': last_step,
                    'from_column': first_col,
                    'to_column': last_col
                }
                # Add step name for step 1
                comparison_mapping[item]['step_names'][1] = 'All Steps'

            # Calculate step-by-step differences
            for i in range(1, len(steps)):

                prev_step = steps[i-1]
                curr_step = steps[i]
                
                prev_col = comparison_mapping[item]['columns'][prev_step]
                curr_col = comparison_mapping[item]['columns'][curr_step]
                
                # Create difference column: diff_{Item}_step_{higher_step}
                diff_col = f"diff_{item}_step_{curr_step}"
                merged_df_w_diff[diff_col] = merged_df_w_diff[curr_col] - merged_df_w_diff[prev_col]

                diff_col_percent = f"percent_diff_{item}_step_{curr_step}"
                # Avoid division by zero
                merged_df_w_diff[diff_col_percent] = merged_df_w_diff.apply(
                    lambda row: (row[diff_col] / row[prev_col] * 100) if row[prev_col] != 0 else None, axis=1
                )
                
                # Store difference column info
                comparison_mapping[item]['differences'][curr_step] = {
                    'diff_column': diff_col,
                    'percent_diff_column': diff_col_percent,
                    'from_step': prev_step,
                    'to_step': curr_step,
                    'from_column': prev_col,
                    'to_column': curr_col
                }
        
        print(f"Difference info generated")
        
        return merged_df_w_diff, comparison_mapping
    
    def process_data(self) -> Tuple[pd.DataFrame, Dict[str, Dict]]:
        """Execute the complete data processing pipeline with new step-based approach
        
        This method orchestrates the three main steps:
        1. Generate comparison mapping from configuration
        2. Load and merge data files
        3. Generate difference columns
        
        Returns:
            Tuple of (merged_df, comparison_mapping)
        """
        # Step 1: Generate comparison mapping
        comparison_mapping = self.generate_comparison_mapping()
        
        # Step 2: Load and merge data
        merged_df = self.load_and_merge_data(comparison_mapping)
        
        # Step 3: Generate differences (modifies merged_df in place and updates comparison_mapping)
        merged_df_w_diff, comparison_mapping = self.generate_differences(merged_df, comparison_mapping)
        
        return merged_df_w_diff, comparison_mapping
    
    def generate_aggregated_summary(self, merged_df: pd.DataFrame, comparison_mapping: Dict[str, Dict]) -> Tuple[pd.DataFrame, Dict[str, Dict]]:
        """Generate aggregated summary table with totals and percentage differences
        
        This method:
        1. Aggregates merged_df by summing all rows for each step column
        2. Creates one row per item with step totals
        3. Calculates percentage differences based on aggregated totals
        
        Args:
            merged_df: The merged dataframe containing all data rows
            comparison_mapping: Mapping containing step information (must have 'steps' component, 
                              'differences' component is optional and will be computed if missing)
            
        Returns:
            DataFrame with summary table containing:
            - Item column (rows - one per item)
            - Step columns with total values
            - Percentage difference columns for each step
            - All Steps percentage difference at the very right
        """
        
        # get all renamed columns for each item and step
        impact_items = list(comparison_mapping.keys())
        renamed_columns = []

        for item in impact_items:
            item_steps = comparison_mapping[item]['steps']
            for step in item_steps:
                renamed_columns.append(item_steps[step]['renamed_column'])

        # aggregate merged_df by summing all rows for each step column
        summary_data = pd.DataFrame([merged_df[renamed_columns].sum()])

        merged_df_w_diff, summary_comparison_mapping = self.generate_differences(summary_data, comparison_mapping)

        return merged_df_w_diff, summary_comparison_mapping

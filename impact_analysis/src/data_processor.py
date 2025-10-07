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
            Dictionary mapping items to their stage information (without 'differences' component)
        """
        # Load mapping data
        mapping_df = self.config_loader.load_mapping_data().sort_values(by=['Item', 'Stage'])
        if len(mapping_df) == 0:
            raise ValueError("No mapping data found")
        
        print("Mapping data loaded:")
        print(mapping_df[['Item', 'Stage', 'StageName', 'File', 'Column']].head(10))
        
        # Get full file paths
        mapping_df['File'] = mapping_df['File'].apply(self.config_loader._abs_path)
        
        # Group by Item and Stage to understand the structure
        impact_items = mapping_df['Item'].unique()
        
        # Build comparison mapping
        comparison_mapping = {}
        
        for item in impact_items:
            item_mapping = mapping_df[mapping_df['Item'] == item].sort_values('Stage')
            comparison_mapping[item] = {
                'stages': {},
                'stage_names': {},
                'columns': {}
            }
            
            for _, row in item_mapping.iterrows():
                stage = row['Stage']
                stage_name = row['StageName']
                file_path = row['File']
                column = row['Column']
                
                #TODO: put the requirement in md file and remove this check
                # Clean up file path
                if file_path.startswith('impact_analysis/'):
                    file_path = file_path[len('impact_analysis/'):]
                
                # Create new column name: {Item}_{Stage}
                new_col_name = f"{item}_{stage}"
                
                # Store stage information
                comparison_mapping[item]['stages'][stage] = {
                    'file_path': file_path,
                    'original_column': column,
                    'renamed_column': new_col_name,
                    'stage_name': stage_name
                }
                comparison_mapping[item]['stage_names'][stage] = stage_name
                comparison_mapping[item]['columns'][stage] = new_col_name
        
        return comparison_mapping
    
    def load_and_merge_data(self, comparison_mapping: Dict[str, Dict]) -> pd.DataFrame:
        """Load and merge data files based on comparison mapping
        
        Args:
            comparison_mapping: Mapping containing stage information for each item
            
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
        
        # Start with the first stage of the first item to establish the base dataframe
        first_item = impact_items[0]
        first_stage_info = comparison_mapping[first_item]['stages'][1]
        first_file = first_stage_info['file_path']
        
        # Start with ALL columns from the first file (not just ID column)
        merged_df = dict_data[first_file].copy()
        
        # Rename comparison columns in the base dataframe
        first_file_rename_map = {}
        for item in impact_items:
            for stage in sorted(comparison_mapping[item]['stages'].keys()):
                stage_info = comparison_mapping[item]['stages'][stage]
                if stage_info['file_path'] == first_file:
                    orig_col = stage_info['original_column']
                    new_col = stage_info['renamed_column']
                    first_file_rename_map[orig_col] = new_col
        
        if first_file_rename_map:
            merged_df.rename(columns=first_file_rename_map, inplace=True)
        

        # Add comparison columns from other files
        for item in impact_items:
            for stage in sorted(comparison_mapping[item]['stages'].keys()):
                stage_info = comparison_mapping[item]['stages'][stage]
                file_path = stage_info['file_path']
                orig_col = stage_info['original_column']
                new_col = stage_info['renamed_column']
                
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
        
        Step numbering:
        - Step 0: Overall difference (last stage - first stage)
        - Step N: Difference from stage N to stage N+1 (for N >= 1)
        
        Args:
            merged_df: Merged DataFrame
            comparison_mapping: Mapping containing stage information for each item
            
        Returns:
            Updated comparison_mapping with 'differences' component added
        """
        # Get all items
        impact_items = list(comparison_mapping.keys())
        merged_df_w_diff = merged_df.copy()
        
        # Add a step_names dictionary to keep track of stage names
        dict_step_names = {}

        # Calculate step-by-step differences
        for item in impact_items:
            stages = sorted(comparison_mapping[item]['stages'].keys())

            # Initialize differences dictionary (stores step information)
            if 'differences' not in comparison_mapping[item]:
                comparison_mapping[item]['differences'] = {}
            
            # Calculate overall difference (last stage vs first stage) - this is Step 0
            if len(stages) >= 2:
                first_stage = stages[0]
                last_stage = stages[-1]
                first_col = comparison_mapping[item]['columns'][first_stage]
                last_col = comparison_mapping[item]['columns'][last_stage]
                
                # Create overall difference column: diff_{Item}_step_0
                overall_diff_col = f"diff_{item}_step_0"
                merged_df_w_diff[overall_diff_col] = merged_df_w_diff[last_col] - merged_df_w_diff[first_col]
                
                overall_diff_col_percent = f"percent_diff_{item}_step_0"
                # Avoid division by zero
                merged_df_w_diff[overall_diff_col_percent] = merged_df_w_diff.apply(
                    lambda row: (row[overall_diff_col] / row[first_col] * 100) if row[first_col] != 0 else None, axis=1
                )

                # Store overall difference as step 0 with name "Overall"
                comparison_mapping[item]['differences'][0] = {
                    'diff_column': overall_diff_col,
                    'percent_diff_column': overall_diff_col_percent,
                    'from_stage': first_stage,
                    'to_stage': last_stage,
                    'from_column': first_col,
                    'to_column': last_col,
                    'step_name': 'Overall'
                }
                dict_step_names[0] = 'Overall'

            # Calculate step-by-step differences (step N goes from stage N to stage N+1)
            for i in range(1, len(stages)):

                prev_stage = stages[i-1]
                curr_stage = stages[i]
                
                prev_col = comparison_mapping[item]['columns'][prev_stage]
                curr_col = comparison_mapping[item]['columns'][curr_stage]
                
                # Step number equals the starting stage number
                step_num = prev_stage
                
                # Create difference column: diff_{Item}_step_{step_num}
                diff_col = f"diff_{item}_step_{step_num}"
                merged_df_w_diff[diff_col] = merged_df_w_diff[curr_col] - merged_df_w_diff[prev_col]

                diff_col_percent = f"percent_diff_{item}_step_{step_num}"
                # Avoid division by zero
                merged_df_w_diff[diff_col_percent] = merged_df_w_diff.apply(
                    lambda row: (row[diff_col] / row[prev_col] * 100) if row[prev_col] != 0 else None, axis=1
                )
                
                # Get the stage name from the target stage (where we're going to)
                step_name = comparison_mapping[item]['stage_names'][curr_stage]
                
                # Store difference column info
                comparison_mapping[item]['differences'][step_num] = {
                    'diff_column': diff_col,
                    'percent_diff_column': diff_col_percent,
                    'from_stage': prev_stage,
                    'to_stage': curr_stage,
                    'from_column': prev_col,
                    'to_column': curr_col,
                    'step_name': step_name
                }
                dict_step_names[step_num] = step_name
        
            comparison_mapping[item]['step_names'] = dict_step_names
        
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
    
    def aggregate_merged_data(self, merged_df: pd.DataFrame, comparison_mapping: Dict[str, Dict]) -> Dict:
        """Generate aggregated summary table with totals and percentage differences
        
        This method:
        1. Extracts all renamed columns from comparison_mapping for each item and stage
        2. Aggregates merged_df by summing all rows for each stage column
        3. Creates a single-row summary DataFrame with column totals
        4. Calls generate_differences to compute difference columns and percentage differences
        
        Args:
            merged_df: The merged dataframe containing all data rows
            comparison_mapping: Mapping containing stage information (must have 'stages' component, 
                      'differences' component is optional and will be computed)

        Returns:
            dict_comparison_summary: Updated comparison_mapping with 'differences' component
        """
        
        # get all renamed columns for each item and stage
        impact_items = list(comparison_mapping.keys())
        renamed_columns = []

        for item in impact_items:
            item_stages = comparison_mapping[item]['stages']
            for stage in item_stages:
                renamed_columns.append(item_stages[stage]['renamed_column'])

        # aggregate merged_df by summing all rows for each stage column
        summary_data = pd.DataFrame([merged_df[renamed_columns].sum()])

        # convert the df into dict for easier manipulation
        dict_comparison_summary = {}

        for item_name, item_dict in comparison_mapping.items():
            
            dict_comparison_summary[item_name] = {}
            sorted_stages = sorted(item_dict['stages'].keys())
            value_total_first_stage = summary_data[item_dict['columns'][sorted_stages[0]]].sum()
            
            for idx, stage in enumerate(sorted_stages):
                stage_name = item_dict['stage_names'][stage]
                col_name = item_dict['columns'][stage]
                value_total = summary_data[col_name].sum()
                value_total_percent = value_total / value_total_first_stage * 100
                
                # Calculate the difference for this stage
                if idx == 0:
                    value_diff = 0  # First stage has no difference
                    value_diff_percent = 0
                else:
                    prev_stage = sorted_stages[idx - 1]
                    prev_col_name = item_dict['columns'][prev_stage]
                    value_diff = value_total - summary_data[prev_col_name].sum()
                    value_diff_percent = value_diff / value_total_first_stage * 100

                dict_comparison_summary[item_name][idx] = {
                    'stage_name': stage_name,
                    'value_total': value_total,
                    'value_diff': value_diff,
                    'value_total_percent': value_total_percent,
                    'value_diff_percent': value_diff_percent
                }

        # merged_df_w_diff, dict_comparison_summary = self.generate_differences(summary_data, comparison_mapping)

        return dict_comparison_summary

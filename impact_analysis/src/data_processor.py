"""
Data processing module for impact analysis tool using Pandas
"""

import pandas as pd
from typing import Dict, List, Tuple
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
import json  # Added for pretty-printing debug info

logger = logging.getLogger(__name__)


class DataProcessor:
    """Processes benchmark and target data using Pandas"""
    
    def __init__(self, config_loader):
        self.config_loader = config_loader
    
    def load_and_deduplicate_file(self, file_path: str, id_column: str) -> pd.DataFrame:
        """Load file and keep only first row for each ID value using Pandas"""
        try:
            df = pd.read_excel(file_path, engine='calamine')
            logger.info(f"Loaded {len(df)} rows from {file_path}")
            
            # Keep only first row for each ID value using Pandas
            df_deduped = df.drop_duplicates(subset=[id_column], keep='first')
            logger.info(f"After deduplication: {len(df_deduped)} rows")
            
            return df_deduped
        except Exception as e:
            raise ValueError(f"Failed to load file {file_path}: {e}")
    
    def generate_comparison_mapping(self) -> Dict[str, Dict]:
        """Generate comparison mapping from configuration data
        
        Returns:
            Dictionary mapping items to their stage information (without 'differences' component)
            Also includes renewal column information if renewal feature is enabled
        """
        # Load mapping data - preserve original order from config file
        mapping_df = self.config_loader.load_mapping_data()
        if len(mapping_df) == 0:
            raise ValueError("No mapping data found")
        
        logger.info("Mapping data loaded:")
        logger.info(f"\n{mapping_df[['Item', 'Stage', 'StageName', 'File', 'Column']].head(10)}")
        
        # Get full file paths
        mapping_df['File'] = mapping_df['File'].apply(self.config_loader._abs_path)
        
        # Get unique items in the order they first appear (preserves config file order)
        impact_items = mapping_df['Item'].unique().tolist()
        
        # Build comparison mapping, maintaining the original order
        comparison_mapping = {}
        
        # Check if renewal feature is enabled
        is_renewal_enabled = self.config_loader.is_renewal_enabled()
        
        for item in impact_items:
            item_mapping = mapping_df[mapping_df['Item'] == item].sort_values('Stage')
            comparison_mapping[item] = {
                'stages': {},
                'stage_names': {},
                'columns': {},
                'renewal_enabled': is_renewal_enabled
            }
            
            # If renewal is enabled, add renewal column info
            if is_renewal_enabled:
                comparison_mapping[item]['renewal_columns'] = {}
            
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
                
                # If renewal is enabled and RNColumn exists, add renewal column info
                if is_renewal_enabled and 'RNColumn' in row and pd.notna(row['RNColumn']):
                    rn_column = row['RNColumn']
                    rn_col_name = f"{item}_{stage}_rn"
                    comparison_mapping[item]['renewal_columns'][stage] = {
                        'file_path': file_path,
                        'original_column': rn_column,
                        'renamed_column': rn_col_name,
                        'stage_name': stage_name
                    }
        
        return comparison_mapping
    
    def load_and_merge_data(self, comparison_mapping: Dict[str, Dict]) -> pd.DataFrame:
        """Load and merge data files based on comparison mapping
        
        Args:
            comparison_mapping: Mapping containing stage information for each item
            
        Returns:
            Merged DataFrame with renamed columns (includes renewal columns if enabled)
        """
        # Load mapping data to get ID column
        mapping_df = self.config_loader.load_mapping_data()
        id_column = mapping_df.iloc[0]['ID']
        logger.info(f"ID Column: {id_column}")
        
        # Get full file paths
        mapping_df['File'] = mapping_df['File'].apply(self.config_loader._abs_path)
        
        # Check if renewal is enabled
        is_renewal_enabled = self.config_loader.is_renewal_enabled()
        
        # Clean up file paths and load all files
        dict_data = {}
        unique_file_paths = mapping_df['File'].unique()
        
        # Load and deduplicate all files in parallel using ThreadPoolExecutor
        logger.info(f"Loading {len(unique_file_paths)} files in parallel...")
        with ThreadPoolExecutor(max_workers=min(len(unique_file_paths), os.cpu_count() or 4)) as executor:
            # Submit all file loading tasks
            future_to_filepath = {
                executor.submit(self.load_and_deduplicate_file, file_path, id_column): file_path
                for file_path in unique_file_paths
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_filepath):
                file_path = future_to_filepath[future]
                try:
                    dict_data[file_path] = future.result()
                except Exception as e:
                    print(f"Error loading {file_path}: {e}")
                    raise
        
        logger.info(f"All {len(unique_file_paths)} files loaded successfully")
        
        # Get all items
        impact_items = list(comparison_mapping.keys())
        
        # Start with the first stage of the first item to establish the base dataframe
        first_item = impact_items[0]
        first_stage_info = comparison_mapping[first_item]['stages'][1]
        first_file = first_stage_info['file_path']
        
        # Filter to keep only segment columns + ID (applies regardless of renewal flag)
        segment_columns = self.config_loader.load_segment_columns()
        
        if segment_columns:
            # Segment columns specified - filter the data
            print(f"Segment columns to keep: {segment_columns}")
            
            # Get all column names from all files
            all_columns_by_file = {}
            for file_path in unique_file_paths:
                all_columns_by_file[file_path] = dict_data[file_path].columns.tolist()
            
            # Pick first occurrence of each segment column
            columns_to_keep = [id_column]  # Always keep ID column
            for seg_col in segment_columns:
                # Skip if this is the ID column (already added)
                if seg_col == id_column:
                    continue
                    
                for file_path in unique_file_paths:
                    if seg_col in all_columns_by_file[file_path]:
                        columns_to_keep.append(seg_col)
                        break  # Only keep first occurrence
            
            # Start with filtered columns from first file
            columns_in_first_file = [col for col in columns_to_keep if col in dict_data[first_file].columns]
            merged_df = dict_data[first_file][columns_in_first_file].copy()
            logger.info(f"Starting with {len(columns_in_first_file)} segment columns from first file")
        else:
            # No segment columns specified - keep all columns from first file
            merged_df = dict_data[first_file].copy()
            logger.info(f"No segment columns specified - keeping all columns from first file")
        
        # Rename comparison columns in the base dataframe
        first_file_rename_map = {}
        for item in impact_items:
            for stage in sorted(comparison_mapping[item]['stages'].keys()):
                stage_info = comparison_mapping[item]['stages'][stage]
                if stage_info['file_path'] == first_file:
                    orig_col = stage_info['original_column']
                    new_col = stage_info['renamed_column']
                    first_file_rename_map[orig_col] = new_col
            
            # Also rename renewal columns if enabled
            if is_renewal_enabled and 'renewal_columns' in comparison_mapping[item]:
                for stage in sorted(comparison_mapping[item]['renewal_columns'].keys()):
                    rn_info = comparison_mapping[item]['renewal_columns'][stage]
                    if rn_info['file_path'] == first_file:
                        orig_col = rn_info['original_column']
                        new_col = rn_info['renamed_column']
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
            
            # Add renewal columns from other files if enabled
            if is_renewal_enabled and 'renewal_columns' in comparison_mapping[item]:
                for stage in sorted(comparison_mapping[item]['renewal_columns'].keys()):
                    rn_info = comparison_mapping[item]['renewal_columns'][stage]
                    file_path = rn_info['file_path']
                    orig_col = rn_info['original_column']
                    new_col = rn_info['renamed_column']
                    
                    # Skip if this column is already in merged_df (from first file)
                    if new_col in merged_df.columns:
                        continue
                    
                    if orig_col in dict_data[file_path].columns:
                        # Merge this specific renewal column
                        temp_df = dict_data[file_path][[id_column, orig_col]].copy()
                        temp_df = temp_df.rename(columns={orig_col: new_col})
                        merged_df = merged_df.merge(temp_df, on=id_column, how='inner')

        logger.info(f"Merged data: {len(merged_df)} rows")
        logger.info(f"Merged columns: {list(merged_df.columns)}")

        return merged_df
    
    def generate_differences(self, merged_df: pd.DataFrame, comparison_mapping: Dict[str, Dict]) -> Dict[str, Dict]:
        """Generate difference columns and add 'differences' component to comparison mapping
        
        Step numbering:
        - Step 0: Overall difference (last stage - first stage)
        - Step N: Difference from stage N to stage N+1 (for N >= 1)
        
        If renewal is enabled, also generates renewal differences for New Business and Renewal segments.
        
        Args:
            merged_df: Merged DataFrame
            comparison_mapping: Mapping containing stage information for each item
            
        Returns:
            Updated comparison_mapping with 'differences' component added
        """
        # Get all items
        impact_items = list(comparison_mapping.keys())
        
        # Check if renewal is enabled
        is_renewal_enabled = self.config_loader.is_renewal_enabled()
        
        # Dictionary to store all new columns to be added
        new_columns = {}
        
        # Add a step_names dictionary to keep track of stage names
        dict_step_names = {}

        # Calculate step-by-step differences
        for item in impact_items:
            stages = sorted(comparison_mapping[item]['stages'].keys())

            # Initialize differences dictionary (stores step information)
            if 'differences' not in comparison_mapping[item]:
                comparison_mapping[item]['differences'] = {}
            
            # If renewal is enabled, initialize renewal differences
            if is_renewal_enabled and 'renewal_columns' in comparison_mapping[item]:
                comparison_mapping[item]['renewal_differences'] = {}
            
            # Calculate overall difference (last stage vs first stage) - this is Step 0
            if len(stages) >= 2:
                first_stage = stages[0]
                last_stage = stages[-1]
                first_col = comparison_mapping[item]['columns'][first_stage]
                last_col = comparison_mapping[item]['columns'][last_stage]
                
                # Create overall difference column: diff_{Item}_step_0
                overall_diff_col = f"diff_{item}_step_0"
                new_columns[overall_diff_col] = merged_df[last_col] - merged_df[first_col]
                
                overall_diff_col_percent = f"percent_diff_{item}_step_0"
                # Avoid division by zero - use vectorized where instead of apply
                new_columns[overall_diff_col_percent] = pd.Series(
                    new_columns[overall_diff_col] / merged_df[first_col]
                ).where(merged_df[first_col] != 0, None)

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
                
                # Calculate renewal differences for overall if enabled
                if is_renewal_enabled and 'renewal_columns' in comparison_mapping[item]:
                    if first_stage in comparison_mapping[item]['renewal_columns'] and last_stage in comparison_mapping[item]['renewal_columns']:
                        first_rn_col = comparison_mapping[item]['renewal_columns'][first_stage]['renamed_column']
                        last_rn_col = comparison_mapping[item]['renewal_columns'][last_stage]['renamed_column']
                        
                        # Create renewal difference column: diff_{Item}_step_0_rn
                        overall_rn_diff_col = f"diff_{item}_step_0_rn"
                        new_columns[overall_rn_diff_col] = merged_df[last_rn_col] - merged_df[first_rn_col]
                        
                        overall_rn_diff_col_percent = f"percent_diff_{item}_step_0_rn"
                        new_columns[overall_rn_diff_col_percent] = pd.Series(
                            new_columns[overall_rn_diff_col] / merged_df[first_rn_col]
                        ).where(merged_df[first_rn_col] != 0, None)
                        
                        comparison_mapping[item]['renewal_differences'][0] = {
                            'diff_column': overall_rn_diff_col,
                            'percent_diff_column': overall_rn_diff_col_percent,
                            'from_stage': first_stage,
                            'to_stage': last_stage,
                            'from_column': first_rn_col,
                            'to_column': last_rn_col,
                            'step_name': 'Overall'
                        }

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
                new_columns[diff_col] = merged_df[curr_col] - merged_df[prev_col]

                diff_col_percent = f"percent_diff_{item}_step_{step_num}"
                # Avoid division by zero - use vectorized where instead of apply
                new_columns[diff_col_percent] = pd.Series(
                    new_columns[diff_col] / merged_df[prev_col]
                ).where(merged_df[prev_col] != 0, None)
                
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
                
                # Calculate renewal differences for this step if enabled
                if is_renewal_enabled and 'renewal_columns' in comparison_mapping[item]:
                    if prev_stage in comparison_mapping[item]['renewal_columns'] and curr_stage in comparison_mapping[item]['renewal_columns']:
                        prev_rn_col = comparison_mapping[item]['renewal_columns'][prev_stage]['renamed_column']
                        curr_rn_col = comparison_mapping[item]['renewal_columns'][curr_stage]['renamed_column']
                        
                        # Create renewal difference column: diff_{Item}_step_{step_num}_rn
                        rn_diff_col = f"diff_{item}_step_{step_num}_rn"
                        new_columns[rn_diff_col] = merged_df[curr_rn_col] - merged_df[prev_rn_col]
                        
                        rn_diff_col_percent = f"percent_diff_{item}_step_{step_num}_rn"
                        new_columns[rn_diff_col_percent] = pd.Series(
                            new_columns[rn_diff_col] / merged_df[prev_rn_col]
                        ).where(merged_df[prev_rn_col] != 0, None)
                        
                        comparison_mapping[item]['renewal_differences'][step_num] = {
                            'diff_column': rn_diff_col,
                            'percent_diff_column': rn_diff_col_percent,
                            'from_stage': prev_stage,
                            'to_stage': curr_stage,
                            'from_column': prev_rn_col,
                            'to_column': curr_rn_col,
                            'step_name': step_name
                        }
        
            comparison_mapping[item]['step_names'] = dict_step_names
        
        # Add all new columns at once to avoid fragmentation
        merged_df_w_diff = pd.concat([merged_df, pd.DataFrame(new_columns, index=merged_df.index)], axis=1)

        logger.info(f"Difference info generated")

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

        # Debug
        # print("Comparison Mapping:")
        # open("impact_analysis/debug/comparison_mapping.json", "w").write(json.dumps(comparison_mapping, indent=2))
        
        # Step 2: Load and merge data
        merged_df = self.load_and_merge_data(comparison_mapping)
        
        # Step 3: Generate differences (modifies merged_df in place and updates comparison_mapping)
        merged_df_w_diff, comparison_mapping = self.generate_differences(merged_df, comparison_mapping)
        
        return merged_df_w_diff, comparison_mapping

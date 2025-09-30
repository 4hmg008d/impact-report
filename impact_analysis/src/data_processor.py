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
    
    def merge_data(
        self, benchmark_df: pd.DataFrame, target_df: pd.DataFrame, 
        id_column: str, benchmark_col: str, target_col: str, all_comparison_cols: set = None
    ) -> pd.DataFrame:
        """Merge benchmark and target data, keeping unique columns using Pandas"""
        # Rename comparison columns with file name prefixes
        mapping_df = self.config_loader.load_mapping_data()
        mapping_row = mapping_df.iloc[0]
        
        benchmark_file_name = os.path.splitext(os.path.basename(mapping_row['Benchmark File']))[0]
        target_file_name = os.path.splitext(os.path.basename(mapping_row['Target File']))[0]
        
        # Create copies to avoid modifying original dataframes
        benchmark_df_copy = benchmark_df.copy()
        target_df_copy = target_df.copy()
        
        # Rename comparison columns using Pandas
        benchmark_df_renamed = benchmark_df_copy.rename(columns={benchmark_col: f"{benchmark_file_name}_{benchmark_col}"})
        target_df_renamed = target_df_copy.rename(columns={target_col: f"{target_file_name}_{target_col}"})
        
        # Identify common columns (excluding id_column, the renamed comparison columns, and all comparison columns)
        excluded_cols = {id_column, f"{benchmark_file_name}_{benchmark_col}", f"{target_file_name}_{target_col}"}
        if all_comparison_cols:
            excluded_cols.update(all_comparison_cols)
        
        benchmark_cols = set(benchmark_df_renamed.columns) - excluded_cols
        target_cols = set(target_df_renamed.columns) - excluded_cols
        common_cols = benchmark_cols.intersection(target_cols)
        
        # For common columns, only keep from benchmark_df
        # Remove common columns from target_df before merge
        target_df_filtered = target_df_renamed.drop(columns=list(common_cols))
        
        # Also remove the original comparison columns from both dataframes
        columns_to_remove = [benchmark_col, target_col]
        benchmark_df_renamed = benchmark_df_renamed.drop(columns=[col for col in columns_to_remove if col in benchmark_df_renamed.columns])
        target_df_filtered = target_df_filtered.drop(columns=[col for col in columns_to_remove if col in target_df_filtered.columns])
        
        # Merge on ID column using Pandas
        merged_df = pd.merge(
            benchmark_df_renamed, 
            target_df_filtered, 
            on=id_column, 
            how='inner'
        )
        
        print(f"Merged data: {len(merged_df)} rows")
        print(f"Common columns kept from benchmark_df: {list(common_cols)}")
        return merged_df
    
    def calculate_differences(self, merged_df: pd.DataFrame, benchmark_col: str, target_col: str) -> pd.DataFrame:
        """Calculate percentage differences between benchmark and target columns using Pandas"""
        # Get the actual column names after renaming
        mapping_df = self.config_loader.load_mapping_data()
        mapping_row = mapping_df.iloc[0]
        
        benchmark_file_name = os.path.splitext(os.path.basename(mapping_row['Benchmark File']))[0]
        target_file_name = os.path.splitext(os.path.basename(mapping_row['Target File']))[0]
        
        benchmark_col_actual = f"{benchmark_file_name}_{benchmark_col}"
        target_col_actual = f"{target_file_name}_{target_col}"
        
        # Calculate percentage difference: (target / benchmark - 1) using Pandas
        diff_col_name = f"diff_{benchmark_col}"
        
        merged_df[diff_col_name] = (merged_df[target_col_actual] / merged_df[benchmark_col_actual] - 1)
        
        # Handle division by zero (infinity values)
        merged_df[diff_col_name] = merged_df[diff_col_name].replace([float('inf'), float('-inf')], None)
        
        print(f"Calculated differences for {benchmark_col}")
        return merged_df
    
    def process_data(self) -> Tuple[pd.DataFrame, Dict[str, str]]:
        """Execute the complete data processing pipeline for multiple comparison items"""
        # Load mapping data
        mapping_df = self.config_loader.load_mapping_data()
        if len(mapping_df) == 0:
            raise ValueError("No mapping data found")
        
        # Get all comparison columns to exclude from common columns
        all_comparison_cols = set()
        for _, row in mapping_df.iterrows():
            all_comparison_cols.add(row['Benchmark Column'])
            all_comparison_cols.add(row['Target Column'])
        
        # Get unique files from mapping
        unique_files = set()
        for _, row in mapping_df.iterrows():
            unique_files.add(row['Benchmark File'])
            unique_files.add(row['Target File'])
        
        # Load and deduplicate all files
        file_data = {}
        id_column = mapping_df.iloc[0]['ID']  # Assume same ID column for all comparisons
        
        print(f"ID Column: {id_column}")
        
        for file_path in unique_files:
            file_data[file_path] = self.load_and_deduplicate_file(file_path, id_column)
        
        # Process each comparison item
        comparison_data = {}
        merged_df = None
        
        for _, mapping_row in mapping_df.iterrows():
            item_name = mapping_row['Item']
            benchmark_file = mapping_row['Benchmark File']
            benchmark_col = mapping_row['Benchmark Column']
            target_file = mapping_row['Target File']
            target_col = mapping_row['Target Column']
            
            print(f"Processing {item_name}: {benchmark_file} -> {benchmark_col} vs {target_file} -> {target_col}")
            
            # Get dataframes for this comparison
            benchmark_df = file_data[benchmark_file]
            target_df = file_data[target_file]
            
            # Merge data for this comparison
            if merged_df is None:
                # First comparison - create the base merged dataframe
                merged_df = self.merge_data(benchmark_df, target_df, id_column, benchmark_col, target_col, all_comparison_cols)
            else:
                # For subsequent comparisons, only merge the specific comparison columns we need
                # Create a temporary dataframe with just the ID and the comparison columns
                temp_df = pd.DataFrame()
                temp_df[id_column] = benchmark_df[id_column]
                
                # Add the renamed comparison columns
                mapping_df = self.config_loader.load_mapping_data()
                mapping_row = mapping_df.iloc[0]
                benchmark_file_name = os.path.splitext(os.path.basename(mapping_row['Benchmark File']))[0]
                target_file_name = os.path.splitext(os.path.basename(mapping_row['Target File']))[0]
                
                temp_df[f"file1_{benchmark_col}"] = benchmark_df[benchmark_col]
                temp_df[f"file2_{target_col}"] = target_df[target_col]
                
                # Merge only the comparison columns with the main dataframe
                merged_df = pd.merge(
                    merged_df,
                    temp_df,
                    on=id_column,
                    how='inner'
                )
            
            # Calculate differences for this comparison
            merged_df = self.calculate_differences(merged_df, benchmark_col, target_col)
            
            # Store the difference column name for this comparison
            diff_col = f"diff_{benchmark_col}"
            comparison_data[item_name] = diff_col
        
        # Clean up the merged dataframe to remove any unwanted columns
        # Keep only the ID columns, common columns, and the comparison-specific columns
        expected_columns = set(merged_df.columns)
        
        # Remove any columns that are original comparison columns (not the renamed ones)
        for col in all_comparison_cols:
            if col in expected_columns:
                expected_columns.remove(col)
        
        # Also remove any columns with suffixes (_x, _y) that are duplicates
        columns_to_keep = []
        for col in merged_df.columns:
            if col not in all_comparison_cols and not col.endswith('_x') and not col.endswith('_y'):
                columns_to_keep.append(col)
        
        # Keep only the cleaned columns
        merged_df = merged_df[columns_to_keep]
        
        print(f"Final merged data columns: {list(merged_df.columns)}")
        return merged_df, comparison_data

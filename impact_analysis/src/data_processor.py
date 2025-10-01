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
    
    def process_data(self) -> Tuple[pd.DataFrame, Dict[str, str]]:
        """Execute the complete data processing pipeline for multiple comparison items"""
        # Load mapping data
        mapping_df = self.config_loader.load_mapping_data()
        if len(mapping_df) == 0:
            raise ValueError("No mapping data found")
        
        # Step 1: Get all benchmark and target columns from all files and rename them first
        # Create a mapping of (file_path, original_col) -> renamed_col
        file_col_mapping = {}
        for _, row in mapping_df.iterrows():
            benchmark_file = row['Benchmark File']
            benchmark_col = row['Benchmark Column']
            target_file = row['Target File']
            target_col = row['Target Column']
            
            # Get file names for prefix
            benchmark_file_name = os.path.splitext(os.path.basename(benchmark_file))[0]
            target_file_name = os.path.splitext(os.path.basename(target_file))[0]
            
            # Store renamed column mappings by file
            file_col_mapping[(benchmark_file, benchmark_col)] = f"{benchmark_file_name}_{benchmark_col}"
            file_col_mapping[(target_file, target_col)] = f"{target_file_name}_{target_col}"
        
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
        
        # Step 2: Get all column names from all files and get the union set
        all_columns = set()
        for df in file_data.values():
            all_columns.update(df.columns)
        
        print(f"Union of all columns: {list(all_columns)}")
        
        # Step 3: Merge all files and keep unique columns in the union set
        # When there are common columns, keep the columns from the first file only
        merged_df = None
        file_order = list(unique_files)
        
        print(f"File order: {file_order}")
        
        for i, file_path in enumerate(file_order):
            df = file_data[file_path].copy()
            file_name = os.path.splitext(os.path.basename(file_path))[0]
            
            print(f"Processing file {i+1}: {file_name}")
            print(f"Original columns: {list(df.columns)}")
            
            # Rename comparison columns for this file using file-specific mapping
            rename_mapping = {}
            for (file_path_key, orig_col), renamed_col in file_col_mapping.items():
                if file_path_key == file_path and orig_col in df.columns:
                    rename_mapping[orig_col] = renamed_col
            
            # Apply renaming
            if rename_mapping:
                df = df.rename(columns=rename_mapping)
                print(f"Renamed columns for {file_name}: {rename_mapping}")
            
            if merged_df is None:
                # First file - start with all columns from this file
                merged_df = df
            else:
                # Subsequent files - merge on ID column, keeping unique columns
                # For common columns, keep from the first file (merged_df)
                common_cols = set(merged_df.columns).intersection(set(df.columns)) - {id_column}
                
                # Remove common columns from the current file before merge
                df_filtered = df.drop(columns=list(common_cols))
                
                # Merge with existing dataframe
                merged_df = pd.merge(
                    merged_df,
                    df_filtered,
                    on=id_column,
                    how='inner'
                )
        
        print(f"Merged data: {len(merged_df)} rows")
        print(f"Merged columns: {list(merged_df.columns)}")
        
        # Step 4: Calculate differences for each comparison item specified in the mapping file
        comparison_data = {}
        
        for _, mapping_row in mapping_df.iterrows():
            item_name = mapping_row['Item']
            benchmark_file = mapping_row['Benchmark File']
            benchmark_col = mapping_row['Benchmark Column']
            target_file = mapping_row['Target File']
            target_col = mapping_row['Target Column']
            
            print(f"Processing {item_name}: {benchmark_file} -> {benchmark_col} vs {target_file} -> {target_col}")
            
            # Get the renamed column names
            benchmark_file_name = os.path.splitext(os.path.basename(benchmark_file))[0]
            target_file_name = os.path.splitext(os.path.basename(target_file))[0]
            
            benchmark_col_actual = f"{benchmark_file_name}_{benchmark_col}"
            target_col_actual = f"{target_file_name}_{target_col}"
            
            # Calculate percentage difference: (target / benchmark - 1) using Pandas
            diff_col_name = f"diff_{benchmark_col}"
            
            merged_df[diff_col_name] = (merged_df[target_col_actual] / merged_df[benchmark_col_actual] - 1)
            
            # Handle division by zero (infinity values)
            merged_df[diff_col_name] = merged_df[diff_col_name].replace([float('inf'), float('-inf')], None)
            
            print(f"Calculated differences for {benchmark_col}")
            
            # Store the difference column name for this comparison
            comparison_data[item_name] = diff_col_name
        
        print(f"Final merged data columns: {list(merged_df.columns)}")
        return merged_df, comparison_data

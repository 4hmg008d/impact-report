"""
Analysis module for impact analysis tool using Pandas
"""

import pandas as pd
from typing import Dict, List, Tuple
import json


class DataAnalyser:
    """Analyzes data and generates insights using Pandas"""
    
    def __init__(self, config_loader):
        self.config_loader = config_loader
    
    def map_to_bands(self, merged_df: pd.DataFrame, value_col: str, band_df: pd.DataFrame) -> pd.DataFrame:
        """Map differences to bands and count frequencies using Pandas"""
        # Create band mapping function
        # Use merge approach for better performance
        merged_df = merged_df.copy()  # Create a copy to avoid modifying a slice
        
        # Create bins from band_df
        bins = band_df['From'].dropna().tolist() + [float('inf')]
        labels = band_df['Name'].dropna().tolist()
        
        # Map values to bands using pd.cut, handling missing values
        merged_df['band'] = pd.cut(
            merged_df[value_col],
            bins=bins,
            labels=labels,
            right=False,
            include_lowest=True
        ).astype(str)
        
        # Replace 'nan' string with appropriate labels
        # Use a mask to identify 'nan' entries and replace them appropriately
        nan_mask = merged_df['band'] == 'nan'
        merged_df.loc[nan_mask, 'band'] = merged_df.loc[nan_mask, value_col].apply(
            lambda x: "Missing" if pd.isna(x) else "Out of Range"
        )
        
        # Count frequencies by band using Pandas
        total_count = len(merged_df)
        band_summary = merged_df.groupby('band').size().reset_index(name='Count')
        band_summary['Percentage'] = (band_summary['Count'] / total_count * 100).round(2)
        
        # Get the original band order from configuration
        band_order = self.config_loader.load_band_data()['Name'].tolist()
        
        # Reorder band_summary to match the original band order
        # Create a mapping from band name to row data
        band_map = {row['band']: row for _, row in band_summary.iterrows()}
        
        # Create ordered list of ALL bands from configuration, including those with 0 count
        ordered_bands = []
        for band_name in band_order:
            if band_name in band_map:
                # Band has data, use existing row
                ordered_bands.append(band_map[band_name])
            else:
                # Band has no data, create row with 0 count and 0% percentage
                ordered_bands.append({
                    'band': band_name,
                    'Count': 0,
                    'Percentage': 0.0
                })
        
        # Add any remaining bands that weren't in the original order but have data
        for band_name in band_summary['band']:
            if band_name not in band_order and band_name not in [b['band'] for b in ordered_bands]:
                ordered_bands.append(band_map[band_name])
        
        # Convert back to DataFrame
        band_summary_ordered = pd.DataFrame(ordered_bands)
        
        print(f"Mapped differences to {len(band_summary_ordered)} bands")
        return band_summary_ordered
    
    def generate_distribution_summary(self, merged_df: pd.DataFrame, comparison_mapping: Dict[str, Dict]) -> Dict:
        """Generate comprehensive analysis for multiple comparison items using Pandas"""
        band_df = self.config_loader.load_band_data()
        
        # Process each comparison item
        dict_distribution_summary = {}
        
        for item_name, item_data in comparison_mapping.items():
            print(f"Assessing {item_name} Impact...")
            
            # Initialize item analysis
            dict_distribution_summary[item_name] = {
                'steps': {},
                'step_names': item_data['step_names']
            }
            
            # Process each difference column (step comparison)
            if 'differences' in item_data:
                # Sort steps to ensure step 0 (Overall) comes first
                sorted_steps = sorted(item_data['differences'].keys())
                
                for step_num in sorted_steps:
                    diff_info = item_data['differences'][step_num]
                    diff_col = diff_info['percent_diff_column']
                    step_name = item_data['step_names'][step_num]
                    
                    # Band distribution for this step comparison
                    summary_by_band = self.map_to_bands(merged_df, diff_col, band_df)
                    
                    # Prepare chart data for this step comparison
                    step_chart_data = []
                    for _, band_row in summary_by_band.iterrows():
                        step_chart_data.append({
                            'name': band_row['band'],
                            'y': int(band_row['Count']),
                            'percentage': round(band_row['Percentage'], 2)
                        })
                    
                    dict_distribution_summary[item_name]['steps'][step_num] = {
                        'step_name': step_name,
                        'percent_diff_column': diff_col,
                        'chart_data': step_chart_data,
                        'total_policies': len(merged_df),
                        'summary_by_band': summary_by_band.to_dict('records'),
                        'from_stage': diff_info['from_stage'],
                        'to_stage': diff_info['to_stage']
                    }
            
            # Also store column information for summary calculations
            dict_distribution_summary[item_name]['columns'] = item_data['columns']
        
        return dict_distribution_summary


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
                value_total_percent = value_total / value_total_first_stage
                
                # Calculate the difference for this stage
                if idx == 0:
                    value_diff = 0  # First stage has no difference
                    value_diff_percent = 0
                else:
                    prev_stage = sorted_stages[idx - 1]
                    prev_col_name = item_dict['columns'][prev_stage]
                    value_diff = value_total - summary_data[prev_col_name].sum()
                    value_diff_percent = value_diff / value_total_first_stage

                dict_comparison_summary[item_name][idx] = {
                    'stage_name': stage_name,
                    'value_total': value_total,
                    'value_diff': value_diff,
                    'value_total_percent': value_total_percent,
                    'value_diff_percent': value_diff_percent
                }

        return dict_comparison_summary

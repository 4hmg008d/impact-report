"""
Analysis module for impact analysis tool using Pandas
"""

import pandas as pd
from typing import Dict, List, Tuple
import json
import logging

logger = logging.getLogger(__name__)


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
                ordered_bands.append(pd.Series({
                    'band': band_name,
                    'Count': 0,
                    'Percentage': 0.0
                }))
        
        # Add any remaining bands that weren't in the original order but have data
        for band_name in band_summary['band']:
            if band_name not in band_order and band_name not in [b['band'] for b in ordered_bands]:
                ordered_bands.append(band_map[band_name])
        
        # Convert back to DataFrame
        band_summary_ordered = pd.DataFrame(ordered_bands)
        
        return band_summary_ordered
    
    def generate_distribution_summary(self, merged_df: pd.DataFrame, comparison_mapping: Dict[str, Dict]) -> Dict:
        """Generate comprehensive analysis for multiple comparison items using Pandas
        
        If renewal feature is enabled, generates separate distributions for New Business and Renewal segments.
        """
        band_df = self.config_loader.load_band_data()
        
        # Check if renewal is enabled
        is_renewal_enabled = any(item_data.get('renewal_enabled', False) for item_data in comparison_mapping.values())
        
        # Process each comparison item
        dict_distribution_summary = {}
        
        for item_name, item_data in comparison_mapping.items():
            logger.info(f"Assessing {item_name} Impact...")
            
            # Initialize item analysis
            dict_distribution_summary[item_name] = {
                'steps': {},
                'step_names': item_data['step_names'],
                'renewal_enabled': item_data.get('renewal_enabled', False)
            }
            
            # Process each difference column (step comparison)
            if 'differences' in item_data:
                # Sort steps to ensure step 0 (Overall) comes first
                sorted_steps = sorted(item_data['differences'].keys())
                
                for step_num in sorted_steps:
                    diff_info = item_data['differences'][step_num]
                    diff_col = diff_info['percent_diff_column']
                    step_name = item_data['step_names'][step_num]
                    
                    # Band distribution for this step comparison (New Business)
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
                    
                    # If renewal is enabled, also calculate renewal distribution
                    if item_data.get('renewal_enabled', False) and 'renewal_differences' in item_data:
                        if step_num in item_data['renewal_differences']:
                            rn_diff_info = item_data['renewal_differences'][step_num]
                            rn_diff_col = rn_diff_info['percent_diff_column']
                            
                            # Band distribution for renewal
                            rn_summary_by_band = self.map_to_bands(merged_df, rn_diff_col, band_df)
                            
                            # Prepare renewal chart data
                            rn_step_chart_data = []
                            for _, band_row in rn_summary_by_band.iterrows():
                                rn_step_chart_data.append({
                                    'name': band_row['band'],
                                    'y': int(band_row['Count']),
                                    'percentage': round(band_row['Percentage'], 2)
                                })
                            
                            # Store renewal data alongside main data
                            dict_distribution_summary[item_name]['steps'][step_num]['renewal_chart_data'] = rn_step_chart_data
                            dict_distribution_summary[item_name]['steps'][step_num]['renewal_summary_by_band'] = rn_summary_by_band.to_dict('records')
                            dict_distribution_summary[item_name]['steps'][step_num]['renewal_percent_diff_column'] = rn_diff_col
            
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

    def aggregate_impact_breakdown(
        self, 
        merged_df: pd.DataFrame, 
        comparison_mapping: Dict[str, Dict],
        breakdown_columns: List[str]
    ) -> Dict[str, pd.DataFrame]:
        """Generate breakdown analysis by specified dimensions with subtotals
        
        Args:
            merged_df: The merged dataframe containing all data rows
            comparison_mapping: Mapping containing stage information for each item
            breakdown_columns: List of columns to break down by (max 3)
            
        Returns:
            Dict mapping item names to their breakdown DataFrames
        """
        # Validate breakdown columns length
        if len(breakdown_columns) > 3:
            logger.warning(f"Maximum 3 breakdown columns allowed. Truncating from {len(breakdown_columns)} to 3.")
            breakdown_columns = breakdown_columns[:3]
        
        if len(breakdown_columns) == 0:
            logger.warning("No breakdown columns provided. Returning empty dict.")
            return {}
        
        # Filter out columns that don't exist in the DataFrame
        valid_breakdown_columns = [col for col in breakdown_columns if col in merged_df.columns]
        if len(valid_breakdown_columns) < len(breakdown_columns):
            missing_cols = set(breakdown_columns) - set(valid_breakdown_columns)
            logger.warning(f"Columns {missing_cols} not found in data. Using only: {valid_breakdown_columns}")
            breakdown_columns = valid_breakdown_columns
        
        if len(breakdown_columns) == 0:
            logger.warning("No valid breakdown columns found in data. Returning empty dict.")
            return {}
        
        breakdown_results = {}
        
        for item_name, item_dict in comparison_mapping.items():
            # Get first and last stage columns
            sorted_stages = sorted(item_dict['stages'].keys())
            first_stage = sorted_stages[0]
            last_stage = sorted_stages[-1]
            
            first_stage_col = item_dict['columns'][first_stage]
            last_stage_col = item_dict['columns'][last_stage]
            
            # Check if columns exist in the dataframe
            if first_stage_col not in merged_df.columns or last_stage_col not in merged_df.columns:
                logger.warning(f"Columns {first_stage_col} or {last_stage_col} not found for {item_name}. Skipping.")
                continue
            
            # Group by breakdown columns and calculate aggregates
            agg_dict = {
                first_stage_col: 'sum',
                last_stage_col: 'sum'
            }
            
            grouped = merged_df.groupby(breakdown_columns, dropna=False).agg(agg_dict)
            grouped['policy_count'] = merged_df.groupby(breakdown_columns, dropna=False).size()
            grouped = grouped.reset_index()
            
            # Rename columns for clarity
            grouped = grouped.rename(columns={
                first_stage_col: 'value_total_start',
                last_stage_col: 'value_total_end'
            })
            
            # Calculate differences
            grouped['value_diff'] = grouped['value_total_end'] - grouped['value_total_start']
            grouped['value_diff_percent'] = grouped.apply(
                lambda row: (row['value_diff'] / row['value_total_start'] * 100) if row['value_total_start'] != 0 else 0,
                axis=1
            )
            
            # Sort by breakdown columns
            grouped = grouped.sort_values(by=breakdown_columns).reset_index(drop=True)
            
            breakdown_results[item_name] = grouped
        
        return breakdown_results

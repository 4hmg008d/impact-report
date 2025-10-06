"""
Analysis module for impact analysis tool using Pandas
"""

import pandas as pd
from typing import Dict, List, Tuple
import json


class ImpactAnalyzer:
    """Analyzes data and generates insights using Pandas"""
    
    def __init__(self, config_loader):
        self.config_loader = config_loader
    
    def map_to_bands(self, merged_df: pd.DataFrame, value_col: str, band_df: pd.DataFrame) -> pd.DataFrame:
        """Map differences to bands and count frequencies using Pandas"""
        # Create band mapping function
        def map_to_band(value):
            if pd.isna(value):
                return "Missing"
            
            for _, band_row in band_df.iterrows():
                from_val = band_row['From']
                to_val = band_row['To']
                band_name = band_row['Name']
                
                # Handle infinity values
                if pd.isna(to_val) and value >= from_val:
                    return band_name
                elif from_val <= value < to_val:
                    return band_name
            
            return "Out of Range"
        
        # Apply band mapping using Pandas with .loc to avoid SettingWithCopyWarning
        merged_df = merged_df.copy()  # Create a copy to avoid modifying a slice
        merged_df.loc[:, 'band'] = merged_df[value_col].apply(map_to_band)
        
        # Count frequencies by band using Pandas
        total_count = len(merged_df)
        band_summary = merged_df.groupby('band').size().reset_index(name='Count')
        band_summary['Percentage'] = (band_summary['Count'] / total_count * 100).round(2)
        
        # Get the original band order from configuration
        band_order = self.config_loader.load_band_data()['Name'].tolist()
        
        # Reorder band_summary to match the original band order
        # Create a mapping from band name to row data
        band_map = {row['band']: row for _, row in band_summary.iterrows()}
        
        # Create ordered list of bands that exist in the data
        ordered_bands = []
        for band_name in band_order:
            if band_name in band_map:
                ordered_bands.append(band_map[band_name])
        
        # Add any remaining bands that weren't in the original order but have data
        for band_name in band_summary['band']:
            if band_name not in band_order and band_name not in [b['band'] for b in ordered_bands]:
                ordered_bands.append(band_map[band_name])
        
        # Convert back to DataFrame
        band_summary_ordered = pd.DataFrame(ordered_bands)
        
        print(f"Mapped differences to {len(band_summary_ordered)} bands")
        return band_summary_ordered
    
    def get_segment_values(self, merged_df: pd.DataFrame, segment_col: str) -> List[str]:
        """Get unique values for a segment column using Pandas"""
        if segment_col in merged_df.columns:
            unique_values = merged_df[segment_col].dropna().unique().tolist()
            return [str(val) for val in unique_values]
        return []
    
    def create_summary_by_band_segment(
        self, merged_df: pd.DataFrame, value_col: str, 
        band_df: pd.DataFrame, segments: List[str]
    ) -> Dict[str, List]:
        """Create data for segment-based tabs using Pandas"""
        tab_data = {}
        
        for segment in segments:
            # Find matching segment columns (handle benchmark/target variations)
            segment_cols = [col for col in merged_df.columns if segment in col]
            
            if segment_cols:
                segment_col = segment_cols[0]  # Use first matching column
                unique_values = self.get_segment_values(merged_df, segment_col)
                
                for value in unique_values:
                    # Filter data for this segment value
                    filtered_df = merged_df[merged_df[segment_col] == value]
                    
                    if len(filtered_df) > 0:
                        # Map to bands for filtered data
                        band_summary = self.map_to_bands(filtered_df, value_col, band_df)
                        
                        # Prepare chart data
                        chart_data = []
                        for _, band_row in band_summary.iterrows():
                            chart_data.append({
                                'name': band_row['band'],
                                'y': int(band_row['Count']),
                                'percentage': round(band_row['Percentage'], 2)
                            })
                        
                        tab_name = f"{segment}: {value}"
                        tab_data[tab_name] = {
                            'chart_data': chart_data,
                            'total_policies': len(filtered_df),
                            'segment_value': value
                        }
        
        return tab_data
    
    def generate_distribution_summary(self, merged_df: pd.DataFrame, comparison_mapping: Dict[str, Dict]) -> Dict:
        """Generate comprehensive segment analysis for multiple comparison items using Pandas"""
        band_df = self.config_loader.load_band_data()
        segments = self.config_loader.load_segment_data()
        
        # Process each comparison item
        comparison_analysis = {}
        
        for item_name, item_data in comparison_mapping.items():
            print(f"Assessing {item_name} Impact...")
            
            # Initialize item analysis
            comparison_analysis[item_name] = {
                'steps': {},
                'step_names': item_data['step_names'],
                'segments_available': len(segments) > 0
            }
            
            # Process each difference column (step comparison)
            if 'differences' in item_data:
                # Sort steps to ensure step 0 (All Steps) comes first
                sorted_steps = sorted(item_data['differences'].keys())
                
                for step in sorted_steps:
                    diff_info = item_data['differences'][step]
                    diff_col = diff_info['percent_diff_column']
                    step_name = item_data['step_names'][step]
                    
                    # Band distribution for this step comparison
                    summary_by_band = self.map_to_bands(merged_df, diff_col, band_df)
                    
                    # Segment-based tab data for this step comparison
                    summary_by_band_segment = self.create_summary_by_band_segment(merged_df, diff_col, band_df, segments)
                    
                    # Prepare chart data for this step comparison
                    step_chart_data = []
                    for _, band_row in summary_by_band.iterrows():
                        step_chart_data.append({
                            'name': band_row['band'],
                            'y': int(band_row['Count']),
                            'percentage': round(band_row['Percentage'], 2)
                        })
                    
                    comparison_analysis[item_name]['steps'][step] = {
                        'step_name': step_name,
                        'percent_diff_column': diff_col,
                        'chart_data': step_chart_data,
                        'total_policies': len(merged_df),
                        'summary_by_band': summary_by_band.to_dict('records'),
                        'summary_by_band_segment': summary_by_band_segment,
                        'from_step': diff_info['from_step'],
                        'to_step': diff_info['to_step']
                    }
            
            # Also store column information for summary calculations
            comparison_analysis[item_name]['columns'] = item_data['columns']
        
        return comparison_analysis
    
    def generate_summary_table(self, merged_df: pd.DataFrame, comparison_mapping: Dict[str, Dict]) -> pd.DataFrame:
        """Generate summary table with total values by item and steps, with percentage differences
        
        Args:
            merged_df: The merged dataframe containing all data
            comparison_mapping: Mapping containing step and difference information
            
        Returns:
            DataFrame with summary table containing:
            - Item column (rows)
            - Step columns with total values
            - Percentage difference columns for each step (recalculated based on aggregated totals)
            - All Steps percentage difference at the very right
        """
        summary_data = []
        
        # Get all items from comparison_mapping
        items = list(comparison_mapping.keys())
        
        for item_name in items:
            item_data = comparison_mapping[item_name]
            row_data = {'Item': item_name}
            
            # Dictionary to store total values for each step (for percentage calculation)
            step_totals = {}
            
            # Get step columns for this item (original values)
            if 'steps' in item_data:
                steps = sorted(item_data['steps'].keys())
                
                # Add step columns with total values using renamed_column
                for step in steps:
                    step_info = item_data['steps'][step]
                    step_col = step_info['renamed_column']
                    step_name = step_info['step_name']
                    
                    if step_col in merged_df.columns:
                        total_value = merged_df[step_col].sum()
                        row_data[f'{step_name}'] = total_value
                        step_totals[step] = total_value
            
            # Calculate and add percentage difference columns based on aggregated totals
            if 'differences' in item_data and 'steps' in item_data:
                diff_steps = sorted(item_data['differences'].keys())
                
                # Separate "All Steps" from other steps
                all_steps_diff = None
                other_diffs = []
                
                for diff_step in diff_steps:
                    diff_info = item_data['differences'][diff_step]
                    from_step = diff_info['from_step']
                    to_step = diff_info['to_step']
                    
                    # Get total values for from_step and to_step
                    from_total = step_totals.get(from_step, 0)
                    to_total = step_totals.get(to_step, 0)
                    
                    # Calculate percentage difference based on aggregated totals
                    if from_total != 0:
                        percent_diff = ((to_total - from_total) / from_total) * 100
                    else:
                        percent_diff = None
                    
                    # Use naming convention: percent_diff_step_{curr_step}
                    if diff_step == 1 and item_data.get('step_names', {}).get(1) == 'All Steps':
                        # This is the "All Steps" comparison - save for later
                        col_name = f'percent_diff_step_all'
                        all_steps_diff = (col_name, percent_diff)
                    else:
                        # Regular step-to-step comparison
                        col_name = f'percent_diff_step_{to_step}'
                        other_diffs.append((col_name, percent_diff))
                
                # Add other diffs first
                for col_name, value in other_diffs:
                    row_data[col_name] = value
                
                # Add "All Steps" diff last (if it exists)
                if all_steps_diff:
                    row_data[all_steps_diff[0]] = all_steps_diff[1]
            
            summary_data.append(row_data)
        
        # Create summary DataFrame
        summary_df = pd.DataFrame(summary_data)
        
        # Reorder columns to ensure proper grouping:
        # Item, Step columns, percentage diff columns (regular), All Steps column
        if not summary_df.empty:
            cols = list(summary_df.columns)
            item_col = ['Item']
            step_cols = [col for col in cols if col not in item_col and not col.startswith('percent_diff_')]
            percent_diff_cols = [col for col in cols if col.startswith('percent_diff_') and 'step_all' not in col]
            all_steps_col = [col for col in cols if 'step_all' in col]
            
            # Reorder: Item, Step columns, percentage diff columns, All Steps column
            ordered_cols = item_col + step_cols + percent_diff_cols + all_steps_col
            summary_df = summary_df[ordered_cols]
        
        return summary_df

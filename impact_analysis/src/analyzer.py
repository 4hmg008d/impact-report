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
    
    def map_to_bands(self, merged_df: pd.DataFrame, diff_col: str, band_df: pd.DataFrame) -> pd.DataFrame:
        """Map differences to bands and count frequencies using Pandas"""
        # Create band mapping function
        def map_to_band(diff_value):
            if pd.isna(diff_value):
                return "Missing"
            
            for _, band_row in band_df.iterrows():
                from_val = band_row['From']
                to_val = band_row['To']
                band_name = band_row['Name']
                
                # Handle infinity values
                if pd.isna(to_val) and diff_value >= from_val:
                    return band_name
                elif from_val <= diff_value < to_val:
                    return band_name
            
            return "Out of Range"
        
        # Apply band mapping using Pandas with .loc to avoid SettingWithCopyWarning
        merged_df = merged_df.copy()  # Create a copy to avoid modifying a slice
        merged_df.loc[:, 'band'] = merged_df[diff_col].apply(map_to_band)
        
        # Count frequencies by band using Pandas
        total_count = len(merged_df)
        band_counts = merged_df.groupby('band').size().reset_index(name='Count')
        band_counts['Percentage'] = (band_counts['Count'] / total_count * 100).round(2)
        
        # Get the original band order from configuration
        band_order = self.config_loader.load_band_data()['Name'].tolist()
        
        # Reorder band_counts to match the original band order
        # Create a mapping from band name to row data
        band_map = {row['band']: row for _, row in band_counts.iterrows()}
        
        # Create ordered list of bands that exist in the data
        ordered_bands = []
        for band_name in band_order:
            if band_name in band_map:
                ordered_bands.append(band_map[band_name])
        
        # Add any remaining bands that weren't in the original order but have data
        for band_name in band_counts['band']:
            if band_name not in band_order and band_name not in [b['band'] for b in ordered_bands]:
                ordered_bands.append(band_map[band_name])
        
        # Convert back to DataFrame
        band_counts_ordered = pd.DataFrame(ordered_bands)
        
        print(f"Mapped differences to {len(band_counts_ordered)} bands")
        return band_counts_ordered
    
    def get_segment_values(self, merged_df: pd.DataFrame, segment_col: str) -> List[str]:
        """Get unique values for a segment column using Pandas"""
        if segment_col in merged_df.columns:
            unique_values = merged_df[segment_col].dropna().unique().tolist()
            return [str(val) for val in unique_values]
        return []
    
    def create_segment_tabs_data(
        self, merged_df: pd.DataFrame, diff_col: str, 
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
                        band_counts = self.map_to_bands(filtered_df, diff_col, band_df)
                        
                        # Prepare chart data
                        chart_data = []
                        for _, band_row in band_counts.iterrows():
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
    
    def generate_segment_analysis(self, merged_df: pd.DataFrame, comparison_data: Dict[str, Dict]) -> Dict:
        """Generate comprehensive segment analysis for multiple comparison items using Pandas"""
        band_df = self.config_loader.load_band_data()
        segments = self.config_loader.load_segment_data()
        
        # Process each comparison item
        comparison_analysis = {}
        
        for item_name, item_data in comparison_data.items():
            print(f"Analyzing {item_name} with data structure: {list(item_data.keys())}")
            
            # Initialize item analysis
            comparison_analysis[item_name] = {
                'steps': {},
                'step_names': item_data['step_names'],
                'segments_available': len(segments) > 0
            }
            
            # Process each difference column (step comparison)
            if 'differences' in item_data:
                for step, diff_info in item_data['differences'].items():
                    diff_col = diff_info['diff_column']
                    step_name = item_data['step_names'][step]
                    
                    print(f"Processing {item_name} step {step} ({step_name}) with column {diff_col}")
                    
                    # Band distribution for this step comparison
                    step_band_counts = self.map_to_bands(merged_df, diff_col, band_df)
                    
                    # Segment-based tab data for this step comparison
                    segment_tabs_data = self.create_segment_tabs_data(merged_df, diff_col, band_df, segments)
                    
                    # Prepare chart data for this step comparison
                    step_chart_data = []
                    for _, band_row in step_band_counts.iterrows():
                        step_chart_data.append({
                            'name': band_row['band'],
                            'y': int(band_row['Count']),
                            'percentage': round(band_row['Percentage'], 2)
                        })
                    
                    comparison_analysis[item_name]['steps'][step] = {
                        'step_name': step_name,
                        'diff_column': diff_col,
                        'chart_data': step_chart_data,
                        'total_policies': len(merged_df),
                        'band_counts': step_band_counts.to_dict('records'),
                        'segment_tabs': segment_tabs_data,
                        'from_step': diff_info['from_step'],
                        'to_step': diff_info['to_step']
                    }
            
            # Also store column information for summary calculations
            comparison_analysis[item_name]['columns'] = item_data['columns']
        
        return comparison_analysis

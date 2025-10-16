"""
Dashboard state management module for Impact Analysis Dashboard
Manages in-memory data storage to avoid reloading when applying filters
"""

import pandas as pd
from typing import Dict, Optional, List
import yaml
import os


class DashboardState:
    """Manages the state of the dashboard including data, config, and results"""
    
    def __init__(self):
        self.merged_df: Optional[pd.DataFrame] = None
        self.comparison_mapping: Optional[Dict] = None
        self.dict_distribution_summary: Optional[Dict] = None
        self.dict_comparison_summary: Optional[Dict] = None
        self.config_yaml: Optional[Dict] = None
        self.config_path: Optional[str] = None
        self.filter_columns: List[str] = []
        self.active_filters: Dict[str, List] = {}
        
    def set_config(self, config_yaml: Dict, config_path: str):
        """Store configuration data"""
        self.config_yaml = config_yaml
        self.config_path = config_path
        # Extract filter columns from config
        self.filter_columns = config_yaml.get('filter', [])
        # Initialize active filters (all values selected by default)
        self.active_filters = {col: [] for col in self.filter_columns}
    
    def set_data(self, merged_df: pd.DataFrame, comparison_mapping: Dict):
        """Store merged data and comparison mapping"""
        self.merged_df = merged_df
        self.comparison_mapping = comparison_mapping
    
    def set_results(self, dict_distribution_summary: Dict, dict_comparison_summary: Dict):
        """Store analysis results"""
        self.dict_distribution_summary = dict_distribution_summary
        self.dict_comparison_summary = dict_comparison_summary
    
    def get_filtered_data(self) -> pd.DataFrame:
        """Get filtered data based on active filters"""
        if self.merged_df is None:
            return None
        
        filtered_df = self.merged_df.copy()
        
        # Apply each active filter
        for col, values in self.active_filters.items():
            if values and len(values) > 0 and col in filtered_df.columns:
                # Convert boolean columns to string for comparison
                # This handles the case where Excel reads "True"/"False" as bool
                if filtered_df[col].dtype == 'bool':
                    col_for_comparison = filtered_df[col].astype(str)
                else:
                    col_for_comparison = filtered_df[col]
                
                # Check if 'NA' is in the filter values
                if 'NA' in values:
                    # Create a mask for non-NA values that match the filter
                    other_values = [v for v in values if v != 'NA']
                    if other_values:
                        # Include rows where column is NA OR matches other filter values
                        mask = filtered_df[col].isna() | col_for_comparison.isin(other_values)
                    else:
                        # Only NA is selected
                        mask = filtered_df[col].isna()
                    filtered_df = filtered_df[mask]
                else:
                    # Filter to include only selected values (exclude NA)
                    filtered_df = filtered_df[col_for_comparison.isin(values)]
        
        return filtered_df
    
    def get_unique_values_for_filter(self, column: str) -> List:
        """Get unique values for a filter column from the merged data, including NA as a separate level"""
        if self.merged_df is None or column not in self.merged_df.columns:
            return []
        
        # Get unique non-NA values
        unique_vals = self.merged_df[column].dropna().unique().tolist()
        unique_vals_str = sorted([str(val) for val in unique_vals])
        
        # Check if there are any NA values in the column
        has_na = self.merged_df[column].isna().any()
        
        # Add NA as a separate level if it exists
        if has_na:
            unique_vals_str.append('NA')
        
        return unique_vals_str
    
    def update_filters(self, filter_updates: Dict[str, List]):
        """Update active filters"""
        self.active_filters.update(filter_updates)
    
    def has_data(self) -> bool:
        """Check if data has been loaded"""
        return self.merged_df is not None
    
    def clear_results(self):
        """Clear stored results (but keep data)"""
        self.dict_distribution_summary = None
        self.dict_comparison_summary = None
    
    def get_config_as_yaml_string(self) -> str:
        """Get current configuration as YAML string for display/editing"""
        if self.config_yaml is None:
            return ""
        return yaml.dump(self.config_yaml, default_flow_style=False, sort_keys=False)
    
    def update_config_from_yaml_string(self, yaml_string: str) -> tuple[bool, str]:
        """
        Update configuration from YAML string
        Returns: (success: bool, message: str)
        """
        try:
            new_config = yaml.safe_load(yaml_string)
            self.config_yaml = new_config
            
            # Update filter columns
            self.filter_columns = new_config.get('filter', [])
            
            # Reset active filters for new columns
            self.active_filters = {col: [] for col in self.filter_columns}
            
            return True, "Configuration updated successfully"
        except Exception as e:
            return False, f"Error parsing YAML: {str(e)}"
    
    def save_config_to_file(self) -> tuple[bool, str]:
        """
        Save current configuration back to the YAML file
        Returns: (success: bool, message: str)
        """
        if self.config_path is None:
            return False, "No config path set"
        
        try:
            with open(self.config_path, 'w') as f:
                yaml.dump(self.config_yaml, f, default_flow_style=False, sort_keys=False)
            return True, f"Configuration saved to {self.config_path}"
        except Exception as e:
            return False, f"Error saving configuration: {str(e)}"


# Global state instance
dashboard_state = DashboardState()

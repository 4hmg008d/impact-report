"""
Configuration loader for impact analysis tool
"""

import yaml
import pandas as pd
from typing import Dict, Any, List
import os


class ConfigLoader:
    """Loads and validates configuration for impact analysis"""
    
    def __init__(self, config_path: str = "config_impact_analysis.yaml"):
        self.config_path = config_path
        # Store the directory containing the config file for resolving relative paths
        self.config_dir = os.path.dirname(os.path.abspath(config_path))
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        
        with open(self.config_path, 'r') as file:
            return yaml.safe_load(file)
    
    def _abs_path(self, path: str) -> str:
        """Resolve relative paths relative to the config file directory"""
        if os.path.isabs(path):
            return path
        else:
            return os.path.join(self.config_dir, path)
    
    def load_mapping_data(self) -> pd.DataFrame:
        """Load mapping data from Excel file"""
        mapping_config = self.config['mapping']
        mapping_file_path = self._abs_path(mapping_config['file_path'])
        sheet_name = mapping_config['sheet_input']
        
        try:
            mapping_df = pd.read_excel(mapping_file_path, sheet_name=sheet_name)
            return mapping_df
        except Exception as e:
            raise ValueError(f"Failed to load mapping file: {e}")
    
    def load_band_data(self) -> pd.DataFrame:
        """Load band mapping from Excel file"""
        mapping_config = self.config['mapping']
        mapping_file_path = self._abs_path(mapping_config['file_path'])
        sheet_name = mapping_config['sheet_band']
        
        try:
            band_df = pd.read_excel(mapping_file_path, sheet_name=sheet_name)
            return band_df
        except Exception as e:
            raise ValueError(f"Failed to load band data: {e}")
    
    def get_output_dir(self) -> str:
        """Get output directory from configuration"""
        return self._abs_path(self.config['output']['dir'])

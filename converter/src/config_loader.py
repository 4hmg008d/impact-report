"""
Configuration loader for data conversion tool
"""

import yaml
import os
from typing import Dict, Any


class ConverterConfigLoader:
    """Loads and validates configuration for data conversion"""
    
    def __init__(self, config_path: str = "config_data_conversion.yaml"):
        self.config_path = config_path
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        
        with open(self.config_path, 'r') as file:
            return yaml.safe_load(file)
    
    def get_input_config(self) -> Dict[str, Any]:
        """Get input configuration"""
        return self.config.get('input', {})
    
    def get_output_config(self) -> Dict[str, Any]:
        """Get output configuration"""
        return self.config.get('output', {})
    
    def get_mapping_config(self) -> Dict[str, Any]:
        """Get mapping configuration"""
        return self.config.get('mapping', {})
    
    def get_processing_config(self) -> Dict[str, Any]:
        """Get processing configuration"""
        return self.config.get('processing', {})

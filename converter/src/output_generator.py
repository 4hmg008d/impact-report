"""
Output generator module for data conversion tool using Pandas
"""

import pandas as pd
import os
from typing import Dict, Any


class OutputGenerator:
    """Generates and saves output files using Pandas"""
    
    def __init__(self, config_loader):
        self.config_loader = config_loader
    
    def _detect_file_type(self, file_path: str) -> str:
        """Detect file type from extension"""
        ext = os.path.splitext(file_path)[1].lower()
        if ext in ['.xlsx', '.xls']:
            return 'excel'
        elif ext == '.csv':
            return 'csv'
        else:
            raise ValueError(f"Unsupported file type: {ext}")
    
    def save_output_data(self, df: pd.DataFrame, output_path: str, file_type: str = 'csv') -> None:
        """Save processed data to output file"""
        try:
            # Ensure all column names are uppercase
            df.columns = [col.upper() for col in df.columns]
            
            # Ensure output directory exists
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
            
            if file_type == 'excel':
                df.to_excel(output_path, index=False)
            elif file_type == 'csv':
                df.to_csv(output_path, index=False)
            else:
                raise ValueError(f"Unsupported output file type: {file_type}")
            
            print(f"Successfully saved output to {output_path}")
            
        except Exception as e:
            raise ValueError(f"Failed to save output file {output_path}: {e}")
    
    def generate_output(self, df: pd.DataFrame) -> None:
        """Generate output file based on configuration"""
        output_config = self.config_loader.get_output_config()
        output_file_path = output_config.get('file_path')
        output_file_type = output_config.get('file_type', 'csv')
        
        if not output_file_path:
            raise ValueError("Output file path not specified in configuration")
        
        # Auto-detect file type if not specified
        if output_file_type == 'auto':
            output_file_type = self._detect_file_type(output_file_path)
        
        self.save_output_data(df, output_file_path, output_file_type)

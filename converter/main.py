"""
Main module for modular data conversion tool using Pandas
"""

import sys
import os
import logging
from typing import Dict

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config_loader import ConverterConfigLoader
from src.mapping_processor import MappingProcessor
from src.data_loader import DataLoader
from src.data_converter import DataConverter
from src.output_generator import OutputGenerator


class ModularDataConverter:
    """Main class that orchestrates the modular data conversion process"""
    
    def __init__(self, config_path: str = "config_data_conversion.yaml"):
        self.config_path = config_path
        self.logger = self._setup_logging()
        self.config_loader = ConverterConfigLoader(config_path)
        self.mapping_processor = MappingProcessor(self.config_loader)
        self.data_loader = DataLoader(self.config_loader)
        self.data_converter = DataConverter(self.config_loader)
        self.output_generator = OutputGenerator(self.config_loader)
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler('conversion.log')
            ]
        )
        return logging.getLogger(__name__)
    
    def convert(self) -> bool:
        """Execute the complete modular data conversion process"""
        try:
            self.logger.info("Starting modular data conversion process")
            
            # Step 1: Load and process mapping rules
            mapping_result = self.mapping_processor.process_mapping()
            column_mapping = mapping_result['column_mapping']
            
            # Step 2: Load input configuration
            input_config = self.config_loader.get_input_config()
            input_file_path = input_config.get('file_path')
            input_file_type = input_config.get('file_type', 'auto')
            
            if not input_file_path:
                raise ValueError("Input file path not specified in configuration")
            
            self.logger.info(f"Input file: {input_file_path} ({input_file_type})")
            
            # Step 3: Load input data
            input_df = self.data_loader.load_input_data(input_file_path, input_file_type)
            self.logger.info(f"Loaded {len(input_df)} rows with {len(input_df.columns)} columns")
            
            # Step 4: Validate input data
            self.data_loader.validate_input_data(input_df, column_mapping)
            
            # Step 5: Convert data types
            converted_df = self.data_converter.convert_data_types(input_df, column_mapping, mapping_result.get('value_mappings', {}))
            self.logger.info(f"Converted to {len(converted_df)} rows with {len(converted_df.columns)} columns")
            
            # Step 6: Process LIST columns
            converted_df = self.data_converter.process_list_columns(converted_df, column_mapping)
            
            # Step 7: Generate output
            output_config = self.config_loader.get_output_config()
            self.logger.info(f"Output file: {output_config.get('file_path')} ({output_config.get('file_type', 'csv')})")
            self.output_generator.generate_output(converted_df)
            
            self.logger.info("Modular data conversion completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Modular data conversion failed: {e}")
            return False


def main():
    """Main function for modular data conversion tool"""
    if len(sys.argv) > 1:
        config_path = sys.argv[1]
    else:
        config_path = "config_data_conversion.yaml"
    
    converter = ModularDataConverter(config_path)
    success = converter.convert()
    
    if success:
        print("Modular data conversion completed successfully!")
        sys.exit(0)
    else:
        print("Modular data conversion failed. Check conversion.log for details.")
        sys.exit(1)


if __name__ == "__main__":
    main()

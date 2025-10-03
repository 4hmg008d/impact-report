"""
Main module for modular impact analysis tool using Pandas
"""

import sys
import os
import logging
from typing import Dict

from .src.config_loader import ConfigLoader
from .src.data_processor import DataProcessor
from .src.analyzer import ImpactAnalyzer
from .src.visualizer import ReportVisualizer


class ModularImpactAnalyzer:
    """Main class that orchestrates the modular impact analysis process"""
    
    def __init__(self, config_path: str = None):
        # If no config path provided, use default relative to this module
        if config_path is None:
            module_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(module_dir, "config_impact_analysis.yaml")
            
        self.config_path = config_path
        self.logger = self._setup_logging()
        self.config_loader = ConfigLoader(config_path)
        self.data_processor = DataProcessor(self.config_loader)
        self.analyzer = ImpactAnalyzer(self.config_loader)
        
        # Set up visualizer with correct template directory
        module_dir = os.path.dirname(os.path.abspath(__file__))
        template_dir = os.path.join(module_dir, "templates")
        self.visualizer = ReportVisualizer(self.config_loader, template_dir)
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        # Create log file in the same directory as the module
        module_dir = os.path.dirname(os.path.abspath(__file__))
        log_path = os.path.join(module_dir, 'impact_analysis.log')
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler(log_path)
            ]
        )
        return logging.getLogger(__name__)
    
    def save_output_files(self, merged_df, comparison_analysis: Dict) -> None:
        """Save all output files using Pandas"""
        output_dir = self.config_loader.get_output_dir()
        os.makedirs(output_dir, exist_ok=True)
        
        # Save merged data
        merged_output_path = os.path.join(output_dir, "merged_data.csv")
        merged_df.to_csv(merged_output_path, index=False)
        self.logger.info(f"Saved merged data to: {merged_output_path}")
        
        # Save band distribution for all comparison items and steps
        all_band_data = []
        for item_name, analysis_data in comparison_analysis.items():
            # Handle new nested structure with steps
            if 'steps' in analysis_data:
                for step, step_data in analysis_data['steps'].items():
                    step_name = step_data['step_name']
                    band_counts = step_data['band_counts']
                    if band_counts:
                        for band_row in band_counts:
                            all_band_data.append({
                                'Item': item_name,
                                'Step': step,
                                'StepName': step_name,
                                'Band': band_row['band'],
                                'Count': band_row['Count'],
                                'Percentage': band_row['Percentage']
                            })
        
        if all_band_data:
            import pandas as pd
            band_df = pd.DataFrame(all_band_data)
            band_output_path = os.path.join(output_dir, "band_distribution.csv")
            band_df.to_csv(band_output_path, index=False)
            self.logger.info(f"Saved band distribution to: {band_output_path}")
    
    def analyze(self) -> bool:
        """Execute the complete modular impact analysis process"""
        try:
            self.logger.info("Starting modular impact analysis process")
            
            # Step 1: Process data
            merged_df, comparison_data = self.data_processor.process_data()
            
            # Step 2: Analyze data for all comparison items
            comparison_analysis = self.analyzer.generate_segment_analysis(merged_df, comparison_data)
            
            # Step 3: Save output files
            self.save_output_files(merged_df, comparison_analysis)
            
            # Step 4: Generate HTML report
            output_dir = self.config_loader.get_output_dir()
            html_output_path = os.path.join(output_dir, "impact_analysis_report.html")
            self.visualizer.generate_html_report(comparison_analysis, html_output_path, merged_df)
            
            self.logger.info("Modular impact analysis completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Modular impact analysis failed: {e}")
            return False


def main():
    """Main function for modular impact analysis tool"""
    if len(sys.argv) > 1:
        config_path = sys.argv[1]
    else:
        config_path = "config_impact_analysis.yaml"
    
    analyzer = ModularImpactAnalyzer(config_path)
    success = analyzer.analyze()
    
    if success:
        print("Modular impact analysis completed successfully!")
        sys.exit(0)
    else:
        print("Modular impact analysis failed. Check impact_analysis.log for details.")
        sys.exit(1)


if __name__ == "__main__":
    main()

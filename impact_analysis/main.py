"""
Main module for modular impact analysis tool using Pandas
"""

import sys
import os
import logging
import json, pprint   # Added for pretty-printing debug info
from typing import Dict

from .src.config_loader import ConfigLoader
from .src.data_processor import DataProcessor
from .src.data_analyser import DataAnalyser
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
        self.data_analyser = DataAnalyser(self.config_loader)
        
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
    
    def save_output_files(self, merged_df, dict_distribution_summary: Dict, comparison_mapping: Dict) -> None:
        """Save all output files using Pandas"""
        import pandas as pd
        output_dir = self.config_loader.get_output_dir()
        os.makedirs(output_dir, exist_ok=True)
        
        # Save merged data
        merged_output_path = os.path.join(output_dir, "merged_data.csv")
        merged_df.to_csv(merged_output_path, index=False)
        self.logger.info(f"Saved merged data to: {merged_output_path}")
        
        # Generate and save summary table using DataAnalyser
        dict_comparison_summary = self.data_analyser.aggregate_merged_data(merged_df, comparison_mapping)

        # Debug
        # print("dict_comparison_summary:")
        # print(json.dumps(dict_comparison_summary, indent=2))

        summary_output_path = os.path.join(output_dir, "summary_table.csv")
        pd.DataFrame(dict_comparison_summary).to_csv(summary_output_path, index=False)
        self.logger.info(f"Saved summary table to: {summary_output_path}")
        
        # Save band distribution for all comparison items and steps
        all_band_summary = []
        for item_name, analysis_data in dict_distribution_summary.items():
            for step, step_data in analysis_data['steps'].items():
                step_name = step_data['step_name']
                summary_by_band = step_data['summary_by_band']
                if summary_by_band:
                    for band_row in summary_by_band:
                        all_band_summary.append({
                            'Item': item_name,
                            'Step': step,
                            'StepName': step_name,
                            'Band': band_row['band'],
                            'Count': band_row['Count'],
                            'Percentage': band_row['Percentage']
                        })
        
        if all_band_summary:
            band_df = pd.DataFrame(all_band_summary)
            band_output_path = os.path.join(output_dir, "band_distribution.csv")
            band_df.to_csv(band_output_path, index=False)
            self.logger.info(f"Saved band distribution to: {band_output_path}")
    
    def analyze(self) -> bool:
        """Execute the complete modular impact analysis process"""
        try:
            self.logger.info("Starting modular impact analysis process")
            
            # Step 1: Process data
            merged_df_w_diff, comparison_mapping = self.data_processor.process_data()
            
            # Step 2: Analyze data for all comparison items
            dict_distribution_summary = self.data_analyser.generate_distribution_summary(merged_df_w_diff, comparison_mapping)
            
            # Debug
            # print("Distribution Summary:")
            # open("impact_analysis/debug/dict_distribution_summary.json", "w").write(json.dumps(dict_distribution_summary, indent=2))
            # return True

            # Step 3: Save output files
            self.save_output_files(merged_df_w_diff, dict_distribution_summary, comparison_mapping)
            
            # Step 4: Generate HTML report
            output_dir = self.config_loader.get_output_dir()
            html_output_path = os.path.join(output_dir, "impact_analysis_report.html")
            dict_comparison_summary = self.data_analyser.aggregate_merged_data(merged_df_w_diff, comparison_mapping)

            # Generate breakdown analysis if breakdown columns are configured
            breakdown_columns = self.config_loader.get_breakdown_columns()
            breakdown_data = None
            if breakdown_columns:
                self.logger.info(f"Generating breakdown analysis for columns: {breakdown_columns}")
                breakdown_data = self.data_analyser.aggregate_impact_breakdown(
                    merged_df_w_diff, comparison_mapping, breakdown_columns
                )

            html_content = self.visualizer.generate_html_report(
                dict_distribution_summary, dict_comparison_summary, breakdown_data
            )
            self.visualizer.save_report(html_content, html_output_path)
            self.logger.info("Modular impact analysis completed successfully")
            return True
            
        except Exception as e:
            import traceback
            self.logger.error(f"Modular impact analysis failed: {e}")
            self.logger.error(traceback.format_exc())
            return False


def main():
    """Main function for modular impact analysis tool"""
    if len(sys.argv) > 1:
        config_path = sys.argv[1]
    else:
        config_path = "config_impact_analysis.yaml"
    
    data_analyser = ModularImpactAnalyzer(config_path)
    success = data_analyser.analyze()
    
    if success:
        print("Modular impact analysis completed successfully!")
        sys.exit(0)
    else:
        print("Modular impact analysis failed. Check impact_analysis.log for details.")
        sys.exit(1)


if __name__ == "__main__":
    main()

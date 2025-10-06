"""
Visualization module for impact analysis tool using Jinja2 templates
"""

import os
from typing import Dict
import pandas as pd
from jinja2 import Environment, FileSystemLoader, select_autoescape
from .chart_generator import ImpactChartGenerator
from .analyzer import ImpactAnalyzer


class ReportVisualizer:
    """Generates HTML reports using Jinja2 templates with flexible component integration"""
    
    def __init__(self, config_loader=None, template_dir="templates"):
        self.config_loader = config_loader
        self.chart_generator = ImpactChartGenerator(config_loader)
        self.analyzer = ImpactAnalyzer(config_loader) if config_loader else None
        
        # Set up Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(['html', 'xml'])
        )
        
        # Add custom filters
        self.env.filters['format_percentage'] = lambda x: f"{x:.2f}%"
    
    def generate_html_report(self, dict_distribution_summary: Dict, summary_df: pd.DataFrame, summary_comparison_mapping: Dict, output_path: str) -> None:
        """Generate HTML report for multiple comparison items using Jinja2 template"""
        


        # Generate charts for all comparison items (including waterfall charts)
        charts_html = self.chart_generator.generate_all_charts_html(dict_distribution_summary, summary_df, summary_comparison_mapping)
        

        
        # Render template with all data
        template = self.env.get_template('report_template.html')
        rendered_html = template.render(
            dict_distribution_summary=dict_distribution_summary,
            charts_html=charts_html
        )
        
        # Save HTML file
        with open(output_path, 'w') as f:
            f.write(rendered_html)
        
        print(f"Generated Jinja2 HTML report: {output_path}")
    
    def generate_report_from_components(self, merged_df: pd.DataFrame, diff_col: str, output_path: str) -> None:
        """Generate complete report by importing components from analyzer and chart_generator"""
        if not self.analyzer:
            raise ValueError("Config loader required for component-based report generation")
        
        # Generate analysis data using analyzer
        analysis_data = self.analyzer.generate_distribution_summary(merged_df, diff_col)
        
        # Generate HTML report
        self.generate_html_report(analysis_data, output_path)
    
    def generate_custom_report(self, template_name: str, context: Dict, output_path: str) -> None:
        """Generate report using a custom template with provided context"""
        template = self.env.get_template(template_name)
        rendered_html = template.render(**context)
        
        with open(output_path, 'w') as f:
            f.write(rendered_html)
        
        print(f"Generated custom report: {output_path}")
    
    def add_custom_filter(self, filter_name: str, filter_function):
        """Add a custom Jinja2 filter"""
        self.env.filters[filter_name] = filter_function
    
    def add_custom_global(self, global_name: str, global_value):
        """Add a custom Jinja2 global"""
        self.env.globals[global_name] = global_value

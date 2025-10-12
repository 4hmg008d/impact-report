"""
Visualization module for impact analysis tool using Jinja2 templates
"""

import os
from typing import Dict
import pandas as pd
from jinja2 import Environment, FileSystemLoader, select_autoescape
from .chart_generator import ImpactChartGenerator
from .data_analyser import DataAnalyser


class ReportVisualizer:
    """Generates HTML reports using Jinja2 templates with flexible component integration"""
    
    def __init__(self, config_loader=None, template_dir="templates"):
        self.config_loader = config_loader
        self.chart_generator = ImpactChartGenerator(config_loader)
        self.analyzer = DataAnalyser(config_loader) if config_loader else None
        
        # Set up Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(['html', 'xml'])
        )
        
        # Add custom filters
        self.env.filters['format_percentage'] = lambda x: f"{x:.2f}%"
    
    def generate_html_report(self, dict_distribution_summary: Dict, dict_comparison_summary: Dict) -> str:
        """Generate HTML report content for multiple comparison items using Jinja2 template
        
        Args:
            dict_distribution_summary: Summary of distribution data
            dict_comparison_summary: Summary of comparison data
            
        Returns:
            str: Rendered HTML content
        """
        
        # Generate charts for all comparison items (including waterfall charts)
        charts_html = self.chart_generator.generate_all_charts_html(dict_distribution_summary, dict_comparison_summary)
        
        # Render template with all data
        template = self.env.get_template('report_template.html')
        rendered_html = template.render(
            dict_distribution_summary=dict_distribution_summary,
            dict_comparison_summary=dict_comparison_summary,
            charts_html=charts_html
        )
        
        return rendered_html
    
    def save_report(self, html_content: str, output_path: str) -> None:
        """Save HTML report content to a file
        
        Args:
            html_content: The HTML content to save
            output_path: Path where the report should be saved
        """
        with open(output_path, 'w') as f:
            f.write(html_content)
        
        print(f"Generated Jinja2 HTML report: {output_path}")


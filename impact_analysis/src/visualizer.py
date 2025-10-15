"""
Visualization module for impact analysis tool using Jinja2 templates
"""

import os
from typing import Dict
import pandas as pd
from jinja2 import Environment, FileSystemLoader, select_autoescape
from .chart_generator import ImpactChartGenerator
from .data_analyser import DataAnalyser
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ReportVisualizer:
    """Generates HTML reports using Jinja2 templates with flexible component integration"""
    
    def __init__(self, config_loader=None, template_dir="templates"):
        self.config_loader = config_loader
        self.chart_generator = ImpactChartGenerator(config_loader)
        self.data_analyser = DataAnalyser(config_loader) if config_loader else None
        
        # Set up Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(['html', 'xml'])
        )
        
        # Add custom filters
        self.env.filters['format_percentage'] = lambda x: f"{x:.2f}%"
    
    def generate_html_report(self, dict_distribution_summary: Dict, dict_comparison_summary: Dict, breakdown_data: Dict[str, pd.DataFrame] = None) -> str:
        """Generate HTML report content for multiple comparison items using Jinja2 template
        
        Args:
            dict_distribution_summary: Summary of distribution data
            dict_comparison_summary: Summary of comparison data
            breakdown_data: Optional dict of breakdown DataFrames by item name
            
        Returns:
            str: Rendered HTML content
        """
        
        # Generate charts for all comparison items (including waterfall charts)
        charts_html = self.chart_generator.generate_all_charts_html(dict_distribution_summary, dict_comparison_summary)
        
        # Generate summary tables HTML for each item
        summary_tables_html = self.generate_summary_table_html(dict_comparison_summary)
        
        # Generate breakdown tables HTML if provided
        breakdown_tables_html = {}
        if breakdown_data:
            breakdown_tables_html = self.generate_breakdown_tables_html(breakdown_data)
        
        # Render template with all data
        template = self.env.get_template('report_template.html')
        rendered_html = template.render(
            dict_distribution_summary=dict_distribution_summary,
            dict_comparison_summary=dict_comparison_summary,
            charts_html=charts_html,
            summary_tables_html=summary_tables_html,
            breakdown_tables_html=breakdown_tables_html
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

        logger.info(f"Generated Jinja2 HTML report: {output_path}")

    def generate_summary_table_html(self, dict_comparison_summary: Dict) -> Dict[str, str]:
        """Generate HTML tables for summary statistics from dict_comparison_summary
        
        Args:
            dict_comparison_summary: Dictionary containing comparison summary data for each item
            
        Returns:
            Dict mapping item names to their HTML table strings
        """
        summary_tables_html = {}
        
        for item_name, item_data in dict_comparison_summary.items():
            # Convert the nested dict to a DataFrame
            # Each column will be a stage, each row will be a metric
            stages_data = {}
            
            for stage_idx in sorted(item_data.keys()):
                stage_info = item_data[stage_idx]
                stages_data[stage_info['stage_name']] = {
                    'Total Value': stage_info['value_total'],
                    'Value Difference': stage_info['value_diff'],
                    'Difference %': stage_info['value_diff_percent'] * 100,
                    'Total %': stage_info['value_total_percent'] * 100
                }
            
            # Create DataFrame with metrics as index and stages as columns
            df = pd.DataFrame(stages_data)
            
            # Format the values using pandas Styler
            def format_cell(val, row_name):
                if 'Difference %' in row_name or 'Total %' in row_name:
                    return f"{val:,.2f}%"
                else:
                    return f"{val:,.2f}"
            
            # Create a formatted version for HTML
            formatted_data = {}
            for col in df.columns:
                formatted_data[col] = [format_cell(df.loc[metric, col], metric) for metric in df.index]
            
            formatted_df = pd.DataFrame(formatted_data, index=df.index)
            
            # Convert to HTML with custom styling
            html_table = formatted_df.to_html(
                classes='summary-table',
                border=0,
                escape=False,
                index=True,
                index_names=False
            )
            
            # Add the Metric header to the first column
            html_table = html_table.replace('<thead>', '<thead>\n    <tr style="display: none;"><th></th></tr>', 1)
            html_table = html_table.replace('<th></th>', '<th>Metric</th>', 1)
            
            summary_tables_html[item_name] = html_table
        
        return summary_tables_html

    def generate_breakdown_tables_html(self, breakdown_data: Dict[str, pd.DataFrame]) -> Dict[str, str]:
        """Generate pivot-table-style HTML tables from breakdown DataFrames
        
        Creates Excel-like pivot tables with subtotal rows at each level and grand total row.
        Handles 1, 2, or 3 breakdown dimensions with proper cell merging and alignment.
        
        Args:
            breakdown_data: Dict mapping item names to their breakdown DataFrames
            
        Returns:
            Dict mapping item names to their HTML table strings
        """
        breakdown_tables_html = {}
        
        for item_name, df in breakdown_data.items():
            if df.empty:
                breakdown_tables_html[item_name] = "<p>No breakdown data available</p>"
                continue
            
            # Get breakdown column names (all columns except the metric columns)
            metric_cols = ['value_total_start', 'value_total_end', 'policy_count', 'value_diff', 'value_diff_percent']
            breakdown_cols = [col for col in df.columns if col not in metric_cols]
            
            if not breakdown_cols:
                breakdown_tables_html[item_name] = "<p>No breakdown dimensions specified</p>"
                continue
            
            # Build HTML table with subtotals
            html_parts = []
            html_parts.append('<table class="breakdown-table">')
            
            # Header
            html_parts.append('  <thead>')
            html_parts.append('    <tr>')
            for col in breakdown_cols:
                html_parts.append(f'      <th class="segment-col">{col}</th>')
            html_parts.append('      <th class="value-col">Policy Count</th>')
            html_parts.append('      <th class="value-col">Start Value</th>')
            html_parts.append('      <th class="value-col">End Value</th>')
            html_parts.append('      <th class="value-col">Value Difference</th>')
            html_parts.append('      <th class="value-col">Difference %</th>')
            html_parts.append('    </tr>')
            html_parts.append('  </thead>')
            html_parts.append('  <tbody>')
            
            num_levels = len(breakdown_cols)
            
            if num_levels == 1:
                # Single level - no subtotals needed, just detail rows
                for idx, row in df.iterrows():
                    html_parts.append('    <tr class="detail-row">')
                    html_parts.append(f'      <td class="segment-col">{row[breakdown_cols[0]]}</td>')
                    html_parts.append(f'      <td class="value-col">{row["policy_count"]:,.0f}</td>')
                    html_parts.append(f'      <td class="value-col">{row["value_total_start"]:,.2f}</td>')
                    html_parts.append(f'      <td class="value-col">{row["value_total_end"]:,.2f}</td>')
                    html_parts.append(f'      <td class="value-col">{row["value_diff"]:,.2f}</td>')
                    html_parts.append(f'      <td class="value-col">{row["value_diff_percent"]:,.2f}%</td>')
                    html_parts.append('    </tr>')
            
            elif num_levels == 2:
                # Two levels - subtotals for first level
                for level1_val in df[breakdown_cols[0]].unique():
                    level1_subset = df[df[breakdown_cols[0]] == level1_val]
                    level1_row_count = len(level1_subset)
                    
                    # Detail rows with rowspan for first column
                    for idx, (_, row) in enumerate(level1_subset.iterrows()):
                        html_parts.append('    <tr class="detail-row">')
                        if idx == 0:
                            html_parts.append(f'      <td class="segment-col level1-cell" rowspan="{level1_row_count + 1}">{level1_val}</td>')
                        html_parts.append(f'      <td class="segment-col">{row[breakdown_cols[1]]}</td>')
                        html_parts.append(f'      <td class="value-col">{row["policy_count"]:,.0f}</td>')
                        html_parts.append(f'      <td class="value-col">{row["value_total_start"]:,.2f}</td>')
                        html_parts.append(f'      <td class="value-col">{row["value_total_end"]:,.2f}</td>')
                        html_parts.append(f'      <td class="value-col">{row["value_diff"]:,.2f}</td>')
                        html_parts.append(f'      <td class="value-col">{row["value_diff_percent"]:,.2f}%</td>')
                        html_parts.append('    </tr>')
                    
                    # Level 1 subtotal row
                    subtotal_count = level1_subset['policy_count'].sum()
                    subtotal_start = level1_subset['value_total_start'].sum()
                    subtotal_end = level1_subset['value_total_end'].sum()
                    subtotal_diff = subtotal_end - subtotal_start
                    subtotal_diff_pct = (subtotal_diff / subtotal_start * 100) if subtotal_start != 0 else 0
                    
                    html_parts.append('    <tr class="subtotal-row subtotal-level1">')
                    html_parts.append(f'      <td class="segment-col"><strong>{level1_val} Subtotal</strong></td>')
                    html_parts.append(f'      <td class="value-col"><strong>{subtotal_count:,.0f}</strong></td>')
                    html_parts.append(f'      <td class="value-col"><strong>{subtotal_start:,.2f}</strong></td>')
                    html_parts.append(f'      <td class="value-col"><strong>{subtotal_end:,.2f}</strong></td>')
                    html_parts.append(f'      <td class="value-col"><strong>{subtotal_diff:,.2f}</strong></td>')
                    html_parts.append(f'      <td class="value-col"><strong>{subtotal_diff_pct:,.2f}%</strong></td>')
                    html_parts.append('    </tr>')
            
            elif num_levels == 3:
                # Three levels - subtotals for both first and second levels
                for level1_val in df[breakdown_cols[0]].unique():
                    level1_subset = df[df[breakdown_cols[0]] == level1_val]
                    level1_total_rows = 0
                    
                    # Calculate total rows for level1 (including subtotals)
                    for level2_val in level1_subset[breakdown_cols[1]].unique():
                        level2_subset = level1_subset[level1_subset[breakdown_cols[1]] == level2_val]
                        level1_total_rows += len(level2_subset) + 1  # details + level2 subtotal
                    level1_total_rows += 1  # level1 subtotal
                    
                    first_row_in_level1 = True
                    
                    for level2_val in level1_subset[breakdown_cols[1]].unique():
                        level2_subset = level1_subset[level1_subset[breakdown_cols[1]] == level2_val]
                        level2_row_count = len(level2_subset)
                        
                        # Detail rows with rowspan for first two columns
                        for idx, (_, row) in enumerate(level2_subset.iterrows()):
                            html_parts.append('    <tr class="detail-row">')
                            if first_row_in_level1:
                                html_parts.append(f'      <td class="segment-col level1-cell" rowspan="{level1_total_rows}">{level1_val}</td>')
                                first_row_in_level1 = False
                            if idx == 0:
                                html_parts.append(f'      <td class="segment-col level2-cell" rowspan="{level2_row_count + 1}">{level2_val}</td>')
                            html_parts.append(f'      <td class="segment-col">{row[breakdown_cols[2]]}</td>')
                            html_parts.append(f'      <td class="value-col">{row["policy_count"]:,.0f}</td>')
                            html_parts.append(f'      <td class="value-col">{row["value_total_start"]:,.2f}</td>')
                            html_parts.append(f'      <td class="value-col">{row["value_total_end"]:,.2f}</td>')
                            html_parts.append(f'      <td class="value-col">{row["value_diff"]:,.2f}</td>')
                            html_parts.append(f'      <td class="value-col">{row["value_diff_percent"]:,.2f}%</td>')
                            html_parts.append('    </tr>')
                        
                        # Level 2 subtotal row
                        subtotal2_count = level2_subset['policy_count'].sum()
                        subtotal2_start = level2_subset['value_total_start'].sum()
                        subtotal2_end = level2_subset['value_total_end'].sum()
                        subtotal2_diff = subtotal2_end - subtotal2_start
                        subtotal2_diff_pct = (subtotal2_diff / subtotal2_start * 100) if subtotal2_start != 0 else 0
                        
                        html_parts.append('    <tr class="subtotal-row subtotal-level2">')
                        html_parts.append(f'      <td class="segment-col"><strong>{level2_val} Subtotal</strong></td>')
                        html_parts.append(f'      <td class="value-col"><strong>{subtotal2_count:,.0f}</strong></td>')
                        html_parts.append(f'      <td class="value-col"><strong>{subtotal2_start:,.2f}</strong></td>')
                        html_parts.append(f'      <td class="value-col"><strong>{subtotal2_end:,.2f}</strong></td>')
                        html_parts.append(f'      <td class="value-col"><strong>{subtotal2_diff:,.2f}</strong></td>')
                        html_parts.append(f'      <td class="value-col"><strong>{subtotal2_diff_pct:,.2f}%</strong></td>')
                        html_parts.append('    </tr>')
                    
                    # Level 1 subtotal row
                    subtotal1_count = level1_subset['policy_count'].sum()
                    subtotal1_start = level1_subset['value_total_start'].sum()
                    subtotal1_end = level1_subset['value_total_end'].sum()
                    subtotal1_diff = subtotal1_end - subtotal1_start
                    subtotal1_diff_pct = (subtotal1_diff / subtotal1_start * 100) if subtotal1_start != 0 else 0
                    
                    html_parts.append('    <tr class="subtotal-row subtotal-level1">')
                    html_parts.append(f'      <td class="segment-col" colspan="2"><strong>{level1_val} Subtotal</strong></td>')
                    html_parts.append(f'      <td class="value-col"><strong>{subtotal1_count:,.0f}</strong></td>')
                    html_parts.append(f'      <td class="value-col"><strong>{subtotal1_start:,.2f}</strong></td>')
                    html_parts.append(f'      <td class="value-col"><strong>{subtotal1_end:,.2f}</strong></td>')
                    html_parts.append(f'      <td class="value-col"><strong>{subtotal1_diff:,.2f}</strong></td>')
                    html_parts.append(f'      <td class="value-col"><strong>{subtotal1_diff_pct:,.2f}%</strong></td>')
                    html_parts.append('    </tr>')
            
            # Grand total row
            grand_total_count = df['policy_count'].sum()
            grand_total_start = df['value_total_start'].sum()
            grand_total_end = df['value_total_end'].sum()
            grand_total_diff = grand_total_end - grand_total_start
            grand_total_diff_pct = (grand_total_diff / grand_total_start * 100) if grand_total_start != 0 else 0
            
            html_parts.append('    <tr class="grand-total-row">')
            html_parts.append(f'      <td class="segment-col" colspan="{len(breakdown_cols)}"><strong>Grand Total</strong></td>')
            html_parts.append(f'      <td class="value-col"><strong>{grand_total_count:,.0f}</strong></td>')
            html_parts.append(f'      <td class="value-col"><strong>{grand_total_start:,.2f}</strong></td>')
            html_parts.append(f'      <td class="value-col"><strong>{grand_total_end:,.2f}</strong></td>')
            html_parts.append(f'      <td class="value-col"><strong>{grand_total_diff:,.2f}</strong></td>')
            html_parts.append(f'      <td class="value-col"><strong>{grand_total_diff_pct:,.2f}%</strong></td>')
            html_parts.append('    </tr>')
            
            html_parts.append('  </tbody>')
            html_parts.append('</table>')
            
            breakdown_tables_html[item_name] = '\n'.join(html_parts)
        
        return breakdown_tables_html


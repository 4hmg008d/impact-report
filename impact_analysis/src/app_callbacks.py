"""
Dashboard callbacks for Impact Analysis Dashboard
Handles all user interactions and data updates
"""

import os
import logging
from datetime import datetime
from dash import Input, Output, State, ALL, callback_context
from dash.exceptions import PreventUpdate
import pandas as pd

from .app_dashboard_state import dashboard_state
from .app_dash_components import (
    create_config_section,
    create_filters_section,
    create_summary_table,
    create_charts_section
)
from ..main import ModularImpactAnalyzer


logger = logging.getLogger(__name__)


def _create_charts_html_for_display(charts_html_dict, dict_distribution_summary):
    """
    Create a complete HTML document with embedded charts for iframe display
    
    Args:
        charts_html_dict: Dictionary of chart HTML/JS from chart generator
        dict_distribution_summary: Distribution summary data
        
    Returns:
        Complete HTML string for iframe display
    """
    # Build the chart container divs and scripts
    chart_containers = []
    chart_scripts = []
    
    for item_name, item_charts in charts_html_dict.items():
        # Create a section for this item
        chart_containers.append(f'<div class="item-section">')
        chart_containers.append(f'<h2>{item_name}</h2>')
        
        # Waterfall chart first if available
        if 'waterfall' in item_charts:
            chart_id = f"waterfall-{item_name.replace(' ', '_').lower()}-chart"
            chart_containers.append(f'<div id="{chart_id}" class="chart-container"></div>')
            chart_scripts.append(item_charts['waterfall'])
        
        # Distribution charts by step
        if 'steps' in dict_distribution_summary.get(item_name, {}):
            sorted_steps = sorted(dict_distribution_summary[item_name]['steps'].keys())
            for step_num in sorted_steps:
                step_key = f'step_{step_num}'
                if step_key in item_charts:
                    step_name = dict_distribution_summary[item_name]['steps'][step_num]['step_name']
                    chart_id = f"{item_name.replace(' ', '_').lower()}-step-{step_num}-chart"
                    chart_containers.append(f'<h3>{step_name}</h3>')
                    chart_containers.append(f'<div id="{chart_id}" class="chart-container"></div>')
                    chart_scripts.append(item_charts[step_key])
        
        chart_containers.append('</div>')
    
    # Create complete HTML document
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Analysis Charts</title>
        <script src="https://code.highcharts.com/highcharts.js"></script>
        <script src="https://code.highcharts.com/modules/exporting.js"></script>
        <script src="https://code.highcharts.com/highcharts-more.js"></script>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; background: white; }}
            .item-section {{ margin-bottom: 40px; border-bottom: 2px solid #ddd; padding-bottom: 20px; }}
            .chart-container {{ width: 100%; height: 400px; margin-bottom: 30px; }}
            h2 {{ color: #333; border-bottom: 1px solid #ddd; padding-bottom: 10px; }}
            h3 {{ color: #666; margin-top: 20px; }}
        </style>
    </head>
    <body>
        {''.join(chart_containers)}
        <script>
            {' '.join(chart_scripts)}
        </script>
    </body>
    </html>
    """
    
    return html

import os
import logging
from datetime import datetime
from dash import Input, Output, State, ALL, callback_context
from dash.exceptions import PreventUpdate
import pandas as pd
from typing import Dict

from .app_dashboard_state import dashboard_state
from .app_dash_components import (
    create_config_section,
    create_filters_section,
    create_summary_table,
    create_charts_section
)
from ..main import ModularImpactAnalyzer


logger = logging.getLogger(__name__)


def _create_charts_html_for_display(charts_html_dict: Dict, dict_distribution_summary: Dict) -> str:
    """
    Create a standalone HTML document for displaying charts in iframe
    This combines the chart JavaScript with the necessary HTML structure
    """
    html_parts = []
    
    # HTML header with Highcharts libraries
    html_parts.append("""
<!DOCTYPE html>
<html>
<head>
    <title>Impact Analysis Charts</title>
    <script src="https://code.highcharts.com/highcharts.js"></script>
    <script src="https://code.highcharts.com/modules/exporting.js"></script>
    <script src="https://code.highcharts.com/highcharts-more.js"></script>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: white; }
        .chart-section { margin-bottom: 40px; }
        .chart-container { width: 100%; height: 450px; margin-bottom: 20px; }
        h2 { color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px; }
        h3 { color: #555; margin-top: 30px; }
    </style>
</head>
<body>
""")
    
    # Generate chart containers and scripts for each item
    for item_name, item_charts in charts_html_dict.items():
        html_parts.append(f'<div class="chart-section"><h2>{item_name}</h2>')
        
        # Waterfall chart first
        if 'waterfall' in item_charts:
            waterfall_id = f"waterfall-{item_name.replace(' ', '_').lower()}-chart"
            html_parts.append(f'<h3>Waterfall Chart</h3>')
            html_parts.append(f'<div id="{waterfall_id}" class="chart-container"></div>')
        
        # Distribution charts by step
        item_analysis = dict_distribution_summary.get(item_name, {})
        if 'steps' in item_analysis:
            sorted_steps = sorted(item_analysis['steps'].keys())
            for step_num in sorted_steps:
                step_data = item_analysis['steps'][step_num]
                step_name = step_data['step_name']
                chart_id = f"{item_name.replace(' ', '_').lower()}-step-{step_num}-chart"
                html_parts.append(f'<h3>Distribution: {step_name}</h3>')
                html_parts.append(f'<div id="{chart_id}" class="chart-container"></div>')
        
        html_parts.append('</div>')
    
    # Add JavaScript to render charts
    html_parts.append('<script>')
    for item_name, item_charts in charts_html_dict.items():
        for chart_type, chart_js in item_charts.items():
            html_parts.append(chart_js)
    html_parts.append('</script>')
    
    # Close HTML
    html_parts.append('</body></html>')
    
    return '\n'.join(html_parts)


def register_callbacks(app):
    """Register all dashboard callbacks"""
    
    @app.callback(
        Output('filters-container', 'children'),
        [Input('data-loaded-flag', 'data')]
    )
    def update_filters_after_data_load(data_loaded):
        """Update filter dropdowns with options from loaded data"""
        filter_options = {}
        if data_loaded and dashboard_state.has_data():
            for col in dashboard_state.filter_columns:
                filter_options[col] = dashboard_state.get_unique_values_for_filter(col)
        
        return create_filters_section(dashboard_state.filter_columns, filter_options)
    
    
    @app.callback(
        [Output('config-status-message', 'children'),
         Output('config-status-message', 'is_open'),
         Output('config-status-message', 'color'),
         Output('config-editor', 'value')],
        [Input('btn-update-config', 'n_clicks')],
        [State('config-editor', 'value')]
    )
    def update_config(n_clicks, config_text):
        """Update configuration from the editor"""
        if not n_clicks:
            raise PreventUpdate
        
        success, message = dashboard_state.update_config_from_yaml_string(config_text)
        
        if success:
            # Save to file
            save_success, save_message = dashboard_state.save_config_to_file()
            if save_success:
                message = f"{message}. {save_message}"
                return message, True, 'success', config_text
            else:
                message = f"{message}. Warning: {save_message}"
                return message, True, 'warning', config_text
        else:
            return message, True, 'danger', config_text
    
    
    @app.callback(
        [Output('loading-output', 'children'),
         Output('data-loaded-flag', 'data'),
         Output('btn-refresh-results', 'disabled'),
         Output('btn-save-html', 'disabled'),
         Output('btn-save-data', 'disabled')],
        [Input('btn-run-analysis', 'n_clicks')],
        [State('config-editor', 'value')]
    )
    def run_impact_analysis(n_clicks, config_text):
        """Run the full impact analysis and load data into memory"""
        if not n_clicks:
            raise PreventUpdate
        
        try:
            # Update config first
            success, message = dashboard_state.update_config_from_yaml_string(config_text)
            if not success:
                return f"Config error: {message}", False, True, True, True
            
            # Initialize analyzer
            analyzer = ModularImpactAnalyzer(dashboard_state.config_path)
            
            # Load and process data
            merged_df, comparison_mapping = analyzer.data_processor.process_data()
            dashboard_state.set_data(merged_df, comparison_mapping)
            
            # Calculate initial results (unfiltered)
            dict_distribution_summary = analyzer.analyzer.generate_distribution_summary(
                merged_df, comparison_mapping
            )
            dict_comparison_summary = analyzer.data_processor.aggregate_merged_data(
                merged_df, comparison_mapping
            )
            dashboard_state.set_results(dict_distribution_summary, dict_comparison_summary)
            
            logger.info("Impact analysis completed successfully")
            return "Analysis completed successfully!", True, False, False, False
            
        except Exception as e:
            logger.error(f"Error running analysis: {e}")
            import traceback
            traceback.print_exc()
            return f"Error: {str(e)}", False, True, True, True
    
    
    @app.callback(
        Output('filter-state', 'data'),
        [Input({'type': 'filter-dropdown', 'column': ALL}, 'value')],
        [State({'type': 'filter-dropdown', 'column': ALL}, 'id')]
    )
    def update_filter_state(filter_values, filter_ids):
        """Update the filter state when filters change"""
        if not filter_values or not filter_ids:
            raise PreventUpdate
        
        filter_updates = {}
        for filter_id, values in zip(filter_ids, filter_values):
            column = filter_id['column']
            filter_updates[column] = values if values else []
        
        dashboard_state.update_filters(filter_updates)
        return filter_updates
    
    
    @app.callback(
        [Output('results-summary-table', 'children'),
         Output('results-charts', 'children')],
        [Input('btn-refresh-results', 'n_clicks'),
         Input('data-loaded-flag', 'data')],
        [State('filter-state', 'data')]
    )
    def refresh_results(n_clicks, data_loaded, filter_state):
        """Refresh results based on current filters"""
        if not data_loaded or not dashboard_state.has_data():
            return "No data loaded. Run the impact analysis first.", ""
        
        try:
            # Get filtered data
            filtered_df = dashboard_state.get_filtered_data()
            
            if filtered_df is None or len(filtered_df) == 0:
                return "No data matches the current filters.", ""
            
            # Initialize analyzer
            analyzer = ModularImpactAnalyzer(dashboard_state.config_path)
            
            # Recalculate results with filtered data
            dict_distribution_summary = analyzer.analyzer.generate_distribution_summary(
                filtered_df, dashboard_state.comparison_mapping
            )
            dict_comparison_summary = analyzer.data_processor.aggregate_merged_data(
                filtered_df, dashboard_state.comparison_mapping
            )
            
            # Update state with new results
            dashboard_state.set_results(dict_distribution_summary, dict_comparison_summary)
            
            # Generate summary table
            summary_table = create_summary_table(dict_comparison_summary)
            
            # Generate full HTML report (but don't save it)
            # We'll create a temporary HTML string for display
            charts_html_dict = analyzer.visualizer.chart_generator.generate_all_charts_html(
                dict_distribution_summary, dict_comparison_summary
            )
            
            # Create a complete HTML document for iframe display
            full_html = _create_charts_html_for_display(
                charts_html_dict, dict_distribution_summary
            )
            charts_display = create_charts_section(full_html)
            
            return summary_table, charts_display
            
        except Exception as e:
            logger.error(f"Error refreshing results: {e}")
            import traceback
            traceback.print_exc()
            return f"Error refreshing results: {str(e)}", ""
    
    
    @app.callback(
        Output('config-status-message', 'children', allow_duplicate=True),
        Output('config-status-message', 'is_open', allow_duplicate=True),
        Output('config-status-message', 'color', allow_duplicate=True),
        [Input('btn-save-html', 'n_clicks')],
        prevent_initial_call=True
    )
    def save_html_report(n_clicks):
        """Save the current results as an HTML report with timestamp"""
        if not n_clicks:
            raise PreventUpdate
        
        if not dashboard_state.has_data():
            return "No data available to save.", True, 'warning'
        
        try:
            # Initialize analyzer
            analyzer = ModularImpactAnalyzer(dashboard_state.config_path)
            
            # Generate output path with timestamp
            output_dir = analyzer.config_loader.get_output_dir()
            os.makedirs(output_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            html_output_path = os.path.join(
                output_dir, 
                f"impact_analysis_report_{timestamp}.html"
            )
            
            # Generate and save HTML report
            analyzer.visualizer.generate_html_report(
                dashboard_state.dict_distribution_summary,
                dashboard_state.dict_comparison_summary,
                html_output_path
            )
            
            logger.info(f"Saved HTML report to {html_output_path}")
            return f"HTML report saved to {html_output_path}", True, 'success'
            
        except Exception as e:
            logger.error(f"Error saving HTML report: {e}")
            return f"Error saving HTML report: {str(e)}", True, 'danger'
    
    
    @app.callback(
        Output('config-status-message', 'children', allow_duplicate=True),
        Output('config-status-message', 'is_open', allow_duplicate=True),
        Output('config-status-message', 'color', allow_duplicate=True),
        [Input('btn-save-data', 'n_clicks')],
        prevent_initial_call=True
    )
    def save_data_files(n_clicks):
        """Save the current data as CSV files (overwrites existing)"""
        if not n_clicks:
            raise PreventUpdate
        
        if not dashboard_state.has_data():
            return "No data available to save.", True, 'warning'
        
        try:
            # Get filtered data
            filtered_df = dashboard_state.get_filtered_data()
            
            # Initialize analyzer
            analyzer = ModularImpactAnalyzer(dashboard_state.config_path)
            
            # Save output files (this will overwrite existing)
            analyzer.save_output_files(
                filtered_df,
                dashboard_state.dict_distribution_summary,
                dashboard_state.comparison_mapping
            )
            
            output_dir = analyzer.config_loader.get_output_dir()
            logger.info(f"Saved data files to {output_dir}")
            return f"Data files saved to {output_dir}", True, 'success'
            
        except Exception as e:
            logger.error(f"Error saving data files: {e}")
            return f"Error saving data files: {str(e)}", True, 'danger'

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
from typing import Dict

from .app_dashboard_state import dashboard_state
from .app_dash_components import (
    create_config_section,
    create_filters_section,
    create_charts_section
)
from ..main import ModularImpactAnalyzer


logger = logging.getLogger(__name__)


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
            dict_distribution_summary = analyzer.data_analyser.generate_distribution_summary(
                merged_df, comparison_mapping
            )
            dict_comparison_summary = analyzer.data_analyser.aggregate_merged_data(
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
        Output('results-charts', 'children'),
        [Input('btn-refresh-results', 'n_clicks'),
         Input('data-loaded-flag', 'data')],
        [State('filter-state', 'data')]
    )
    def refresh_results(n_clicks, data_loaded, filter_state):
        """Refresh results based on current filters"""
        if not data_loaded or not dashboard_state.has_data():
            return "No data loaded. Run the impact analysis first."
        
        try:
            # Get filtered data
            filtered_df = dashboard_state.get_filtered_data()
            
            if filtered_df is None or len(filtered_df) == 0:
                return "No data matches the current filters."
            
            # Initialize analyzer
            analyzer = ModularImpactAnalyzer(dashboard_state.config_path)
            
            # Recalculate results with filtered data
            dict_distribution_summary = analyzer.data_analyser.generate_distribution_summary(
                filtered_df, dashboard_state.comparison_mapping
            )
            dict_comparison_summary = analyzer.data_analyser.aggregate_merged_data(
                filtered_df, dashboard_state.comparison_mapping
            )
            
            # Update state with new results
            dashboard_state.set_results(dict_distribution_summary, dict_comparison_summary)
            
            # Generate full HTML report using visualizer
            html_report_content = analyzer.visualizer.generate_html_report(
                dict_distribution_summary, dict_comparison_summary
            )
            
            # Create charts display with full HTML report
            charts_display = create_charts_section(html_report_content)
            
            return charts_display
            
        except Exception as e:
            logger.error(f"Error refreshing results: {e}")
            import traceback
            traceback.print_exc()
            return f"Error refreshing results: {str(e)}"
    
    
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
            html_content = analyzer.visualizer.generate_html_report(
                dashboard_state.dict_distribution_summary,
                dashboard_state.dict_comparison_summary
            )
            analyzer.visualizer.save_report(html_content, html_output_path)
            
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

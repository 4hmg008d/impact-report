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
    create_charts_section,
    log_capture
)
from ..main import ModularImpactAnalyzer


logger = logging.getLogger(__name__)


def register_callbacks(app):
    """Register all dashboard callbacks"""
    
    @app.callback(
        Output('log-display', 'children'),
        [Input('log-interval', 'n_intervals')]
    )
    def update_logs(n_intervals):
        """Update log display with captured logs"""
        logs = log_capture.get_logs()
        if not logs:
            return "No logs yet..."
        
        # Join logs with newlines, show most recent last (at bottom)
        log_text = '\n'.join(logs[-100:])  # Show last 100 logs
        return log_text
    
    
    @app.callback(
        Output('logs-collapse', 'is_open'),
        [Input('btn-toggle-logs', 'n_clicks')],
        [State('logs-collapse', 'is_open')]
    )
    def toggle_logs(n_clicks, is_open):
        """Toggle log panel visibility"""
        if n_clicks:
            return not is_open
        return is_open
    
    
    @app.callback(
        Output('log-display', 'children', allow_duplicate=True),
        [Input('btn-clear-logs', 'n_clicks')],
        prevent_initial_call=True
    )
    def clear_logs(n_clicks):
        """Clear all captured logs"""
        if n_clicks:
            log_capture.clear_logs()
            return "Logs cleared..."
        raise PreventUpdate
    
    
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
         Output('config-editor', 'value'),
         Output('filters-container', 'children', allow_duplicate=True)],
        [Input('btn-update-config', 'n_clicks')],
        [State('config-editor', 'value')],
        prevent_initial_call=True
    )
    def update_config(n_clicks, config_text):
        """Update configuration from the editor"""
        if not n_clicks:
            raise PreventUpdate
        
        success, message = dashboard_state.update_config_from_yaml_string(config_text)
        
        # Get current filter options from loaded data (if available)
        filter_options = {}
        if dashboard_state.has_data():
            for col in dashboard_state.filter_columns:
                filter_options[col] = dashboard_state.get_unique_values_for_filter(col)
        
        # Create updated filters section
        updated_filters = create_filters_section(dashboard_state.filter_columns, filter_options)
        
        if success:
            # Save to file
            save_success, save_message = dashboard_state.save_config_to_file()
            if save_success:
                message = f"{message}. {save_message}"
                return message, True, 'success', config_text, updated_filters
            else:
                message = f"{message}. Warning: {save_message}"
                return message, True, 'warning', config_text, updated_filters
        else:
            return message, True, 'danger', config_text, updated_filters
    
    
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
            
            # Initialize data_analyser
            data_analyser = ModularImpactAnalyzer(dashboard_state.config_path)
            
            # Load and process data
            merged_df, comparison_mapping = data_analyser.data_processor.process_data()
            dashboard_state.set_data(merged_df, comparison_mapping)
            
            logger.info("Data loaded successfully")
            return "Data loaded successfully!", True, False, False, False
            
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
        [Input('btn-refresh-results', 'n_clicks')],
        [State('filter-state', 'data'),
         State('data-loaded-flag', 'data')]
    )
    def refresh_results(n_clicks, filter_state, data_loaded):
        """Refresh results based on current filters"""
        if not n_clicks:
            raise PreventUpdate
        
        if not data_loaded or not dashboard_state.has_data():
            return "No data loaded. Run the impact analysis first."
        
        try:
            # Get filtered data
            filtered_df = dashboard_state.get_filtered_data()
            
            if filtered_df is None or len(filtered_df) == 0:
                return "No data matches the current filters."
            
            # Initialize data_analyser
            data_analyser = ModularImpactAnalyzer(dashboard_state.config_path)
            
            # Recalculate results with filtered data
            dict_distribution_summary = data_analyser.data_analyser.generate_distribution_summary(
                filtered_df, dashboard_state.comparison_mapping
            )
            dict_comparison_summary = data_analyser.data_analyser.generate_comparison_summary(
                filtered_df, dashboard_state.comparison_mapping
            )
            
            # Update state with new results
            dashboard_state.set_results(dict_distribution_summary, dict_comparison_summary)
            
            # Generate breakdown analysis if breakdown columns are configured
            breakdown_columns = data_analyser.config_loader.get_breakdown_columns()
            breakdown_data = None
            if breakdown_columns:
                breakdown_data = data_analyser.data_analyser.aggregate_impact_breakdown(
                    filtered_df, dashboard_state.comparison_mapping, breakdown_columns
                )
            
            # Generate full HTML report using visualizer
            html_report_content = data_analyser.visualizer.generate_html_report(
                dict_distribution_summary, dict_comparison_summary, breakdown_data
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
            # Initialize data_analyser
            data_analyser = ModularImpactAnalyzer(dashboard_state.config_path)
            
            # Generate output path with timestamp
            output_dir = data_analyser.config_loader.get_output_dir()
            os.makedirs(output_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            html_output_path = os.path.join(
                output_dir, 
                f"impact_analysis_report_{timestamp}.html"
            )
            
            # Generate breakdown analysis if breakdown columns are configured
            breakdown_columns = data_analyser.config_loader.get_breakdown_columns()
            breakdown_data = None
            if breakdown_columns and dashboard_state.merged_df is not None:
                filtered_df = dashboard_state.get_filtered_data()
                breakdown_data = data_analyser.data_analyser.aggregate_impact_breakdown(
                    filtered_df, dashboard_state.comparison_mapping, breakdown_columns
                )
            
            # Generate and save HTML report
            html_content = data_analyser.visualizer.generate_html_report(
                dashboard_state.dict_distribution_summary,
                dashboard_state.dict_comparison_summary,
                breakdown_data
            )
            data_analyser.visualizer.save_report(html_content, html_output_path)
            
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
            
            # Initialize data_analyser
            data_analyser = ModularImpactAnalyzer(dashboard_state.config_path)
            
            # Save output files (this will overwrite existing)
            data_analyser.save_output_files(
                filtered_df,
                dashboard_state.dict_distribution_summary,
                dashboard_state.comparison_mapping
            )
            
            output_dir = data_analyser.config_loader.get_output_dir()
            logger.info(f"Saved data files to {output_dir}")
            return f"Data files saved to {output_dir}", True, 'success'
            
        except Exception as e:
            logger.error(f"Error saving data files: {e}")
            return f"Error saving data files: {str(e)}", True, 'danger'
    
    
    @app.callback(
        [Output('export-item-dropdown', 'options'),
         Output('export-step-dropdown', 'options'),
         Output('btn-export-filtered', 'disabled')],
        [Input('data-loaded-flag', 'data')]
    )
    def update_export_dropdowns(data_loaded):
        """Update export section dropdowns when data is loaded"""
        if not data_loaded or not dashboard_state.has_data():
            return [], [], True
        
        try:
            # Get items from comparison_mapping
            item_options = [
                {'label': item_name, 'value': item_name}
                for item_name in dashboard_state.comparison_mapping.keys()
            ]
            
            # Get steps from the first item (all items should have same steps)
            if dashboard_state.comparison_mapping:
                first_item = list(dashboard_state.comparison_mapping.keys())[0]
                step_dict = dashboard_state.comparison_mapping[first_item].get('differences', {})
                step_options = []
                for step_num in sorted(step_dict.keys()):
                    step_name = dashboard_state.comparison_mapping[first_item]['step_names'].get(step_num, f'Step {step_num}')
                    step_options.append({'label': step_name, 'value': step_num})
            else:
                step_options = []
            
            return item_options, step_options, False
            
        except Exception as e:
            logger.error(f"Error updating export dropdowns: {e}")
            return [], [], True
    
    
    @app.callback(
        Output('export-segment-selector', 'style'),
        [Input('data-loaded-flag', 'data')]
    )
    def toggle_segment_selector(data_loaded):
        """Show/hide NB/RN selector based on whether renewal is enabled"""
        if not data_loaded or not dashboard_state.has_data():
            return {'display': 'none'}
        
        try:
            # Check if renewal is enabled in any item
            renewal_enabled = False
            if dashboard_state.comparison_mapping:
                for item_dict in dashboard_state.comparison_mapping.values():
                    if item_dict.get('renewal_enabled', False):
                        renewal_enabled = True
                        break
            
            if renewal_enabled:
                return {'display': 'inline-block', 'marginRight': '5px'}
            else:
                return {'display': 'none'}
                
        except Exception as e:
            logger.error(f"Error toggling segment selector: {e}")
            return {'display': 'none'}
    
    
    @app.callback(
        [Output('export-status-message', 'children'),
         Output('export-status-message', 'is_open'),
         Output('export-status-message', 'color')],
        [Input('btn-export-filtered', 'n_clicks')],
        [State('export-item-dropdown', 'value'),
         State('export-step-dropdown', 'value'),
         State('export-from-input', 'value'),
         State('export-to-input', 'value'),
         State('export-segment-radio', 'value')]
    )
    def export_filtered_data(n_clicks, item_name, step_num, from_threshold, to_threshold, segment_type):
        """Export filtered data based on rate change thresholds"""
        if not n_clicks:
            raise PreventUpdate
        
        # Default segment_type to 'nb' if not provided
        if segment_type is None:
            segment_type = 'nb'
        
        # Validate inputs
        if not item_name:
            return "Please select an item.", True, 'warning'
        
        if step_num is None:
            return "Please select a step.", True, 'warning'
        
        if from_threshold is None or to_threshold is None:
            return "Please enter both 'from' and 'to' threshold values.", True, 'warning'
        
        # Validate threshold range
        if from_threshold < -1:
            return "The 'from' threshold must be greater than or equal to -1.", True, 'warning'
        
        if from_threshold > to_threshold:
            return "The 'from' threshold must be less than or equal to the 'to' threshold.", True, 'warning'
        
        if not dashboard_state.has_data():
            return "No data available. Please run the analysis first.", True, 'warning'
        
        try:
            # Initialize data_analyser to get data_processor
            data_analyser = ModularImpactAnalyzer(dashboard_state.config_path)
            
            # Get filtered data using the dashboard's current filtered data
            current_filtered_df = dashboard_state.get_filtered_data()
            
            # Apply rate change filter
            rate_filtered_df = data_analyser.data_processor.filter_data_by_rate_change(
                merged_df=current_filtered_df,
                comparison_mapping=dashboard_state.comparison_mapping,
                item_name=item_name,
                step_num=step_num,
                from_threshold=from_threshold,
                to_threshold=to_threshold,
                segment_type=segment_type
            )
            
            # Generate output filename with timestamp
            output_dir = data_analyser.config_loader.get_output_dir()
            os.makedirs(output_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            step_name = dashboard_state.comparison_mapping[item_name]['step_names'].get(step_num, f'step_{step_num}')
            # Clean step name for filename
            step_name_clean = step_name.replace(' ', '_').replace('/', '_')
            item_name_clean = item_name.replace(' ', '_').replace('/', '_')
            segment_suffix = f"_{segment_type.upper()}" if segment_type else ""
            
            filename = f"filtered_data_{item_name_clean}_{step_name_clean}{segment_suffix}_{timestamp}.csv"
            output_path = os.path.join(output_dir, filename)
            
            # Save to CSV
            rate_filtered_df.to_csv(output_path, index=False)
            
            logger.info(f"Exported filtered data to {output_path}")
            return f"Successfully exported {len(rate_filtered_df)} rows to {filename}", True, 'success'
            
        except ValueError as ve:
            logger.error(f"Validation error during filtered export: {ve}")
            return f"Validation error: {str(ve)}", True, 'danger'
        except Exception as e:
            logger.error(f"Error exporting filtered data: {e}")
            import traceback
            traceback.print_exc()
            return f"Error exporting data: {str(e)}", True, 'danger'

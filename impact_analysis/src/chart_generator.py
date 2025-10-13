"""
Chart generation module for impact analysis using Highcharts Python
"""

from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.axes.x_axis import XAxis
from highcharts_core.options.axes.y_axis import YAxis
from highcharts_core.options.series.bar import ColumnSeries
from highcharts_core.options.series.bar import WaterfallSeries
from typing import Dict, List, Any
import pandas as pd


class ImpactChartGenerator:
    """Generates Highcharts charts for impact analysis results"""
    
    def __init__(self, config_loader=None):
        self.config_loader = config_loader
    
    
    def _get_band_order(self) -> List[str]:
        """Get the original band order from the configuration"""
        if not self.config_loader:
            return None
        
        try:
            band_df = self.config_loader.load_band_data()
            # Return band names in the order they appear in the configuration
            return band_df['Name'].tolist()
        except Exception as e:
            print(f"Warning: Could not load band order from configuration: {e}")
            return None


    def create_bar_chart(self, chart_data: List[Dict], title: str, chart_id: str = None, band_order: List[str] = None, 
                         renewal_enabled: bool = False, renewal_chart_data: List[Dict] = None) -> Chart:
        """Create a vertical bar chart from chart data with bands in original order
        
        Args:
            chart_data: Chart data for New Business (or all data if renewal not enabled)
            title: Chart title
            chart_id: Optional chart ID for rendering
            band_order: Optional list of band names in original order
            renewal_enabled: If True, creates a grouped column chart with two series
            renewal_chart_data: Chart data for Renewal segment (required if renewal_enabled is True)
        
        Returns:
            Chart object
        """
        
        # If band_order is provided, reorder chart_data to match the original band order
        if band_order:
            # Create a mapping from band name to data
            data_map = {item['name']: item for item in chart_data}
            
            # Reorder data according to band_order, include only bands that have data
            ordered_data = []
            for band_name in band_order:
                if band_name in data_map:
                    ordered_data.append(data_map[band_name])
            
            # Add any remaining bands that weren't in band_order but have data
            for item in chart_data:
                if item['name'] not in band_order:
                    ordered_data.append(item)
            
            chart_data = ordered_data
            
            # Also reorder renewal data if provided
            if renewal_enabled and renewal_chart_data:
                renewal_data_map = {item['name']: item for item in renewal_chart_data}
                ordered_renewal_data = []
                for band_name in band_order:
                    if band_name in renewal_data_map:
                        ordered_renewal_data.append(renewal_data_map[band_name])
                
                for item in renewal_chart_data:
                    if item['name'] not in band_order:
                        ordered_renewal_data.append(item)
                
                renewal_chart_data = ordered_renewal_data
        
        # Extract categories for x-axis
        categories = [item['name'] for item in chart_data]
        
        # Create series based on whether renewal is enabled
        if renewal_enabled and renewal_chart_data:
            # Grouped column chart with two series: New Business and Renewal
            nb_series_data = [
                {'name': item['name'], 'y': item['percentage'], 'custom': {'count': item['y']}}
                for item in chart_data
            ]
            
            rn_series_data = [
                {'name': item['name'], 'y': item['percentage'], 'custom': {'count': item['y']}}
                for item in renewal_chart_data
            ]
            
            series = [
                ColumnSeries(
                    name='New Business',
                    data=nb_series_data,
                    color='#7cb5ec'  # Blue color for New Business
                ),
                ColumnSeries(
                    name='Renewal',
                    data=rn_series_data,
                    color='#90ed7d'  # Green color for Renewal
                )
            ]
            
            tooltip_config = {
                'headerFormat': '<span style="font-size:10px">{point.key}</span><br/>',
                'pointFormat': '<span style="color:{series.color}">{series.name}</span>: <b>{point.y:.1f}%</b><br/>Count: <b>{point.custom.count}</b><br/>',
                'shared': True,
                'useHTML': True
            }
            
        else:
            # Single series chart (original behavior)
            series_data = [
                {'name': item['name'], 'y': item['percentage'], 'custom': {'count': item['y']}}
                for item in chart_data
            ]
            
            series = [
                ColumnSeries(
                    name='Policy Proportion',
                    data=series_data,
                    color_by_point=True
                )
            ]
            
            tooltip_config = {
                'headerFormat': '<span style="font-size:10px">{point.key}</span><br/>',
                'pointFormat': 'Count: <b>{point.custom.count}</b>',
                'shared': False,
                'useHTML': True
            }
        
        options = HighchartsOptions(
            chart={'type': 'column', 'renderTo': chart_id} if chart_id else {'type': 'column'},
            title={'text': title},
            x_axis=XAxis(
                type='category',
                categories=categories,
                title={'text': 'Difference Bands'},
                labels={
                    'rotation': 315,
                    'style': {
                        'fontSize': '11px',
                        'fontFamily': 'Verdana, sans-serif'
                    }
                }
            ),
            y_axis=YAxis(
                title={'text': 'Proportion of Policies (%)'},
                min=0,
                max=100
            ),
            tooltip=tooltip_config,
            plot_options={
                'column': {
                    'pointPadding': 0.2,
                    'borderWidth': 0,
                    'dataLabels': {
                        'enabled': True,
                        'format': '{y:.1f}%'
                    }
                }
            },
            series=series
        )
        
        return Chart.from_options(options)


    def create_waterfall_chart(self, dict_waterfall: Dict, title: str, chart_id: str = None) -> Chart:
        """Create a waterfall chart from summary statistics data"""
        
        # Create waterfall series data
        waterfall_data = []
        
        # Get sorted indices
        sorted_indices = sorted(dict_waterfall.keys())
        
        # Starting point
        waterfall_data.append({
            'name': dict_waterfall[sorted_indices[0]]['stage_name'],
            'y': dict_waterfall[sorted_indices[0]]['value_total_percent'] * 100,
            'color': '#550062',
            'custom': {
                'value_total': dict_waterfall[sorted_indices[0]]['value_total'],
                'value_diff': dict_waterfall[sorted_indices[0]]['value_diff']
            }
        })
        
        # Intermediate changes
        for i in range(1, len(sorted_indices)):
            idx = sorted_indices[i]
            change = dict_waterfall[idx]['value_diff_percent'] * 100
            waterfall_data.append({
                'name': dict_waterfall[idx]['stage_name'],
                'y': change,
                'color': '#90ed7d' if change >= 0 else '#f7a35c',
                'custom': {
                    'value_total': dict_waterfall[idx]['value_total'],
                    'value_diff': dict_waterfall[idx]['value_diff']
                }
            })
        
        # Final sum
        waterfall_data.append({
            'name': 'Final',
            'y': dict_waterfall[sorted_indices[-1]]['value_total_percent'] * 100,
            'isSum': True,
            'color': '#550062',
            'custom': {
                'value_total': dict_waterfall[sorted_indices[-1]]['value_total'],
                'value_diff': dict_waterfall[sorted_indices[-1]]['value_total'] - dict_waterfall[sorted_indices[0]]['value_total']
            }
        })
        
        # Create chart options
        options = HighchartsOptions(
            chart={'type': 'waterfall', 'renderTo': chart_id} if chart_id else {'type': 'waterfall'},
            title={'text': title},
            x_axis=XAxis(
                type='category',
                title={'text': 'Stages'}
            ),
            y_axis=YAxis(
                title={'text': 'Total Value'},
            ),
            tooltip={
                'pointFormat': '<br/>Value: {point.custom.value_total:,.0f}<br/>Step Impact: {point.custom.value_diff:,.0f}'
            },
            plot_options={
                'waterfall': {
                    'pointPadding': 0.2,
                    'dataLabels': {
                        'enabled': True,
                        'verticalAlign': 'top',
                        'format': '{y:.1f}%'
                    }
                }
            },
            series=[
                WaterfallSeries(
                    name=title.split(' - ')[0] if ' - ' in title else title,
                    data=waterfall_data
                )
            ]
        )
        
        return Chart.from_options(options)


    def generate_all_charts_html(self, dict_distribution_summary: Dict, dict_comparison_summary: Dict) -> Dict:
        """Generate all charts HTML for the analysis data - consistent pattern
        
        Handles both regular and renewal-enabled charts.
        """
        charts_html = {}
        
        for item_name, item_analysis in dict_distribution_summary.items():
            charts_html[item_name] = {}
            
            # Check if renewal is enabled for this item
            renewal_enabled = item_analysis.get('renewal_enabled', False)
            
            # Generate distribution charts for each step (sorted by step number)
            sorted_steps = sorted(item_analysis['steps'].keys())
            for step_num in sorted_steps:
                chart_data = item_analysis['steps'][step_num]
                chart_title = f"{item_name} - {chart_data['step_name']}"
                chart_id = f"{item_name.replace(' ', '_').lower()}-step-{step_num}-chart"
                band_order = self._get_band_order()
                
                # Check if renewal data is available for this step
                renewal_chart_data = chart_data.get('renewal_chart_data', None) if renewal_enabled else None
                
                # Create chart with or without renewal data
                chart_html = self.create_bar_chart(
                    chart_data['chart_data'], 
                    chart_title, 
                    chart_id, 
                    band_order,
                    renewal_enabled=renewal_enabled,
                    renewal_chart_data=renewal_chart_data
                ).to_js_literal()
                
                charts_html[item_name][f'step_{step_num}'] = chart_html
            
            # Generate waterfall chart for this item if summary stats available
        for item_name, item_dict in dict_comparison_summary.items():
            waterfall_title = f"{item_name} - Waterfall Chart"
            waterfall_chart_id = f"waterfall-{item_name.replace(' ', '_').lower()}-chart"
            waterfall_html = self.create_waterfall_chart(item_dict, waterfall_title, waterfall_chart_id).to_js_literal()
            charts_html[item_name]['waterfall'] = waterfall_html
    
        return charts_html
    
    
    def generate_chart_for_dash(self, chart_data: List[Dict], title: str) -> Dict:
        """Generate chart configuration for Dash integration"""
        chart = self.create_bar_chart(chart_data, title)
        
        # Convert to JSON-serializable format for Dash
        chart_config = chart.to_dict()
        
        # Simplify for Dash compatibility
        simplified_config = {
            'chart': chart_config.get('chart', {}),
            'title': chart_config.get('title', {}),
            'xAxis': chart_config.get('xAxis', {}),
            'yAxis': chart_config.get('yAxis', {}),
            'series': chart_config.get('series', []),
            'plotOptions': chart_config.get('plotOptions', {}),
            'tooltip': chart_config.get('tooltip', {})
        }
        
        return simplified_config
    
    def generate_dash_charts(self, analysis_data: Dict) -> Dict[str, Dict]:
        """Generate chart configurations for Dash dashboard"""
        dash_charts = {}
        
        # Overall chart for Dash
        dash_charts['overall'] = self.generate_chart_for_dash(
            analysis_data['overall']['chart_data'],
            'Overall Difference Distribution'
        )
        
        return dash_charts


def generate_dash_compatible_charts(analysis_data: Dict) -> Dict[str, Dict]:
    """Generate chart configurations for Dash (backward compatibility)"""
    generator = ImpactChartGenerator()
    return generator.generate_dash_charts(analysis_data)

"""
Chart generation module for impact analysis using Highcharts Python
"""

from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.global_options.shared_options import SharedOptions
from highcharts_core.options.axes.x_axis import XAxis
from highcharts_core.options.axes.y_axis import YAxis
from highcharts_core.options.series.bar import ColumnSeries
from typing import Dict, List, Any


class ImpactChartGenerator:
    """Generates Highcharts charts for impact analysis results"""
    
    def __init__(self, config_loader=None):
        self.config_loader = config_loader
        self.shared_options = self._create_shared_options()
    
    def _create_shared_options(self) -> SharedOptions:
        """Create shared options for all charts"""
        return SharedOptions(
            chart={
                'type': 'bar'
            },
            xAxis={
                'type': 'category',
                'title': {
                    'text': 'Difference Bands'
                }
            },
            yAxis={
                'title': {
                    'text': 'Proportion of Policies (%)'
                },
                'max': 100
            },
            tooltip={
                'pointFormat': 'Proportion: <b>{point.percentage}%</b><br>Count: <b>{point.y}</b>'
            },
            plotOptions={
                'bar': {
                    'dataLabels': {
                        'enabled': True,
                        'format': '{point.percentage}%'
                    }
                }
            }
        )
    
    def create_bar_chart(self, chart_data: List[Dict], title: str, chart_id: str = None, band_order: List[str] = None) -> Chart:
        """Create a vertical bar chart from chart data with bands in original order"""
        
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
        
        # Prepare series data - use percentage for y-axis (proportion) but include count in custom properties
        series_data = [
            {'name': item['name'], 'y': item['percentage'], 'custom': {'count': item['y']}}
            for item in chart_data
        ]

        # Extract categories for x-axis
        categories = [item['name'] for item in chart_data]
        
        # Debug: Print the series data to see what's being generated
        # print(f"Series data: {series_data}")
        
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
            tooltip={
                'headerFormat': '<span style="font-size:10px">{point.key}</span><br/>',
                'pointFormat': 'Count: <b>{point.custom.count}</b>',
                'shared': False,
                'useHTML': True
            },
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
            series=[
                ColumnSeries(
                    name='Policy Proportion',
                    data=series_data,
                    color_by_point=True
                )
            ]
        )
        
        # Debug: Print the options to see what's being generated
        # print(f"Chart options: {options.to_js_literal()}")
        
        return Chart.from_options(options)
    
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
    
    def generate_chart_html(self, chart_data: List[Dict], title: str, chart_id: str) -> str:
        """Generate HTML for a single chart"""
        band_order = self._get_band_order()
        chart = self.create_bar_chart(chart_data, title, chart_id, band_order)
        return chart.to_js_literal()
    
    def generate_overall_chart_html(self, overall_data: Dict, item_name: str) -> str:
        """Generate HTML for overall distribution chart"""
        band_order = self._get_band_order()
        chart_id = f"{item_name.replace(' ', '_').replace(':', '_').lower()}-chart"
        chart = self.create_bar_chart(
            overall_data['chart_data'],
            f'{item_name} - Overall Difference Distribution',
            chart_id,
            band_order
        )
        return chart.to_js_literal()
    
    def generate_step_chart_html(self, step_data: Dict, title: str, chart_id: str) -> str:
        """Generate HTML for step distribution chart"""
        band_order = self._get_band_order()
        chart = self.create_bar_chart(
            step_data['chart_data'],
            title,
            chart_id,
            band_order
        )
        return chart.to_js_literal()

    def generate_segment_chart_html(self, segment_data: Dict, segment_name: str, chart_id: str = None) -> str:
        """Generate HTML for segment distribution chart"""
        if chart_id is None:
            chart_id = f"{segment_name.replace(' ', '_').replace(':', '_').lower()}-chart"
        band_order = self._get_band_order()
        chart = self.create_bar_chart(
            segment_data['chart_data'],
            f'{segment_name} - Difference Distribution',
            chart_id,
            band_order
        )
        return chart.to_js_literal()
    
    def generate_all_charts_html(self, analysis_data: Dict, item_name: str = None) -> Dict[str, str]:
        """Generate HTML for all charts in the analysis with new nested structure"""
        charts_html = {}
        
        # Handle new structure with steps
        if 'steps' in analysis_data:
            for step, step_data in analysis_data['steps'].items():
                step_name = step_data['step_name']
                # Create chart ID that matches the template: {item_name}-step-{step}-chart
                chart_id = f"{item_name.replace(' ', '_').replace(':', '_').lower()}-step-{step}-chart"
                
                # Generate chart for this step
                charts_html[f"step_{step}"] = self.generate_step_chart_html(step_data, f"{item_name} - {step_name}", chart_id)
                
                # Generate segment charts for this step if available
                if 'segment_tabs' in step_data:
                    for segment_name, segment_data in step_data['segment_tabs'].items():
                        segment_chart_id = f"{item_name.replace(' ', '_').replace(':', '_').lower()}-step-{step}-{segment_name.replace(' ', '_').lower()}-chart"
                        charts_html[f"step_{step}_{segment_name}"] = self.generate_segment_chart_html(segment_data, f"{step_name} - {segment_name}", segment_chart_id)
        else:
            # Fallback to old structure for compatibility
            if 'overall' in analysis_data:
                charts_html['overall'] = self.generate_overall_chart_html(analysis_data['overall'], item_name)
            
            if 'segment_tabs' in analysis_data:
                for segment_name, segment_data in analysis_data['segment_tabs'].items():
                    charts_html[segment_name] = self.generate_segment_chart_html(segment_data, segment_name)
        
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
        
        # Segment charts for Dash
        for segment_name, segment_data in analysis_data['segment_tabs'].items():
            dash_charts[segment_name] = self.generate_chart_for_dash(
                segment_data['chart_data'],
                f'{segment_name} - Difference Distribution'
            )
        
        return dash_charts


# Utility functions for backward compatibility
def create_chart_generator():
    """Factory function to create chart generator instance"""
    return ImpactChartGenerator()


def generate_static_report_charts(analysis_data: Dict) -> Dict[str, str]:
    """Generate chart HTML for static reports (backward compatibility)"""
    generator = ImpactChartGenerator()
    return generator.generate_all_charts_html(analysis_data)


def generate_dash_compatible_charts(analysis_data: Dict) -> Dict[str, Dict]:
    """Generate chart configurations for Dash (backward compatibility)"""
    generator = ImpactChartGenerator()
    return generator.generate_dash_charts(analysis_data)

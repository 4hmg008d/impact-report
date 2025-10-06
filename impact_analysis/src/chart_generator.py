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


class ImpactChartGenerator:
    """Generates Highcharts charts for impact analysis results"""
    
    def __init__(self, config_loader=None):
        self.config_loader = config_loader
    
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


    def create_waterfall_chart(self, item_data: Dict, summary_stats: Dict, title: str, chart_id: str = None) -> Chart:
        """Create a waterfall chart from summary statistics data"""
        if not summary_stats:
            return None
        
        # Debug: Print the summary stats to see what's being used
        # print(f"Creating waterfall chart for {title} with summary stats: {summary_stats}")
        # print(f"Item data: {item_data}")

        # Prepare waterfall data
        steps = sorted(item_data['step_names'].keys())
        step_names = [item_data['step_names'][step] for step in steps]
        values = []
        
        # Get values for each step
        for step in steps:
            if step in summary_stats and 'total' in summary_stats[step]:
                values.append(summary_stats[step]['total'])
            else:
                values.append(0)
        
        if not values:
            return None
        
        # Create waterfall series data
        waterfall_data = []
        
        # Starting point
        waterfall_data.append({
            'name': step_names[0],
            'y': values[0],
            'isSum': False,
            'color': '#7cb5ec'
        })
        
        # Intermediate changes
        for i in range(1, len(values)):
            change = values[i] - values[i-1]
            waterfall_data.append({
                'name': step_names[i],
                'y': change,
                'isIntermediateSum': False,
                'color': '#90ed7d' if change >= 0 else '#f7a35c'
            })
        
        # Final sum
        waterfall_data.append({
            'name': 'Final',
            'isSum': True,
            'color': '#434348'
        })
        
        # Create chart options
        options = HighchartsOptions(
            chart={'type': 'waterfall', 'renderTo': chart_id} if chart_id else {'type': 'waterfall'},
            title={'text': title},
            x_axis=XAxis(
                type='category',
                title={'text': 'Steps'}
            ),
            y_axis=YAxis(
                title={'text': 'Total Value'},
                labels={
                    'formatter': 'function() { return this.value.toLocaleString(); }'
                }
            ),
            tooltip={
                'pointFormat': '<b>{point.name}</b><br/>Value: {point.y:,.0f}<br/>Total: {point.stackTotal:,.0f}'
            },
            plot_options={
                'waterfall': {
                    'dataLabels': {
                        'enabled': True,
                        'formatter': '''function() {
                            if (this.point.isSum || this.point.isIntermediateSum) {
                                return this.point.stackTotal.toLocaleString();
                            } else {
                                const percentage = ((this.point.y / this.point.stackTotal) * 100).toFixed(1);
                                return percentage + '%';
                            }
                        }''',
                        'style': {
                            'fontWeight': 'bold'
                        }
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
    
    
    def generate_step_chart_html(self, step_data: Dict, title: str, chart_id: str = None) -> str:
        """Generate HTML for step distribution chart"""
        band_order = self._get_band_order()
        chart = self.create_bar_chart(
            step_data['chart_data'],
            title,
            chart_id,
            band_order
        )
        return chart.to_js_literal()


    def generate_waterfall_chart_html(self, item_name: str, item_data: Dict, summary_stats: Dict, chart_id: str) -> str:
        """Generate HTML/JS for waterfall chart using highcharts_core package"""
        title = f'{item_name} Step Progression Waterfall'
        chart = self.create_waterfall_chart(item_data, summary_stats, title, chart_id)
        
        if not chart:
            return f"// No data available for {item_name} waterfall chart"
        
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
    
    def generate_all_charts_html(self, analysis_data, summary_stats=None):
        """Generate all charts HTML for the analysis data - consistent pattern"""
        charts_html = {}
        
        for item_name, item_analysis in analysis_data.items():
            charts_html[item_name] = {}
            
            # Generate distribution charts for each step (sorted to ensure step 0 comes first)
            sorted_steps = sorted(item_analysis['steps'].keys())
            for step in sorted_steps:
                step_data = item_analysis['steps'][step]
                chart_id = f"{item_name.replace(' ', '_').replace(':', '_').lower()}-step-{step}-chart"
                # Use the consistent generate_step_chart_html pattern
                chart_html = self.generate_step_chart_html(step_data, f"{item_name} - {step_data['step_name']}", chart_id)
                charts_html[item_name][f'step_{step}'] = chart_html
            
            # Generate waterfall chart for this item if summary stats available
            if summary_stats and item_name in summary_stats:
                waterfall_chart_id = f"waterfall-{item_name.replace(' ', '_').replace(':', '_').lower()}-chart"
                waterfall_html = self.generate_waterfall_chart_html(item_name, item_analysis, summary_stats[item_name], waterfall_chart_id)
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
        
        # Segment charts for Dash
        for segment_name, segment_data in analysis_data['summary_by_band_segment'].items():
            dash_charts[segment_name] = self.generate_chart_for_dash(
                segment_data['chart_data'],
                f'{segment_name} - Difference Distribution'
            )
        
        return dash_charts


def generate_dash_compatible_charts(analysis_data: Dict) -> Dict[str, Dict]:
    """Generate chart configurations for Dash (backward compatibility)"""
    generator = ImpactChartGenerator()
    return generator.generate_dash_charts(analysis_data)

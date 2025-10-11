"""
Reusable Dash components for Impact Analysis Dashboard
"""

import dash
from dash import dcc, html, dash_table
import dash_bootstrap_components as dbc
from typing import Dict, List


def create_config_section(config_yaml_str: str) -> dbc.Card:
    """Create the configuration preview/edit section"""
    return dbc.Card([
        dbc.CardHeader(html.H4("Configuration")),
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    dcc.Textarea(
                        id='config-editor',
                        value=config_yaml_str,
                        style={
                            'width': '100%',
                            'height': '300px',
                            'fontFamily': 'monospace',
                            'fontSize': '12px'
                        },
                        placeholder='Configuration YAML will appear here...'
                    )
                ], width=12)
            ]),
            html.Br(),
            dbc.Row([
                dbc.Col([
                    dbc.Button(
                        "Update Configuration",
                        id='btn-update-config',
                        color='primary',
                        className='me-2'
                    ),
                    dbc.Button(
                        "Run Impact Analysis",
                        id='btn-run-analysis',
                        color='success',
                        className='me-2'
                    ),
                    dbc.Button(
                        "Refresh Results",
                        id='btn-refresh-results',
                        color='info',
                        className='me-2',
                        disabled=True
                    ),
                    dbc.Button(
                        "Save as HTML Report",
                        id='btn-save-html',
                        color='warning',
                        className='me-2',
                        disabled=True
                    ),
                    dbc.Button(
                        "Save Data",
                        id='btn-save-data',
                        color='secondary',
                        disabled=True
                    )
                ], width=12)
            ]),
            html.Br(),
            dbc.Alert(
                id='config-status-message',
                children='',
                color='info',
                is_open=False,
                dismissable=True,
                duration=4000
            )
        ])
    ], className='mb-4')


def create_filters_section(filter_columns: List[str], filter_options: Dict[str, List]) -> dbc.Card:
    """Create the filters section with dropdowns for each filter column"""
    if not filter_columns:
        return dbc.Card([
            dbc.CardHeader(html.H4("Filters")),
            dbc.CardBody([
                html.P("No filters configured. Add filter columns in the configuration.", className='text-muted')
            ])
        ], className='mb-4')
    
    filter_controls = []
    for col in filter_columns:
        options = filter_options.get(col, [])
        filter_controls.append(
            dbc.Row([
                dbc.Col([
                    html.Label(col, style={'fontWeight': 'bold'}),
                    dcc.Dropdown(
                        id={'type': 'filter-dropdown', 'column': col},
                        options=[{'label': val, 'value': val} for val in options],
                        value=options,  # All selected by default
                        multi=True,
                        placeholder=f'Select {col}...'
                    )
                ], width=12)
            ], className='mb-3')
        )
    
    return dbc.Card([
        dbc.CardHeader(html.H4("Filters")),
        dbc.CardBody(filter_controls)
    ], className='mb-4')


def create_loading_indicator() -> html.Div:
    """Create a loading indicator"""
    return html.Div([
        dcc.Loading(
            id="loading-analysis",
            type="default",
            children=html.Div(id="loading-output")
        )
    ])


def create_summary_table(dict_comparison_summary: Dict) -> html.Div:
    """Create summary table from comparison summary"""
    if not dict_comparison_summary:
        return html.Div([
            html.P("No data available. Run the impact analysis first.", className='text-muted')
        ])
    
    # Create tabs for each item
    tabs = []
    for item_name, item_data in dict_comparison_summary.items():
        tab_content = _create_item_summary_table(item_data)
        tabs.append(dbc.Tab(tab_content, label=item_name, tab_id=f"summary-tab-{item_name}"))
    
    return dbc.Tabs(tabs, id="summary-tabs", active_tab=f"summary-tab-{list(dict_comparison_summary.keys())[0]}")


def _create_item_summary_table(item_data: Dict) -> dash_table.DataTable:
    """Create a summary table for a single item"""
    # Prepare table data
    # First, collect all stage names for the header row
    sorted_stages = sorted(item_data.keys())
    stage_names = [item_data[stage_idx]['stage_name'] for stage_idx in sorted_stages]
    
    # Create rows in specific order
    rows = []
    
    # Row 1: Total Value
    total_values = [f"{item_data[stage_idx]['value_total']:,.2f}" for stage_idx in sorted_stages]
    rows.append(['Total Value'] + total_values)
    
    # Row 2: Difference
    differences = [f"{item_data[stage_idx]['value_diff']:,.2f}" for stage_idx in sorted_stages]
    rows.append(['Difference'] + differences)
    
    # Row 3: Difference %
    diff_percentages = [f"{item_data[stage_idx]['value_diff_percent']:.2f}%" for stage_idx in sorted_stages]
    rows.append(['Difference %'] + diff_percentages)
    
    # Row 4 (last): Total %
    total_percentages = [f"{item_data[stage_idx]['value_total_percent']:.2f}%" for stage_idx in sorted_stages]
    rows.append(['Total %'] + total_percentages)
    
    # Convert to dictionary format for DataTable
    table_data = []
    columns = [{'name': 'Metric', 'id': 'Metric'}]
    
    # Add stage columns
    for idx, stage_name in enumerate(stage_names):
        col_id = f'stage_{idx}'
        columns.append({'name': stage_name, 'id': col_id})
    
    # Add data rows
    for row in rows:
        row_dict = {'Metric': row[0]}
        for idx, value in enumerate(row[1:]):
            row_dict[f'stage_{idx}'] = value
        table_data.append(row_dict)
    
    # Create and return table
    return dash_table.DataTable(
        data=table_data,
        columns=columns,
        style_table={'overflowX': 'auto'},
        style_cell={
            'textAlign': 'left',
            'padding': '10px',
            'fontFamily': 'Arial, sans-serif'
        },
        style_header={
            'backgroundColor': 'rgb(230, 230, 230)',
            'fontWeight': 'bold',
            'textAlign': 'center'
        },
        style_data_conditional=[
            {
                'if': {'column_id': 'Metric'},
                'fontWeight': 'bold',
                'backgroundColor': 'rgb(240, 240, 240)'
            },
            {
                'if': {'row_index': 3},  # Total % row
                'backgroundColor': 'rgb(220, 235, 255)'
            }
        ]
    )


def create_charts_section(charts_html_dict: Dict, dict_distribution_summary: Dict, dict_comparison_summary: Dict) -> html.Div:
    """Create charts section with item tabs containing summary, waterfall, and distribution sub-tabs"""
    if not charts_html_dict or not dict_distribution_summary:
        return html.Div([
            html.P("No charts available. Run the impact analysis first.", className='text-muted')
        ])
    
    # Create tabs for each item
    item_tabs = []
    
    for item_name, item_charts in charts_html_dict.items():
        # Create content sections for this item
        item_content_sections = []
        
        # Section 1: Summary Table
        item_content_sections.append(html.H2("Summary Table", className='mt-3 mb-3'))
        if item_name in dict_comparison_summary:
            item_summary_table = _create_item_summary_table(dict_comparison_summary[item_name])
            item_content_sections.append(item_summary_table)
        
        # Section 2: Waterfall Chart
        if 'waterfall' in item_charts:
            item_content_sections.append(html.H2("Waterfall Chart", className='mt-4 mb-3'))
            chart_id = f"waterfall-{item_name.replace(' ', '_').lower()}-chart"
            waterfall_html = _create_single_chart_html(
                item_charts['waterfall'],
                chart_id,
                f"{item_name} - Waterfall Chart"
            )
            item_content_sections.append(
                html.Iframe(
                    srcDoc=waterfall_html,
                    style={'width': '100%', 'height': '500px', 'border': 'none'}
                )
            )
        
        # Section 3: Distribution Charts (with step sub-tabs)
        item_content_sections.append(html.H2("Distribution Charts", className='mt-4 mb-3'))
        
        # Create sub-tabs for distribution charts
        step_tabs = []
        if item_name in dict_distribution_summary and 'steps' in dict_distribution_summary[item_name]:
            sorted_steps = sorted(dict_distribution_summary[item_name]['steps'].keys())
            for step_num in sorted_steps:
                step_key = f'step_{step_num}'
                if step_key in item_charts:
                    step_name = dict_distribution_summary[item_name]['steps'][step_num]['step_name']
                    chart_id = f"{item_name.replace(' ', '_').lower()}-step-{step_num}-chart"
                    
                    step_html = _create_single_chart_html(
                        item_charts[step_key],
                        chart_id,
                        f"{item_name} - {step_name}"
                    )
                    
                    step_tabs.append(
                        dbc.Tab(
                            html.Iframe(
                                srcDoc=step_html,
                                style={'width': '100%', 'height': '500px', 'border': 'none'}
                            ),
                            label=step_name,
                            tab_id=f"tab-{item_name}-step-{step_num}"
                        )
                    )
        
        # Add the distribution sub-tabs
        if step_tabs:
            item_content_sections.append(
                dbc.Tabs(
                    step_tabs,
                    id=f"step-tabs-{item_name}",
                    active_tab=step_tabs[0].tab_id if step_tabs else None
                )
            )
        
        # Create the item tab with all sections
        item_tab_content = html.Div(item_content_sections, className='p-3')
        item_tabs.append(
            dbc.Tab(
                item_tab_content,
                label=item_name,
                tab_id=f"item-tab-{item_name}"
            )
        )
    
    if not item_tabs:
        return html.Div([
            html.P("No charts available.", className='text-muted')
        ])
    
    return dbc.Tabs(
        item_tabs,
        id="item-tabs",
        active_tab=item_tabs[0].tab_id if item_tabs else None
    )


def _create_single_chart_html(chart_js: str, chart_id: str, title: str) -> str:
    """Create a standalone HTML document for a single chart"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{title}</title>
        <script src="https://code.highcharts.com/highcharts.js"></script>
        <script src="https://code.highcharts.com/modules/exporting.js"></script>
        <script src="https://code.highcharts.com/highcharts-more.js"></script>
        <style>
            body {{ 
                font-family: Arial, sans-serif; 
                margin: 0; 
                padding: 20px;
                background: white; 
            }}
            .chart-container {{ 
                width: 100%; 
                height: 450px; 
            }}
        </style>
    </head>
    <body>
        <div id="{chart_id}" class="chart-container"></div>
        <script>
            {chart_js}
        </script>
    </body>
    </html>
    """


def create_charts_section_legacy(charts_html: str) -> html.Div:
    """Create charts section from generated HTML"""
    if not charts_html:
        return html.Div([
            html.P("No charts available. Run the impact analysis first.", className='text-muted')
        ])
    
    return html.Div([
        html.Iframe(
            srcDoc=charts_html,
            style={'width': '100%', 'height': '800px', 'border': 'none'}
        )
    ])


def create_results_section() -> dbc.Card:
    """Create the analysis results section"""
    return dbc.Card([
        dbc.CardHeader(html.H4("Analysis Results")),
        dbc.CardBody([
            # Summary tables are now embedded in item tabs, hide this div
            html.Div(id='results-summary-table', style={'display': 'none'}),
            html.Div(id='results-charts')
        ])
    ], className='mb-4')


def create_main_layout(config_yaml_str: str = "", filter_columns: list = None, filter_options: dict = None) -> html.Div:
    """Create the main dashboard layout"""
    if filter_columns is None:
        filter_columns = []
    if filter_options is None:
        filter_options = {}
    
    return dbc.Container([
        html.H1("Impact Analysis Dashboard", className='text-center my-4'),
        
        # Config section - initialized directly
        create_config_section(config_yaml_str),
        
        # Filters section - can be updated via callback
        html.Div(
            id='filters-container',
            children=create_filters_section(filter_columns, filter_options)
        ),
        
        # Loading indicator
        create_loading_indicator(),
        
        # Results section
        create_results_section(),
        
        # Hidden divs for storing state
        dcc.Store(id='data-loaded-flag', data=False),
        dcc.Store(id='filter-state', data={}),
        
    ], fluid=True, style={'maxWidth': '1400px'})

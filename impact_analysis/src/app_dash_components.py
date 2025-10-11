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
    
    tables = []
    for item_name, item_data in dict_comparison_summary.items():
        # Prepare table data
        table_data = []
        for stage_idx in sorted(item_data.keys()):
            stage_info = item_data[stage_idx]
            table_data.append({
                'Stage': stage_info['stage_name'],
                'Total Value': f"{stage_info['value_total']:,.2f}",
                'Total %': f"{stage_info['value_total_percent']:.2f}%",
                'Difference': f"{stage_info['value_diff']:,.2f}",
                'Difference %': f"{stage_info['value_diff_percent']:.2f}%"
            })
        
        tables.append(html.Div([
            html.H5(f"{item_name}", className='mt-3'),
            dash_table.DataTable(
                data=table_data,
                columns=[
                    {'name': 'Stage', 'id': 'Stage'},
                    {'name': 'Total Value', 'id': 'Total Value'},
                    {'name': 'Total %', 'id': 'Total %'},
                    {'name': 'Difference', 'id': 'Difference'},
                    {'name': 'Difference %', 'id': 'Difference %'}
                ],
                style_table={'overflowX': 'auto'},
                style_cell={
                    'textAlign': 'left',
                    'padding': '10px',
                    'fontFamily': 'Arial, sans-serif'
                },
                style_header={
                    'backgroundColor': 'rgb(230, 230, 230)',
                    'fontWeight': 'bold'
                },
                style_data_conditional=[
                    {
                        'if': {'row_index': 'odd'},
                        'backgroundColor': 'rgb(248, 248, 248)'
                    }
                ]
            )
        ]))
    
    return html.Div(tables)


def create_charts_section(charts_html: str) -> html.Div:
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
            html.Div(id='results-summary-table'),
            html.Hr(),
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

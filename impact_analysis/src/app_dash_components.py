"""
Reusable Dash components for Impact Analysis Dashboard
"""

import dash
from dash import dcc, html, dash_table
import dash_bootstrap_components as dbc
from typing import Dict, List
import io
import sys
from collections import deque
import logging


# Global log storage
class LogCapture:
    """Capture logs and stdout/stderr for display in dashboard"""
    def __init__(self, max_lines=1000):
        self.logs = deque(maxlen=max_lines)
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        
    def write(self, message):
        """Capture stdout/stderr writes"""
        if message.strip():  # Only capture non-empty messages
            self.logs.append(message.strip())
        # Also write to original stdout
        self.original_stdout.write(message)
        
    def flush(self):
        """Flush method for stdout compatibility"""
        self.original_stdout.flush()
        
    def get_logs(self):
        """Get all captured logs as a list"""
        return list(self.logs)
    
    def clear_logs(self):
        """Clear all captured logs"""
        self.logs.clear()


# Global log capture instance
log_capture = LogCapture()


class DashLogHandler(logging.Handler):
    """Custom logging handler that writes to log_capture"""
    def emit(self, record):
        log_entry = self.format(record)
        log_capture.logs.append(log_entry)


def create_log_panel() -> dbc.Card:
    """Create a collapsible log panel to display logs and stdout"""
    return dbc.Card([
        dbc.CardHeader([
            html.Div([
                html.H4("Logs", style={'display': 'inline-block', 'marginRight': '15px'}),
                dbc.Button(
                    "Toggle Logs",
                    id='btn-toggle-logs',
                    color='info',
                    size='sm',
                    className='me-2'
                ),
                dbc.Button(
                    "Clear Logs",
                    id='btn-clear-logs',
                    color='secondary',
                    size='sm'
                )
            ])
        ]),
        dbc.Collapse(
            dbc.CardBody([
                html.Div(
                    id='log-display',
                    style={
                        'height': '300px',
                        'overflowY': 'scroll',
                        'backgroundColor': '#1e1e1e',
                        'color': '#d4d4d4',
                        'fontFamily': 'monospace',
                        'fontSize': '12px',
                        'padding': '10px',
                        'whiteSpace': 'pre-wrap',
                        'borderRadius': '4px'
                    }
                )
            ]),
            id='logs-collapse',
            is_open=False
        )
    ], className='mb-4')


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
                        "Load Data",
                        id='btn-run-analysis',
                        color='success',
                        className='me-2'
                    ),
                    dbc.Button(
                        "Update Configuration",
                        id='btn-update-config',
                        color='primary',
                        className='me-2'
                    ),
                    dbc.Button(
                        "(re)Generate Results",
                        id='btn-refresh-results',
                        color='info',
                        className='me-2',
                        disabled=True
                    ),
                    dbc.Button(
                        "Export HTML Report",
                        id='btn-save-html',
                        color='warning',
                        className='me-2',
                        disabled=True
                    ),
                    dbc.Button(
                        "Export Data",
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
                duration=20000  # 20 seconds
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


def create_charts_section(html_report_content: str) -> html.Div:
    """Create charts section using the full HTML report from visualizer.generate_html_report()
    
    Args:
        html_report_content: The complete HTML report content from visualizer.generate_html_report()
        
    Returns:
        html.Div containing an iframe with the full report
    """
    if not html_report_content:
        return html.Div([
            html.P("No report available. Generate the report first.", className='text-muted')
        ])
    
    return html.Div([
        html.Iframe(
            srcDoc=html_report_content,
            style={
                'width': '100%', 
                'height': '1200px',
                'border': '1px solid #dee2e6',
                'borderRadius': '4px'
            }
        )
    ])


def create_results_section() -> dbc.Card:
    """Create the analysis results section"""
    return dbc.Card([
        dbc.CardHeader(html.H4("Analysis Results")),
        dbc.CardBody([
            dcc.Loading(
                id='loading-results',
                type='default',
                children=html.Div(id='results-charts')
            )
        ])
    ], className='mb-4')


def create_filtered_export_section() -> dbc.Card:
    """Create the filtered data export section"""
    return dbc.Card([
        dbc.CardHeader(html.H4("Export Filtered Data")),
        dbc.CardBody([
            html.P("Filter and export data based on rate change thresholds:", className='mb-3'),
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.Span("Output data with ", style={'marginRight': '5px'}),
                        dcc.Dropdown(
                            id='export-item-dropdown',
                            placeholder='Select item...',
                            style={'display': 'inline-block', 'width': '200px', 'height': '38px', 'verticalAlign': 'middle'}
                        ),
                        html.Span("'s ", style={'margin': '0 5px'}),
                        # NB/RN Radio Buttons (hidden by default, shown when renewal is enabled)
                        html.Span(
                            id='export-segment-selector',
                            children=[
                                dcc.RadioItems(
                                    id='export-segment-radio',
                                    options=[
                                        {'label': 'NB', 'value': 'nb'},
                                        {'label': 'RN', 'value': 'rn'}
                                    ],
                                    value='nb',
                                    inline=False,
                                    style={'display': 'inline-block', 'verticalAlign': 'middle', 'lineHeight': '1.3'}
                                )
                            ],
                            style={'display': 'none', 'margin': '5 5px'}  # Hidden by default
                        ),
                        html.Span("rate change in step ", style={'margin': '0 5px'}),
                        dcc.Dropdown(
                            id='export-step-dropdown',
                            placeholder='Select step...',
                            style={'display': 'inline-block', 'width': '150px', 'height': '38px', 'verticalAlign': 'middle'}
                        ),
                        html.Span(" is between ", style={'margin': '0 5px'}),
                        dcc.Input(
                            id='export-from-input',
                            type='number',
                            placeholder='From',
                            step=0.01,
                            style={'display': 'inline-block', 'width': '100px', 'height': '38px', 'verticalAlign': 'middle'}
                        ),
                        html.Span(" and ", style={'margin': '0 5px'}),
                        dcc.Input(
                            id='export-to-input',
                            type='number',
                            placeholder='To',
                            step=0.01,
                            style={'display': 'inline-block', 'width': '100px', 'height': '38px', 'verticalAlign': 'middle'}
                        ),
                        dbc.Button(
                            "Output Data",
                            id='btn-export-filtered',
                            color='primary',
                            style={'display': 'inline-block', 'marginLeft': '10px', 'verticalAlign': 'middle'},
                            disabled=True
                        )
                    ], style={'lineHeight': '2.5'})
                ], width=12)
            ]),
            html.Br(),
            dbc.Alert(
                id='export-status-message',
                children='',
                color='info',
                is_open=False,
                dismissable=True,
                duration=20000
            )
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
        
        # Log panel at the top
        create_log_panel(),
        
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
        
        # Filtered export section
        create_filtered_export_section(),
        
        # Hidden divs for storing state
        dcc.Store(id='data-loaded-flag', data=False),
        dcc.Store(id='filter-state', data={}),
        
        # Interval component for updating logs
        dcc.Interval(
            id='log-interval',
            interval=1000,  # Update every second
            n_intervals=0
        )
        
    ], fluid=True, style={'maxWidth': '1400px'})

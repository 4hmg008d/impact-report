"""
Dash Dashboard for Data Conversion and Impact Analysis Tools
"""

import dash
from dash import dcc, html, Input, Output, State, callback_context
import dash_bootstrap_components as dbc
import pandas as pd
import yaml
import os
import sys
import logging
import io
import base64
from datetime import datetime

# Add the src directory to Python path to import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import existing modules
try:
    from src.converter.main import ModularDataConverter
    from src.impact_analysis.main import ModularImpactAnalyzer
    from src.impact_analysis.chart_generator import generate_dash_compatible_charts
    CONVERTER_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import converter modules: {e}")
    CONVERTER_AVAILABLE = False

# Initialize Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)
app.title = "Data Tools Dashboard"

# Global variables for storing uploaded data
uploaded_data = None
uploaded_mapping = None
conversion_logs = []

# Layout components
def create_navbar():
    """Create the navigation bar"""
    return dbc.NavbarSimple(
        children=[
            dbc.NavItem(dbc.NavLink("Data Conversion", href="/")),
            dbc.NavItem(dbc.NavLink("Impact Analysis", href="/impact-analysis")),
        ],
        brand="Data Tools Dashboard",
        brand_href="/",
        color="primary",
        dark=True,
        sticky="top",
    )

def create_data_conversion_page():
    """Create the data conversion page layout"""
    return html.Div([
        html.H2("Data Conversion Tool", className="mb-4"),
        
        # File Upload Section
        dbc.Card([
            dbc.CardHeader("File Upload"),
            dbc.CardBody([
                html.H5("Input Data File"),
                dcc.Upload(
                    id='upload-data',
                    children=html.Div([
                        'Drag and Drop or ',
                        html.A('Select Files')
                    ]),
                    style={
                        'width': '100%',
                        'height': '60px',
                        'lineHeight': '60px',
                        'borderWidth': '1px',
                        'borderStyle': 'dashed',
                        'borderRadius': '5px',
                        'textAlign': 'center',
                        'margin': '10px'
                    },
                    multiple=False
                ),
                html.Div(id='data-preview', className="mt-3"),
                
                html.H5("Mapping File", className="mt-4"),
                dcc.Upload(
                    id='upload-mapping',
                    children=html.Div([
                        'Drag and Drop or ',
                        html.A('Select Files')
                    ]),
                    style={
                        'width': '100%',
                        'height': '60px',
                        'lineHeight': '60px',
                        'borderWidth': '1px',
                        'borderStyle': 'dashed',
                        'borderRadius': '5px',
                        'textAlign': 'center',
                        'margin': '10px'
                    },
                    multiple=False
                ),
                html.Div(id='mapping-preview', className="mt-3"),
            ])
        ], className="mb-4"),
        
        # Configuration Editor
        dbc.Card([
            dbc.CardHeader("Configuration Editor"),
            dbc.CardBody([
                dcc.Textarea(
                    id='config-editor',
                    style={'width': '100%', 'height': 200},
                    placeholder="Edit configuration here..."
                ),
                dbc.Button("Update Configuration", id='update-config', className="mt-2"),
                html.Div(id='config-status', className="mt-2")
            ])
        ], className="mb-4"),
        
        # Conversion Controls
        dbc.Card([
            dbc.CardHeader("Conversion Controls"),
            dbc.CardBody([
                dbc.Button("Start Conversion", id='start-conversion', color="primary", className="me-2"),
                dbc.Button("Clear Logs", id='clear-logs', color="secondary"),
                html.Div(id='conversion-status', className="mt-3")
            ])
        ], className="mb-4"),
        
        # Log Display
        dbc.Card([
            dbc.CardHeader("Conversion Log"),
            dbc.CardBody([
                html.Div(id='conversion-logs', style={
                    'height': '300px',
                    'overflowY': 'scroll',
                    'border': '1px solid #ddd',
                    'padding': '10px',
                    'backgroundColor': '#f8f9fa',
                    'fontFamily': 'monospace',
                    'fontSize': '12px'
                })
            ])
        ])
    ])

def create_impact_analysis_page():
    """Create the impact analysis page layout"""
    return html.Div([
        html.H2("Impact Analysis Tool", className="mb-4"),
        
        # Configuration Editor
        dbc.Card([
            dbc.CardHeader("Impact Analysis Configuration"),
            dbc.CardBody([
                dcc.Textarea(
                    id='impact-config-editor',
                    style={'width': '100%', 'height': 200},
                    placeholder="Edit impact analysis configuration here..."
                ),
                dbc.Button("Update Configuration", id='update-impact-config', className="mt-2"),
                html.Div(id='impact-config-status', className="mt-2")
            ])
        ], className="mb-4"),
        
        # Analysis Controls
        dbc.Card([
            dbc.CardHeader("Analysis Controls"),
            dbc.CardBody([
                dbc.Button("Run Impact Analysis", id='run-impact-analysis', color="primary", className="me-2"),
                html.Div(id='impact-analysis-status', className="mt-3")
            ])
        ], className="mb-4"),
        
        # Results Display
        dbc.Card([
            dbc.CardHeader("Analysis Results"),
            dbc.CardBody([
                html.Div(id='impact-results', className="mt-3")
            ])
        ])
    ])

# App layout
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    create_navbar(),
    html.Div(id='page-content', className="container mt-4"),
    
    # Hidden divs for storing data
    dcc.Store(id='uploaded-data-store'),
    dcc.Store(id='uploaded-mapping-store'),
    dcc.Store(id='current-config'),
    dcc.Store(id='current-impact-config'),
])

# Callbacks for page navigation
@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/impact-analysis':
        return create_impact_analysis_page()
    else:
        return create_data_conversion_page()

# Callback for data file upload
@app.callback(
    [Output('data-preview', 'children'),
     Output('uploaded-data-store', 'data')],
    [Input('upload-data', 'contents')],
    [State('upload-data', 'filename')]
)
def update_data_preview(contents, filename):
    if contents is None:
        return html.Div("No file uploaded"), None
    
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    
    try:
        if filename.endswith('.csv'):
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
        elif filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(io.BytesIO(decoded))
        else:
            return html.Div("Unsupported file format"), None
        
        # Store the uploaded data
        global uploaded_data
        uploaded_data = df
        
        # Create preview
        preview = html.Div([
            html.H6(f"File: {filename}"),
            html.P(f"Shape: {df.shape[0]} rows × {df.shape[1]} columns"),
            dbc.Table.from_dataframe(df.head(5), striped=True, bordered=True, hover=True, size="sm")
        ])
        
        return preview, df.to_dict('records')
        
    except Exception as e:
        return html.Div(f"Error processing file: {str(e)}"), None

# Callback for mapping file upload
@app.callback(
    [Output('mapping-preview', 'children'),
     Output('uploaded-mapping-store', 'data')],
    [Input('upload-mapping', 'contents')],
    [State('upload-mapping', 'filename')]
)
def update_mapping_preview(contents, filename):
    if contents is None:
        return html.Div("No mapping file uploaded"), None
    
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    
    try:
        if filename.endswith('.xlsx'):
            df = pd.read_excel(io.BytesIO(decoded), sheet_name='column mapping')
        else:
            return html.Div("Mapping file must be Excel format"), None
        
        # Store the uploaded mapping
        global uploaded_mapping
        uploaded_mapping = df
        
        # Create preview
        preview = html.Div([
            html.H6(f"Mapping File: {filename}"),
            html.P(f"Columns: {', '.join(df.columns)}"),
            dbc.Table.from_dataframe(df.head(10), striped=True, bordered=True, hover=True, size="sm")
        ])
        
        return preview, df.to_dict('records')
        
    except Exception as e:
        return html.Div(f"Error processing mapping file: {str(e)}"), None

# Load initial configuration
def load_config_file(config_path):
    """Load configuration from YAML file"""
    try:
        with open(config_path, 'r') as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        return {}

# Initialize configuration editors
@app.callback(
    Output('config-editor', 'value'),
    [Input('url', 'pathname')]
)
def initialize_config_editor(pathname):
    config = load_config_file('config_data_conversion.yaml')
    return yaml.dump(config, default_flow_style=False)

@app.callback(
    Output('impact-config-editor', 'value'),
    [Input('url', 'pathname')]
)
def initialize_impact_config_editor(pathname):
    config = load_config_file('config_impact_analysis.yaml')
    return yaml.dump(config, default_flow_style=False)

# Configuration update callbacks
@app.callback(
    Output('config-status', 'children'),
    [Input('update-config', 'n_clicks')],
    [State('config-editor', 'value')]
)
def update_configuration(n_clicks, config_text):
    if n_clicks is None:
        return ""
    
    try:
        config = yaml.safe_load(config_text)
        with open('config_data_conversion.yaml', 'w') as file:
            yaml.dump(config, file, default_flow_style=False)
        
        return dbc.Alert("Configuration updated successfully!", color="success")
    except Exception as e:
        return dbc.Alert(f"Error updating configuration: {str(e)}", color="danger")

@app.callback(
    Output('impact-config-status', 'children'),
    [Input('update-impact-config', 'n_clicks')],
    [State('impact-config-editor', 'value')]
)
def update_impact_configuration(n_clicks, config_text):
    if n_clicks is None:
        return ""
    
    try:
        config = yaml.safe_load(config_text)
        with open('config_impact_analysis.yaml', 'w') as file:
            yaml.dump(config, file, default_flow_style=False)
        
        return dbc.Alert("Configuration updated successfully!", color="success")
    except Exception as e:
        return dbc.Alert(f"Error updating configuration: {str(e)}", color="danger")

# Log management functions
def add_log_message(message, level="info"):
    """Add a message to the conversion logs"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {level.upper()}: {message}"
    conversion_logs.append(log_entry)
    # Keep only last 100 logs
    if len(conversion_logs) > 100:
        conversion_logs.pop(0)

def get_logs_html():
    """Convert logs to HTML format"""
    return html.Pre("\n".join(conversion_logs[-20:]))  # Show last 20 logs

# Conversion execution callback
@app.callback(
    [Output('conversion-status', 'children'),
     Output('conversion-logs', 'children')],
    [Input('start-conversion', 'n_clicks'),
     Input('clear-logs', 'n_clicks')],
    [State('uploaded-data-store', 'data'),
     State('uploaded-mapping-store', 'data')]
)
def handle_conversion(start_clicks, clear_clicks, data_store, mapping_store):
    ctx = callback_context
    if not ctx.triggered:
        return "", get_logs_html()
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if button_id == 'clear-logs':
        conversion_logs.clear()
        return dbc.Alert("Logs cleared", color="info"), get_logs_html()
    
    if button_id == 'start-conversion':
        if not CONVERTER_AVAILABLE:
            add_log_message("Converter modules not available", "error")
            return dbc.Alert("Converter modules not available", color="danger"), get_logs_html()
        
        if data_store is None:
            add_log_message("No data file uploaded", "error")
            return dbc.Alert("Please upload a data file first", color="warning"), get_logs_html()
        
        add_log_message("Starting data conversion process...")
        
        try:
            # Create converter instance
            converter = ModularDataConverter('config_data_conversion.yaml')
            
            # Execute conversion
            success = converter.convert()
            
            if success:
                add_log_message("Data conversion completed successfully!")
                return dbc.Alert("Conversion completed successfully!", color="success"), get_logs_html()
            else:
                add_log_message("Data conversion failed", "error")
                return dbc.Alert("Conversion failed - check logs for details", color="danger"), get_logs_html()
                
        except Exception as e:
            add_log_message(f"Conversion error: {str(e)}", "error")
            return dbc.Alert(f"Conversion error: {str(e)}", color="danger"), get_logs_html()
    
    return "", get_logs_html()

# Impact analysis callback
@app.callback(
    Output('impact-analysis-status', 'children'),
    [Input('run-impact-analysis', 'n_clicks')]
)
def run_impact_analysis(n_clicks):
    if n_clicks is None:
        return ""
    
    if not CONVERTER_AVAILABLE:
        return dbc.Alert("Impact analysis modules not available", color="danger")
    
    try:
        # Create analyzer instance
        analyzer = ModularImpactAnalyzer('config_impact_analysis.yaml')
        
        # Execute analysis
        success = analyzer.analyze()
        
        if success:
            # Load and display results
            results_html = create_impact_results()
            return html.Div([
                dbc.Alert("Impact analysis completed successfully!", color="success"),
                results_html
            ])
        else:
            return dbc.Alert("Impact analysis failed - check logs for details", color="danger")
            
    except Exception as e:
        return dbc.Alert(f"Impact analysis error: {str(e)}", color="danger")

def create_impact_results():
    """Create HTML for displaying impact analysis results with Highcharts"""
    try:
        # Load band distribution
        band_df = pd.read_csv('impact_analysis/output/band_distribution.csv')
        
        # Create simple table display
        table = dbc.Table.from_dataframe(band_df, striped=True, bordered=True, hover=True)
        
        # Try to generate Highcharts charts if analysis data is available
        try:
            # Load merged data to generate chart data
            merged_df = pd.read_csv('impact_analysis/output/merged_data.csv')
            
            # Create simple chart data from band distribution
            chart_data = []
            for _, row in band_df.iterrows():
                chart_data.append({
                    'name': row['band'],
                    'y': int(row['Count']),
                    'percentage': float(row['Percentage'])
                })
            
            # Generate Highcharts chart configuration
            if CONVERTER_AVAILABLE:
                charts_config = generate_dash_compatible_charts({
                    'overall': {
                        'chart_data': chart_data,
                        'total_policies': len(merged_df),
                        'band_counts': band_df.to_dict('records')
                    },
                    'segment_tabs': {}
                })
                
                # Create Highcharts chart component
                chart_component = dcc.Graph(
                    id='impact-chart',
                    figure={
                        'data': [{
                            'x': [item['name'] for item in chart_data],
                            'y': [item['y'] for item in chart_data],
                            'type': 'bar',
                            'name': 'Policy Count',
                            'text': [f"{item['percentage']}%" for item in chart_data],
                            'textposition': 'auto',
                        }],
                        'layout': {
                            'title': 'Impact Analysis - Band Distribution',
                            'xaxis': {'title': 'Difference Bands'},
                            'yaxis': {'title': 'Number of Policies'},
                            'showlegend': False
                        }
                    }
                )
                
                return html.Div([
                    html.H4("Impact Analysis Results"),
                    chart_component,
                    html.H5("Band Distribution Table"),
                    table,
                    html.P("Full report available at: impact_analysis/output/impact_analysis_report.html")
                ])
        
        except Exception as chart_error:
            print(f"Chart generation error: {chart_error}")
            # Fallback to simple table display
            return html.Div([
                html.H4("Band Distribution Results"),
                table,
                html.P("Full report available at: impact_analysis/output/impact_analysis_report.html")
            ])
        
        return html.Div([
            html.H4("Band Distribution Results"),
            table,
            html.P("Full report available at: impact_analysis/output/impact_analysis_report.html")
        ])
    except Exception as e:
        return html.Div(f"Could not load results: {str(e)}")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8050)

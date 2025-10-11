# Dashboard Extension Guide

## How to Add New Features

### Adding a New Button

**1. Add UI Component** (`app_dash_components.py`)

```python
def create_config_section(config_yaml_str: str) -> dbc.Card:
    # ... existing code ...
    dbc.Button(
        "Your New Button",
        id='btn-your-feature',
        color='info',
        className='me-2'
    ),
    # ... existing code ...
```

**2. Add Callback** (`app_callbacks.py`)

```python
@app.callback(
    Output('some-output', 'children'),
    [Input('btn-your-feature', 'n_clicks')]
)
def your_feature_handler(n_clicks):
    if not n_clicks:
        raise PreventUpdate
    
    # Your logic here
    return "Feature executed!"
```

### Adding a New Display Section

**1. Create Component Function** (`app_dash_components.py`)

```python
def create_your_section() -> dbc.Card:
    return dbc.Card([
        dbc.CardHeader(html.H4("Your Section")),
        dbc.CardBody([
            html.Div(id='your-section-content')
        ])
    ], className='mb-4')
```

**2. Add to Main Layout** (`app_dash_components.py`)

```python
def create_main_layout() -> html.Div:
    return dbc.Container([
        # ... existing sections ...
        html.Div(id='your-section'),
        # ... rest of layout ...
    ])
```

**3. Populate with Callback** (`app_callbacks.py`)

```python
@app.callback(
    Output('your-section', 'children'),
    [Input('some-trigger', 'data')]
)
def populate_your_section(trigger_data):
    return create_your_section()
```

### Adding State Variables

**1. Add to DashboardState Class** (`app_dashboard_state.py`)

```python
class DashboardState:
    def __init__(self):
        # ... existing attributes ...
        self.your_new_data = None
    
    def set_your_data(self, data):
        self.your_new_data = data
```

**2. Use in Callbacks** (`app_callbacks.py`)

```python
from .app_dashboard_state import dashboard_state

def some_callback():
    dashboard_state.set_your_data(some_data)
    value = dashboard_state.your_new_data
```

### Adding a New Filter Type

**1. Update Config Schema** (config YAML)

```yaml
filter:
  - EXISTING_COLUMN
  - NEW_COLUMN

advanced_filters:  # New section
  date_range:
    enabled: true
    column: DATE_COLUMN
```

**2. Create Filter Component** (`app_dash_components.py`)

```python
def create_date_range_filter() -> html.Div:
    return html.Div([
        html.Label("Date Range"),
        dcc.DatePickerRange(
            id='date-range-filter',
            start_date=None,
            end_date=None
        )
    ])
```

**3. Handle Filter in Callback** (`app_callbacks.py`)

```python
@app.callback(
    Output('filter-state', 'data'),
    [Input('date-range-filter', 'start_date'),
     Input('date-range-filter', 'end_date')]
)
def update_date_filter(start_date, end_date):
    # Process date filter
    return {'date_range': (start_date, end_date)}
```

### Adding Export Formats

**1. Add Button** (in config section)

```python
dbc.Button(
    "Export to Excel",
    id='btn-export-excel',
    color='success'
)
```

**2. Create Export Function** (`app_callbacks.py`)

```python
@app.callback(
    Output('status-message', 'children'),
    [Input('btn-export-excel', 'n_clicks')]
)
def export_to_excel(n_clicks):
    if not n_clicks:
        raise PreventUpdate
    
    try:
        filtered_df = dashboard_state.get_filtered_data()
        output_path = "output.xlsx"
        
        with pd.ExcelWriter(output_path) as writer:
            filtered_df.to_excel(writer, sheet_name='Data', index=False)
        
        return f"Exported to {output_path}"
    except Exception as e:
        return f"Export failed: {e}"
```

## Example: Adding Data Preview

Here's a complete example of adding a data preview feature:

### 1. Component (`app_dash_components.py`)

```python
def create_data_preview(df, num_rows=10):
    if df is None or len(df) == 0:
        return html.P("No data available")
    
    return html.Div([
        html.H5(f"Data Preview (first {num_rows} rows)"),
        dash_table.DataTable(
            data=df.head(num_rows).to_dict('records'),
            columns=[{'name': col, 'id': col} for col in df.columns],
            style_table={'overflowX': 'auto'},
            style_cell={'textAlign': 'left', 'padding': '5px'},
            style_header={'backgroundColor': '#f0f0f0', 'fontWeight': 'bold'}
        )
    ])
```

### 2. Add to Layout

```python
def create_main_layout():
    return dbc.Container([
        # ... existing sections ...
        
        dbc.Card([
            dbc.CardHeader(html.H4("Data Preview")),
            dbc.CardBody([
                html.Div(id='data-preview')
            ])
        ], className='mb-4'),
        
        # ... rest of layout ...
    ])
```

### 3. Callback (`app_callbacks.py`)

```python
@app.callback(
    Output('data-preview', 'children'),
    [Input('data-loaded-flag', 'data'),
     Input('btn-refresh-results', 'n_clicks')]
)
def update_data_preview(data_loaded, refresh_clicks):
    if not data_loaded or not dashboard_state.has_data():
        return "Load data first by clicking 'Run Impact Analysis'"
    
    filtered_df = dashboard_state.get_filtered_data()
    return create_data_preview(filtered_df, num_rows=10)
```

## Best Practices

### 1. Error Handling

Always wrap callback logic in try-except:

```python
@app.callback(...)
def my_callback(...):
    try:
        # Your logic
        return result
    except Exception as e:
        logger.error(f"Error in callback: {e}")
        return f"Error: {str(e)}"
```

### 2. Loading States

Use dcc.Loading for long operations:

```python
dcc.Loading(
    id="loading-my-feature",
    type="default",
    children=html.Div(id="my-feature-output")
)
```

### 3. Prevent Initial Callbacks

Use `prevent_initial_call=True` when appropriate:

```python
@app.callback(
    ...,
    prevent_initial_call=True
)
def my_callback(...):
    pass
```

### 4. State Management

Keep global state in DashboardState, not in callbacks:

```python
# Good
dashboard_state.my_data = processed_data

# Bad
global my_data  # Don't use module-level globals
my_data = processed_data
```

### 5. Reuse Existing Functions

Leverage the existing analysis modules:

```python
from ..main import ModularImpactAnalyzer

analyzer = ModularImpactAnalyzer(config_path)
results = analyzer.analyzer.some_existing_method(data)
```

## Testing New Features

1. **Import Test**
   ```python
   python -c "from impact_analysis.src.app_callbacks import register_callbacks"
   ```

2. **Run Dashboard**
   ```bash
   python run_dashboard.py
   ```

3. **Check Browser Console**
   - Open DevTools (F12)
   - Look for JavaScript errors
   - Check Network tab for failed requests

4. **Check Terminal Logs**
   - Look for Python exceptions
   - Verify callback execution

## Common Patterns

### Pattern: Update Multiple Outputs

```python
@app.callback(
    [Output('output1', 'children'),
     Output('output2', 'children'),
     Output('output3', 'disabled')],
    [Input('trigger', 'n_clicks')]
)
def multi_output_callback(n_clicks):
    return "value1", "value2", False
```

### Pattern: Pattern Matching Callbacks

```python
@app.callback(
    Output('result', 'children'),
    [Input({'type': 'dynamic-button', 'index': ALL}, 'n_clicks')]
)
def handle_dynamic_buttons(all_clicks):
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    # Process based on which button was clicked
```

### Pattern: Chained Callbacks

```python
# First callback
@app.callback(
    Output('intermediate-value', 'data'),
    [Input('input1', 'value')]
)
def process_input(value):
    return processed_value

# Second callback uses output of first
@app.callback(
    Output('final-output', 'children'),
    [Input('intermediate-value', 'data')]
)
def generate_output(processed):
    return final_result
```

## Resources

- Dash Documentation: https://dash.plotly.com/
- Dash Bootstrap Components: https://dash-bootstrap-components.opensource.faculty.ai/
- Plotly Python: https://plotly.com/python/
- Highcharts: https://www.highcharts.com/

## Need Help?

- Check existing code in `app_callbacks.py` for examples
- Review Dash documentation for component APIs
- Test changes incrementally
- Use browser DevTools for debugging

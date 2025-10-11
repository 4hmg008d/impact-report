# Impact Analysis Dashboard

An interactive web-based dashboard for running and visualizing impact analysis reports.

## Features

### 1. Configuration Management
- **Preview Configuration**: View current `config_impact_analysis.yaml` settings
- **Edit Configuration**: Modify configuration directly in the dashboard
- **Update Configuration**: Save changes and reload settings with one click

### 2. Data Analysis
- **Run Impact Analysis**: Load data files, calculate comparisons, and generate results
- **In-Memory Storage**: Data is stored in memory for fast re-calculation with different filters
- **Automatic Results**: Summary tables and charts are generated automatically

### 3. Interactive Filters
- **Dynamic Filters**: Filter columns are read from the `filter` parameter in config
- **Multi-Select Dropdowns**: Each filter shows unique values from the data
- **Refresh Results**: Apply filters and recalculate without reloading data

### 4. Visualization
- **Summary Tables**: Total values and differences by stage for each comparison item
- **Waterfall Charts**: Visual representation of value changes through stages
- **Distribution Charts**: Band distribution for each step comparison
- **Interactive Charts**: Powered by Highcharts with zoom, export, and tooltip features

### 5. Export Options
- **Save as HTML Report**: Export current results as timestamped HTML file
- **Save Data**: Export filtered data as CSV files (overwrites existing)

## Installation

1. Install required packages:
```bash
pip install -r requirements.txt
```

Required packages:
- pandas
- openpyxl
- PyYAML
- xlrd
- dash
- dash-bootstrap-components
- plotly
- highcharts-core
- highcharts-maps
- Jinja2

## Usage

### Starting the Dashboard

Run the dashboard using the launcher script:

```bash
python run_dashboard.py
```

Or specify a custom config file:

```bash
python run_dashboard.py path/to/config.yaml
```

The dashboard will start at: `http://127.0.0.1:8050`

### Workflow

1. **Review Configuration**
   - Check the configuration editor
   - Make any necessary changes
   - Click "Update Configuration" to save

2. **Run Analysis**
   - Click "Run Impact Analysis" to load data and calculate results
   - Wait for the success message
   - Results will appear in the "Analysis Results" section

3. **Apply Filters** (Optional)
   - Use the filter dropdowns to select specific values
   - Click "Refresh Results" to recalculate with filtered data
   - Charts and tables will update automatically

4. **Export Results**
   - Click "Save as HTML Report" to create a timestamped HTML file
   - Click "Save Data" to export CSV files (merged_data.csv, summary_table.csv, band_distribution.csv)

## Dashboard Sections

### Configuration Section
- YAML editor for config file
- Buttons for updating config and running analysis

### Filters Section
- Dynamic dropdowns based on `filter` parameter in config
- Each dropdown shows unique values from the data
- Multiple selections allowed per filter

### Analysis Results Section
- **Summary Tables**: Aggregated totals by stage
- **Waterfall Charts**: Stage-by-stage value progression
- **Distribution Charts**: Band distribution for each comparison step

## Configuration File Structure

The dashboard reads `config_impact_analysis.yaml`:

```yaml
filter:
  - LOCATION_CITY
  - PRODUCT_TYPE
  # Add more columns to filter

mapping:
  file_path: data/impact_analysis_config.xlsx
  sheet_band: band
  sheet_input: mapping_column
  sheet_segment: segment

output:
  dir: data/output
```

### Filter Parameter
- Lists column names to create filter dropdowns
- Columns must exist in the merged data
- Each column becomes a multi-select dropdown

## File Structure

```
impact-report/
├── dashboard_app.py              # Main dashboard application
├── run_dashboard.py              # Launcher script
├── impact_analysis/
│   ├── src/
│   │   ├── app_dashboard_state.py    # State management
│   │   ├── app_dash_components.py    # UI components
│   │   ├── app_callbacks.py          # Callback functions
│   │   ├── config_loader.py          # Config handling
│   │   ├── data_processor.py         # Data processing
│   │   ├── analyzer.py               # Analysis logic
│   │   ├── chart_generator.py        # Chart generation
│   │   └── visualizer.py             # HTML report generation
│   ├── config_impact_analysis.yaml   # Configuration file
│   └── data/
│       ├── input/                    # Input Excel files
│       └── output/                   # Generated reports and CSV
```

## Technical Details

### State Management
- `DashboardState` class manages all in-memory data
- Merged data is loaded once and reused for filter operations
- Results are recalculated only when filters change

### Component Architecture
- **app_dashboard_state.py**: Centralized state management
- **app_dash_components.py**: Reusable UI components
- **app_callbacks.py**: Event handlers and business logic
- **dashboard_app.py**: Main application entry point

### Data Flow
1. User clicks "Run Impact Analysis"
2. Data is loaded and merged using existing `ModularImpactAnalyzer`
3. Results are calculated and stored in memory
4. User applies filters and clicks "Refresh Results"
5. Filtered data is extracted from memory
6. Results are recalculated without reloading files

## Troubleshooting

### Dashboard won't start
- Check that all dependencies are installed: `pip install -r requirements.txt`
- Ensure port 8050 is not in use
- Check the console for error messages

### No data appears
- Click "Run Impact Analysis" first to load data
- Check that input files exist in the paths specified in config
- Review console logs for data loading errors

### Filters not showing
- Add column names to the `filter` parameter in config
- Click "Update Configuration" to reload
- Run analysis again to populate filter dropdowns

### Charts not displaying
- Check browser console for JavaScript errors
- Ensure internet connection (Highcharts loads from CDN)
- Try refreshing the browser

## Browser Compatibility

Tested with:
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Performance Notes

- First run loads all data (may take time for large files)
- Subsequent filter operations are fast (data in memory)
- Chart rendering depends on data size
- Consider filtering to reduce data volume for better performance

## Support

For issues or questions:
1. Check the console logs for error messages
2. Review `impact_analysis.log` for detailed logs
3. Verify configuration file syntax
4. Ensure all input files are accessible

# Data Tools Dashboard

A comprehensive Dash-based web interface for data conversion and impact analysis tools.

## Features

### Page 1: Data Conversion
- **File Upload**: Drag and drop input data files (Excel/CSV) with live preview
- **Mapping File Upload**: Upload Excel mapping files with column mapping preview
- **Configuration Editor**: Real-time YAML configuration editor for `config_data_conversion.yaml`
- **Live Logging**: Real-time conversion progress and error display
- **Conversion Controls**: Start conversion and clear logs functionality

### Page 2: Impact Analysis
- **Configuration Editor**: Real-time YAML configuration editor for `config_impact_analysis.yaml`
- **Analysis Controls**: Run impact analysis with results display
- **Results Visualization**: Display band distribution and analysis results

## Installation

1. Install required dependencies:
```bash
pip install -r requirements.txt
```

2. Ensure you have the following files in your project:
- `config_data_conversion.yaml` - Data conversion configuration
- `config_impact_analysis.yaml` - Impact analysis configuration
- Sample data files in `data/input/` directory
- Mapping files in `mapping/` directory

## Usage

1. Start the dashboard:
```bash
python dashboard_app.py
```

2. Open your web browser and navigate to: `http://localhost:8050`

3. Use the navigation bar to switch between:
   - **Data Conversion**: For converting data files using mapping rules
   - **Impact Analysis**: For analyzing differences between benchmark and target files

## Data Conversion Workflow

1. **Upload Data File**: Drag and drop your input data file (Excel or CSV)
2. **Upload Mapping File**: Drag and drop your mapping Excel file (must contain "column mapping" sheet)
3. **Edit Configuration**: Modify the YAML configuration as needed
4. **Start Conversion**: Click "Start Conversion" to begin the process
5. **Monitor Logs**: Watch the live log display for progress and errors

## Impact Analysis Workflow

1. **Edit Configuration**: Modify the impact analysis YAML configuration
2. **Run Analysis**: Click "Run Impact Analysis" to execute the analysis
3. **View Results**: See the band distribution and analysis results

## Configuration Files

### Data Conversion Configuration (`config_data_conversion.yaml`)
```yaml
input:
  file_path: "data/input/sample_data_with_flags.xlsx"
  file_type: "auto"
output:
  file_path: "data/output/converted_data.csv"
  file_type: "csv"
mapping:
  file_path: "mapping/column_mapping.xlsx"
  sheet_name: "column mapping"
processing:
  list_format: "list_in_single_string"
```

### Impact Analysis Configuration (`config_impact_analysis.yaml`)
```yaml
benchmark:
  file_path: "impact_analysis/input/file1.xlsx"
  premium_column: "PREMIUM_AMOUNT"
target:
  file_path: "impact_analysis/input/file2.xlsx"
  premium_column: "PREMIUM_AMOUNT"
id_column: "POLICY_NUMBER"
band_config:
  file_path: "impact_analysis/impact_analysis_config.xlsx"
  sheet_name: "bands"
segment_config:
  file_path: "impact_analysis/impact_analysis_config.xlsx"
  sheet_name: "segments"
output:
  merged_data_path: "impact_analysis/output/merged_data.csv"
  band_distribution_path: "impact_analysis/output/band_distribution.csv"
  report_path: "impact_analysis/output/impact_analysis_report.html"
```

## File Structure

```
data-conversion/
├── dashboard_app.py          # Main dashboard application
├── requirements.txt          # Python dependencies
├── config_data_conversion.yaml    # Data conversion configuration
├── config_impact_analysis.yaml    # Impact analysis configuration
├── src/
│   ├── converter/           # Modular data conversion modules
│   └── impact_analysis/     # Modular impact analysis modules
├── data/
│   ├── input/              # Input data files
│   └── output/             # Output files
├── mapping/                # Column mapping files
└── impact_analysis/        # Impact analysis files
```

## Troubleshooting

- **Module Import Errors**: Ensure all required modules are installed and the `src/` directory structure is correct
- **File Upload Issues**: Check file formats and ensure files are not corrupted
- **Configuration Errors**: Verify YAML syntax in configuration editors
- **Conversion Failures**: Check the live logs for detailed error messages

## Development

The dashboard leverages the existing modular codebase:
- `src/converter/` modules for data conversion
- `src/impact_analysis/` modules for impact analysis

All functionality is integrated through the Dash framework, providing a user-friendly web interface for the underlying Python tools.

# Impact Analysis Tool

A comprehensive tool for generating impact analysis reports comparing benchmark and target files with Highcharts visualization.

## Overview

The Impact Analysis Tool compares data between benchmark and target files, calculates percentage differences, aggregates by segments, maps differences to bands, and generates interactive visualizations.

## Features

- **Highcharts visualization**: Generate interactive bar charts and tables
- **Multiple output formats**: 
  - Merged data in CSV
  - Summarised data tables in CSV
  - HTML dashboard report with tables and charts
- **Flexible input data**: Input data can come from multiple files and different format
- **Deduplication**: Keep only first row for each ID value (handles exploded data)
- **Segment impact**: Impact results by difference segments
- **Band Mapping**: Map differences to predefined bands for analysis

## Assumptions

- **Deduplication**: Column name for the Key columns across all files need to be the same

## Configuration

### Configuration File (`config_impact_analysis.yaml`)

```yaml
output:
  dir: "impact_analysis/output"

mapping:
  file_path: "impact_analysis/impact_analysis_config.xlsx"
  sheet_input: "mapping_column"      # Column mapping sheet
  sheet_segment: "segment"           # Segment columns sheet
  sheet_band: "band"                 # Band definitions sheet
```

### Mapping Configuration (Excel File)

#### Sheet: mapping_column
| ID | Benchmark File | Benchmark Column | Target File | Target Column |
|----|----------------|------------------|-------------|---------------|
| POLICY_NUMBER | impact_analysis/input/file1.xlsx | PREMIUM_AMOUNT | impact_analysis/input/file2.xlsx | PREMIUM_AMOUNT |

#### Sheet: segment
| Segment |
|---------|
| BUILDING_CONSTRUCTION_TYPE |

#### Sheet: band
| From | To | Name |
|------|----|------|
| -1 | -0.9 | [-100%, -90%] |
| -0.9 | -0.8 | [-90%, -80%] |
| ... | ... | ... |

## Usage

```bash
# Run with default configuration
python impact_analysis_tool.py

# Run with custom configuration
python impact_analysis_tool.py my_config.yaml
```

## Output Files

The tool generates the following output files:

### 1. Merged Data (`merged_data.csv`)
- Contains all merged data from benchmark and target files
- Comparison columns prefixed with file names
- Percentage difference column added (`diff_<column_name>`)

### 2. Aggregated by Segments (`aggregated_by_segments.csv`)
- Statistics aggregated by segment columns (count, mean, median, min, max, std)
- One row per segment value with comprehensive statistics

### 3. Band Distribution (`band_distribution.csv`)
- Count and percentage of policies in each difference band
- Shows distribution of impact across predefined bands

### 4. HTML Report (`impact_analysis_report.html`)
- Interactive Highcharts bar chart
- Tabular band distribution data
- Professional formatting and styling



## File Structure

```
impact_analysis/
├── input/
│   ├── file1.xlsx          # Benchmark file
│   └── file2.xlsx          # Target file
├── impact_analysis_config.xlsx  # Configuration mapping
├── output/
│   ├── merged_data.csv           # Merged comparison data
│   ├── aggregated_by_segments.csv # Segment aggregation
│   ├── band_distribution.csv     # Band frequency counts
│   └── impact_analysis_report.html # Interactive report
└── impact_analysis_tool.py       # Main analysis script
```

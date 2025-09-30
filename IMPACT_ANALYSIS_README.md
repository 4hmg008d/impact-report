# Impact Analysis Tool

A comprehensive tool for generating impact analysis reports comparing benchmark and target files with Highcharts visualization.

## Overview

The Impact Analysis Tool compares data between benchmark and target files, calculates percentage differences, aggregates by segments, maps differences to bands, and generates interactive visualizations.

## Features

- **File Comparison**: Compare benchmark and target files based on specified columns
- **Deduplication**: Keep only first row for each ID value (handles exploded data)
- **Percentage Difference Calculation**: Compute (target / benchmark - 1) differences
- **Segment Aggregation**: Aggregate results by specified segment columns
- **Band Mapping**: Map differences to predefined bands for analysis
- **Highcharts Visualization**: Generate interactive bar charts and tables
- **Multiple Output Formats**: CSV data files and HTML reports

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

## Example Analysis

### Input Data Structure
- **Benchmark File**: Original premium amounts (file1.xlsx)
- **Target File**: Modified premium amounts (file2.xlsx)
- **ID Column**: POLICY_NUMBER (used for merging)
- **Comparison Column**: PREMIUM_AMOUNT

### Analysis Process
1. **Deduplication**: Keep only first row per policy number (handle exploded data)
2. **Merging**: Combine benchmark and target data on policy number
3. **Difference Calculation**: Compute percentage differences
4. **Segment Aggregation**: Analyze differences by building construction type
5. **Band Mapping**: Categorize differences into impact bands
6. **Visualization**: Generate interactive charts and reports

### Sample Results

#### Band Distribution Example:
| Band | Count | Percentage |
|------|-------|------------|
| [0%, 10%] | 7 | 35.0% |
| [-10%, 0%] | 3 | 15.0% |
| [50%, 100%] | 2 | 10.0% |
| ... | ... | ... |

#### Segment Aggregation Example:
| Building Type | Count | Mean Diff | Median Diff | Min Diff | Max Diff |
|---------------|-------|-----------|-------------|----------|----------|
| Brick | 8 | -9.16% | -0.67% | -99.4% | +74.6% |
| Steel Frame | 5 | +24.6% | +0.45% | 0% | +106.9% |
| Timber | 4 | +3.08% | -5.98% | -41.5% | +65.8% |

## Customization

### Adding New Segments
1. Edit the `segment` sheet in the mapping Excel file
2. Add new segment column names
3. Ensure columns exist in input files

### Modifying Bands
1. Edit the `band` sheet in the mapping Excel file
2. Adjust band ranges and names as needed
3. Bands should cover the full range of expected differences

### Multiple Comparisons
The tool currently supports single column comparisons. For multiple comparisons:
1. Create separate mapping rows in the `mapping_column` sheet
2. Run the tool multiple times with different configurations
3. Combine results as needed

## Technical Details

### Data Processing
- **Deduplication**: Uses `drop_duplicates()` to keep first row per ID
- **Merging**: Inner join on ID column with file name prefixes
- **Difference Calculation**: Handles division by zero and infinite values
- **Band Mapping**: Flexible band definitions with inclusive/exclusive ranges

### Error Handling
- Comprehensive logging to `impact_analysis.log`
- Graceful handling of missing files and columns
- Validation of input data and configuration

### Visualization
- Uses Highcharts library for interactive charts
- Responsive design for different screen sizes
- Tooltips showing count and percentage details

## Requirements

- Python 3.7+
- pandas
- numpy
- pyyaml
- openpyxl (for Excel file handling)

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

## Use Cases

### Insurance Premium Analysis
- Compare premium changes between different rating models
- Analyze impact by policy segments (building type, location, etc.)
- Identify policies with significant premium changes

### Financial Data Comparison
- Compare financial metrics between periods
- Analyze performance by business segments
- Track changes in key performance indicators

### Data Migration Validation
- Validate data transformations during system migrations
- Compare source and target system outputs
- Identify discrepancies and anomalies

The Impact Analysis Tool provides a comprehensive framework for comparing and analyzing data changes with professional reporting and visualization capabilities.

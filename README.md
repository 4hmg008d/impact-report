# Universal Data Conversion Tool

A flexible Python tool for converting Excel and CSV files between different data formats using configurable mapping rules. Designed specifically for insurance company data but adaptable to any domain.

## Features

- **Universal Format Support**: Handles both Excel (.xlsx, .xls) and CSV files
- **Flexible Column Mapping**: Uses Excel-based mapping files to define column transformations
- **Data Type Conversion**: Supports INTEGER, BIGDEC (float), and TEXT data types
- **Case Insensitive Matching**: Handles variations in column naming (underscores vs spaces)
- **Optional Columns**: Configurable optional fields that can be skipped if missing
- **Modular Architecture**: Clean, maintainable code structure
- **Comprehensive Logging**: Detailed logging for debugging and monitoring

## Project Structure

```
data-conversion/
├── converter.py              # Main conversion script
├── config.yaml               # Default configuration
├── config_csv.yaml           # CSV-specific configuration
├── requirements.txt          # Python dependencies
├── README.md                 # This file
├── mapping/                  # Mapping files
│   ├── column_mapping.xlsx           # Basic mapping
│   └── column_mapping_enhanced.xlsx  # Enhanced mapping with variations
├── data/                     # Sample data
│   ├── input/               # Input files
│   │   ├── sample_data.xlsx
│   │   ├── sample_data.csv
│   │   └── sample_data_variation.csv
│   └── output/              # Generated output files
│       ├── converted_data.csv
│       └── converted_data_from_csv.csv
└── src/                     # Modular source code (alternative implementation)
    ├── config_loader.py
    ├── mapping_loader.py
    ├── data_processor.py
    └── main.py
```

## Quick Start

### 1. Installation

```bash
# Install required packages
pip install -r requirements.txt
```

### 2. Basic Usage

```bash
# Convert using default configuration (Excel input)
python converter.py

# Convert using specific configuration file
python converter.py config_csv.yaml
```

### 3. Configuration

Edit `config.yaml` to specify your input/output files:

```yaml
input:
  file_path: "data/input/sample_data.xlsx"  # Input file path
  file_type: "auto"                         # auto, excel, or csv

output:
  file_path: "data/output/converted_data.csv"  # Output file path
  file_type: "csv"                            # csv or excel

mapping:
  file_path: "mapping/column_mapping.xlsx"    # Mapping file
  sheet_name: "column mapping"                # Excel sheet name

processing:
  skip_optional_columns: false  # Skip optional columns if missing
  strict_validation: true       # Strict validation of required columns
  encoding: "utf-8"             # File encoding
```

### 4. Mapping File Format

The mapping file should be an Excel file with a sheet named "column mapping" containing:

| Original Column | New Column | Data Type | Optional |
|----------------|------------|-----------|----------|
| policy_number | POLICY_NUMBER | TEXT | NO |
| inception_date | INCEPTION_DATE | TEXT | NO |
| premium_amount | PREMIUM_AMOUNT | BIGDEC | NO |
| building_construction_type | BUILDING_CONSTRUCTION_TYPE | TEXT | YES |

**Column Definitions:**
- **Original Column**: Column name in the input file
- **New Column**: Column name in the output file (will be converted to uppercase)
- **Data Type**: INTEGER, BIGDEC (float), or TEXT
- **Optional**: YES/NO - whether the column is required

## Sample Data

The tool includes sample insurance company data with columns like:
- Policy information (number, dates, status)
- Financial data (premiums, sums insured, deductibles)
- Property details (construction type, fire protection, occupancy)
- Location information (city, state)
- Risk assessment (category, underwriting year)

## Data Types

- **INTEGER**: Whole numbers (supports NaN values)
- **BIGDEC**: Floating-point numbers for financial data
- **TEXT**: String data with proper NaN handling
- **LIST**: Combines multiple flag columns (1/0 values) into a single list column

### LIST Data Type Special Feature

The LIST data type allows you to combine multiple flag columns into a single list column. This is particularly useful for fire protection factors or other categorical flags.

**Example Usage:**
- Multiple input columns: `smoke_alarm`, `fire_extinguisher`, `fire_blanket`, `sprinkler_system`, `fire_hydrant`
- All map to the same output column: `FIRE_PROTECTION` with data type `LIST`
- Result: `['smoke_alarm', 'fire_extinguisher']` (when both flags are 1)

**Mapping File Example:**
| Original Column | New Column | Data Type | Optional |
|----------------|------------|-----------|----------|
| smoke_alarm | FIRE_PROTECTION | LIST | YES |
| fire_extinguisher | FIRE_PROTECTION | LIST | YES |
| fire_blanket | FIRE_PROTECTION | LIST | YES |
| sprinkler_system | FIRE_PROTECTION | LIST | YES |
| fire_hydrant | FIRE_PROTECTION | LIST | YES |

**Input Data:**
- Flag columns should contain `1` (present) or `0` (absent)
- Multiple columns can map to the same LIST column

**Configuration Options:**
- **list_in_multiple_rows**: Explodes list items into separate rows
- **list_in_single_string**: Keeps list items as semicolon-separated string in single row

**Output Result for list_in_multiple_rows:**
- **Exploded Format**: Each list item becomes a separate row
- **First Row**: Keeps all original column values intact
- **Subsequent Rows**: Only policy number and list item are preserved; other columns set to NA
- **Policy Number Fill Down**: Policy number is maintained across all related rows
- **Individual Items**: The list column contains single items instead of lists
- **Empty Lists**: Preserved as single row with all values intact

**Example Transformation (list_in_multiple_rows):**
```
Before Explosion:
POLICY_NUMBER | FIRE_PROTECTION | OTHER_COLUMNS
POL2001       | ['smoke_alarm', 'fire_extinguisher', 'fire_blanket'] | data...

After Explosion:
POLICY_NUMBER | FIRE_PROTECTION | OTHER_COLUMNS
POL2001       | smoke_alarm     | data... (all values preserved)
POL2001       | fire_extinguisher | NA (only policy number and list item)
POL2001       | fire_blanket    | NA (only policy number and list item)
```

**Output Result for list_in_single_string:**
- **Single Row Format**: All list items remain in the same row
- **Semicolon-Separated**: Items are separated by semicolons (e.g., "item1;item2;item3")
- **Empty String**: Empty lists are represented as empty string `""` instead of `[]`
- **All Values Preserved**: All column values remain intact in their original rows

**Example Transformation (list_in_single_string):**
```
Before Conversion:
POLICY_NUMBER | FIRE_PROTECTION | OTHER_COLUMNS
POL2001       | ['smoke_alarm', 'fire_extinguisher', 'fire_blanket'] | data...

After Conversion:
POLICY_NUMBER | FIRE_PROTECTION | OTHER_COLUMNS
POL2001       | smoke_alarm;fire_extinguisher;fire_blanket | data... (all values preserved)
```

## Advanced Features

### Flexible Column Name Matching

The tool automatically handles variations in column naming:
- Case insensitive matching
- Underscore/space variations (e.g., "policy_number" ↔ "policy number")
- Uses enhanced mapping file for maximum compatibility

### Error Handling

- Comprehensive validation of input data against mapping requirements
- Detailed logging in `conversion.log`
- Graceful handling of missing optional columns
- Strict validation mode for production use

### Customization

The modular architecture allows for easy extension:
- Add new data types by extending the conversion methods
- Custom validation rules
- Support for additional file formats

## Usage Examples

### Convert Excel to CSV
```bash
python converter.py
```

### Convert CSV to Excel
```bash
python converter.py config_csv.yaml
```

### Custom Configuration
```bash
python converter.py my_custom_config.yaml
```

## Troubleshooting

### Common Issues

1. **Missing Required Columns**: Ensure all required columns are present in the input file
2. **File Not Found**: Check file paths in configuration
3. **Data Type Conversion Errors**: Verify data types in mapping file match actual data
4. **Encoding Issues**: Adjust encoding in configuration for non-UTF-8 files

### Logs

Check `conversion.log` for detailed processing information and error messages.

## Development

The tool is built with modularity in mind:

- `converter.py`: Standalone conversion script
- `src/` directory: Modular implementation for larger projects
- Extensible architecture for custom requirements

## License

This tool is provided as-is for data conversion purposes. Feel free to modify and adapt for your specific needs.

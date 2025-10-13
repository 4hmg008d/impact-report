# Renewal Feature Implementation Summary

## Overview
This document summarizes the implementation of the renewal feature for the impact analysis tool. The renewal feature allows users to compare New Business and Renewal segments side-by-side in grouped column charts.

## Changes Made

### 1. Configuration Updates

#### YAML Configuration (`config_impact_analysis.yaml`)
- Added a new `features` section with a `renewal` flag:
  ```yaml
  features:
    renewal: true
  ```

#### Excel Configuration (`impact_analysis_config.xlsx`)
- **Tab: `mapping_column`**: Added a new column `RNColumn` to specify the renewal column for each stage
- **Tab: `segment_columns`**: New sheet listing non-premium columns to keep in the merged data (when renewal is enabled)

### 2. Code Changes

#### 2.1 `config_loader.py`
Added three new methods:

- **`load_segment_columns()`**: Loads the list of segment columns from the `segment_columns` sheet in the Excel config file. These columns define which non-premium columns should be retained in the merged data when renewal is enabled.

- **`is_renewal_enabled()`**: Checks if the renewal feature is enabled by reading the `features.renewal` flag from the YAML config.

#### 2.2 `data_processor.py`
Updated multiple methods to handle renewal columns:

- **`generate_comparison_mapping()`**: 
  - Extended to read `RNColumn` from the mapping file
  - Stores renewal column information in `comparison_mapping[item]['renewal_columns']`
  - Adds `renewal_enabled` flag to each item in the mapping
  - Renewal columns are renamed with `_rn` suffix (e.g., `Premium_1_rn`)

- **`load_and_merge_data()`**: 
  - When renewal is enabled, filters the merged data to keep only segment columns (defined in `segment_columns` sheet)
  - Picks the first occurrence of each segment column across all files
  - Merges renewal columns alongside regular comparison columns
  - Renames renewal columns with the `_rn` suffix

- **`generate_differences()`**: 
  - Calculates renewal differences for each step (e.g., `diff_{Item}_step_{N}_rn`)
  - Calculates renewal percentage differences (e.g., `percent_diff_{Item}_step_{N}_rn`)
  - Stores renewal difference information in `comparison_mapping[item]['renewal_differences']`
  - Maintains the same step numbering logic as regular differences

#### 2.3 `data_analyser.py`
Updated `generate_distribution_summary()`:

- Checks if renewal is enabled for each item
- Calculates separate band distributions for New Business (regular) and Renewal segments
- Stores renewal chart data in `dict_distribution_summary[item]['steps'][step]['renewal_chart_data']`
- Stores renewal summary by band in `dict_distribution_summary[item]['steps'][step]['renewal_summary_by_band']`
- Adds `renewal_enabled` flag to each item in the distribution summary

#### 2.4 `chart_generator.py`
Updated chart generation to support grouped column charts:

- **`create_bar_chart()`**: 
  - Added `renewal_enabled` and `renewal_chart_data` parameters
  - When renewal is enabled, creates two series: "New Business" (blue) and "Renewal" (green)
  - Uses shared tooltip to display both series' data
  - Maintains original single-series behavior when renewal is disabled
  - Properly orders bands for both series

- **`generate_all_charts_html()`**: 
  - Checks renewal_enabled flag for each item
  - Passes renewal chart data to `create_bar_chart()` when available
  - Generates grouped column charts for distribution analysis
  - Waterfall charts remain unchanged (only show overall values, not split by renewal)

#### 2.5 Integration Files
No changes required for:
- `main.py`: Uses existing analyzer methods which now handle renewal automatically
- `visualizer.py`: Uses chart generator which now supports renewal
- `app_callbacks.py`: Uses analyzer methods which handle renewal automatically
- Dashboard components: Work with the new chart structure automatically

## Data Flow

### With Renewal Enabled:

1. **Configuration Loading**:
   - Config loader reads `features.renewal: true` from YAML
   - Loads `RNColumn` mapping from Excel config
   - Loads segment columns list from Excel config

2. **Data Processing**:
   - Load and deduplicate all data files
   - Filter to keep only segment columns + ID column (first occurrence)
   - Merge premium columns with standard naming: `{Item}_{Stage}`
   - Merge renewal columns with standard naming: `{Item}_{Stage}_rn`

3. **Difference Calculation**:
   - Calculate differences for New Business: `diff_{Item}_step_{N}`
   - Calculate differences for Renewal: `diff_{Item}_step_{N}_rn`
   - Calculate percentage differences for both segments

4. **Distribution Analysis**:
   - Map New Business differences to bands
   - Map Renewal differences to bands
   - Generate separate chart data for each segment

5. **Chart Generation**:
   - Create grouped column charts with two series
   - New Business series in blue
   - Renewal series in green
   - Both series share the same band categories (x-axis)

6. **Visualization**:
   - HTML report displays grouped charts for distribution analysis
   - Waterfall charts show overall values only (not split by renewal)

## Configuration Requirements

To use the renewal feature, users must:

1. Set `features.renewal: true` in `config_impact_analysis.yaml`

2. In Excel config file (`impact_analysis_config.xlsx`):
   - **Tab `mapping_column`**: Add `RNColumn` column with renewal column names for each stage
   - **Tab `segment_columns`**: Create new sheet listing non-premium columns to keep in merged data

3. Ensure data files contain both regular and renewal columns as specified in the mapping

## Testing Checklist

Before marking this feature as complete, verify:

- [ ] Config loader correctly reads renewal flag and segment columns
- [ ] Data processor correctly filters and merges renewal columns
- [ ] Renewal columns are renamed with `_rn` suffix
- [ ] Differences are calculated for both New Business and Renewal
- [ ] Distribution analysis generates separate band summaries
- [ ] Grouped column charts display correctly with two series
- [ ] Waterfall charts remain unchanged (not split by renewal)
- [ ] Dashboard integration works correctly with renewal feature
- [ ] CSV outputs include renewal columns and differences
- [ ] HTML report displays grouped charts correctly

## Backward Compatibility

The renewal feature is fully backward compatible:

- If `features.renewal` is not set or set to `false`, the tool works as before
- Existing config files without renewal settings continue to work
- No changes to existing workflows when renewal is not enabled

## Notes

- Waterfall charts intentionally do not show renewal split as they focus on overall stage-to-stage impacts
- The renewal feature only affects distribution charts (band analysis)
- Segment columns filtering only applies when renewal is enabled
- The `_rn` suffix is used consistently for all renewal-related columns and differences

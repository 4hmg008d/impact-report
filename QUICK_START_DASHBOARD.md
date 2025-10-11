# Quick Start Guide - Impact Analysis Dashboard

## Installation

```bash
pip install -r requirements.txt
```

## Run the Dashboard

```bash
python run_dashboard.py
```

Then open: **http://127.0.0.1:8050**

## Quick Test

```bash
python test_dashboard.py
```

## Button Guide

| Button | Action | When to Use |
|--------|--------|-------------|
| **Update Configuration** | Saves edited YAML config | After editing config in the text area |
| **Run Impact Analysis** | Loads data & performs analysis | First step - loads all data into memory |
| **Refresh Results** | Recalculates with current filters | After changing filter selections |
| **Save as HTML Report** | Exports timestamped HTML | To save current results for sharing |
| **Save Data** | Exports CSV files | To get raw data (overwrites existing) |

## Typical Workflow

```
1. Edit config (if needed) → Update Configuration
2. Run Impact Analysis (loads data)
3. Select filter values → Refresh Results
4. Review charts and tables
5. Save as HTML Report or Save Data
```

## Filter Behavior

- All values selected by default
- Deselect values to exclude from analysis
- Must click "Refresh Results" to apply changes
- Data stays in memory (fast recalculation)

## Export Files

### HTML Reports (timestamped)
- `impact_analysis_report_20251011_184530.html`
- Preserves all previous exports

### CSV Files (overwrite)
- `merged_data.csv` - All merged records
- `summary_table.csv` - Aggregated totals
- `band_distribution.csv` - Distribution by bands

## Troubleshooting

**Dashboard won't start?**
- Check: `pip install -r requirements.txt`
- Verify: `python test_dashboard.py`

**No filters showing?**
- Add columns to `filter:` section in config.yaml
- Click "Run Impact Analysis" to load data

**Results not updating?**
- Click "Refresh Results" after filter changes
- Ensure data was loaded first

## Config Format

```yaml
filter:
  - COLUMN_NAME_1
  - COLUMN_NAME_2

mapping:
  file_path: data/impact_analysis_config.xlsx
  sheet_band: band
  sheet_input: mapping_column
  sheet_segment: segment

output:
  dir: data/output
```

## Support

- Full documentation: `DASHBOARD_README.md`
- Implementation details: `DASHBOARD_IMPLEMENTATION_SUMMARY.md`
- Impact analysis guide: `IMPACT_ANALYSIS_README.md`

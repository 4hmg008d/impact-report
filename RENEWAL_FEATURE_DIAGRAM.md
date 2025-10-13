# Renewal Feature Data Flow Diagram

## Overview Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    RENEWAL FEATURE ENABLED                       │
│                  (features.renewal: true)                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    1. CONFIGURATION LOADING                      │
├─────────────────────────────────────────────────────────────────┤
│  • Read YAML: features.renewal flag                             │
│  • Load Excel mapping: Item, Stage, Column, RNColumn            │
│  • Load segment_columns: List of columns to keep                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    2. DATA LOADING & FILTERING                   │
├─────────────────────────────────────────────────────────────────┤
│  • Load all data files                                          │
│  • Deduplicate by ID column                                     │
│  • Filter to keep only segment columns + ID                     │
│  • Pick first occurrence of each segment column                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    3. COLUMN MERGING & RENAMING                  │
├─────────────────────────────────────────────────────────────────┤
│  New Business Columns:        Renewal Columns:                  │
│  • Premium → Premium_1         • Premium_RN → Premium_1_rn      │
│  • Premium → Premium_2         • Premium_RN → Premium_2_rn      │
│                                                                  │
│  Result: merged_df with both NB and RN columns                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    4. DIFFERENCE CALCULATION                     │
├─────────────────────────────────────────────────────────────────┤
│  New Business:                 Renewal:                          │
│  • diff_Premium_step_0        • diff_Premium_step_0_rn          │
│  • diff_Premium_step_1        • diff_Premium_step_1_rn          │
│  • percent_diff_...           • percent_diff_..._rn             │
│                                                                  │
│  Result: merged_df with both NB and RN differences              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    5. BAND DISTRIBUTION ANALYSIS                 │
├─────────────────────────────────────────────────────────────────┤
│  For Each Step:                                                  │
│  ┌─────────────────────┐    ┌─────────────────────┐            │
│  │   New Business      │    │      Renewal        │            │
│  │   Band Mapping      │    │   Band Mapping      │            │
│  │   Count & %         │    │   Count & %         │            │
│  └─────────────────────┘    └─────────────────────┘            │
│                                                                  │
│  Result: dict_distribution_summary with both datasets           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    6. CHART GENERATION                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Distribution Charts (Grouped):                                  │
│  ┌────────────────────────────────────────┐                     │
│  │  Band      │  NB   │  RN   │           │                     │
│  │  -10 to -5 │  ███  │  ██   │ Blue      │                     │
│  │   -5 to 0  │  ████ │  ███  │ Green     │                     │
│  │    0 to 5  │  █████│  ████ │           │                     │
│  └────────────────────────────────────────┘                     │
│                                                                  │
│  Waterfall Charts (Unchanged):                                   │
│  ┌────────────────────────────────────────┐                     │
│  │  Stage1 →  Impact  →  Stage2           │                     │
│  │   ███      +10       ███                │                     │
│  │   ███       →        ███                │                     │
│  └────────────────────────────────────────┘                     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    7. OUTPUT GENERATION                          │
├─────────────────────────────────────────────────────────────────┤
│  • HTML Report: Grouped charts + Waterfall charts               │
│  • merged_data.csv: All columns including _rn                   │
│  • band_distribution.csv: Both NB and RN distributions          │
│  • summary_table.csv: Overall statistics                        │
└─────────────────────────────────────────────────────────────────┘
```

## Data Structure Flow

```
CONFIG FILES
├── config_impact_analysis.yaml
│   └── features:
│       └── renewal: true
│
└── impact_analysis_config.xlsx
    ├── mapping_column tab
    │   ├── Item
    │   ├── Stage
    │   ├── Column
    │   └── RNColumn  ← NEW
    │
    └── segment_columns tab  ← NEW
        └── ColumnName
            ├── POLICY_NUMBER
            ├── LOCATION_CITY
            └── ...

                ↓

COMPARISON MAPPING
{
  "Premium": {
    "renewal_enabled": true,  ← NEW
    "stages": {
      1: {
        "renamed_column": "Premium_1",
        ...
      },
      2: {
        "renamed_column": "Premium_2",
        ...
      }
    },
    "renewal_columns": {  ← NEW
      1: {
        "original_column": "PREMIUM_RN",
        "renamed_column": "Premium_1_rn",
        ...
      },
      2: {
        "original_column": "PREMIUM_RN",
        "renamed_column": "Premium_2_rn",
        ...
      }
    },
    "differences": {
      0: {...},  // Overall
      1: {...}   // Step 1
    },
    "renewal_differences": {  ← NEW
      0: {...},  // Overall
      1: {...}   // Step 1
    }
  }
}

                ↓

MERGED DATAFRAME
┌──────────────┬──────────┬───────────┬──────────────┬──────────────┐
│ POLICY_NUMBER│ LOCATION │ Premium_1 │ Premium_1_rn │ Premium_2    │...
├──────────────┼──────────┼───────────┼──────────────┼──────────────┤
│ POL001       │ Sydney   │ 1000      │ 1100         │ 1050         │...
│ POL002       │ Melbourne│ 1500      │ 1450         │ 1600         │...
└──────────────┴──────────┴───────────┴──────────────┴──────────────┘

WITH DIFFERENCES:
┌─────────────┬──────────┬────────────────┬───────────────────────┐
│ Premium_1   │ Premium_2│ diff_Premium_1 │ diff_Premium_1_rn     │...
├─────────────┼──────────┼────────────────┼───────────────────────┤
│ 1000        │ 1050     │ 50             │ -50                   │...
│ 1500        │ 1600     │ 100            │ 150                   │...
└─────────────┴──────────┴────────────────┴───────────────────────┘

                ↓

DISTRIBUTION SUMMARY
{
  "Premium": {
    "renewal_enabled": true,  ← NEW
    "steps": {
      0: {
        "step_name": "Overall",
        "chart_data": [  // New Business
          {"name": "-10% to -5%", "y": 10, "percentage": 15.2},
          {"name": "-5% to 0%", "y": 20, "percentage": 30.5},
          ...
        ],
        "renewal_chart_data": [  ← NEW // Renewal
          {"name": "-10% to -5%", "y": 5, "percentage": 7.6},
          {"name": "-5% to 0%", "y": 15, "percentage": 22.9},
          ...
        ]
      }
    }
  }
}

                ↓

CHARTS
┌──────────────────────────────────┐
│  Distribution Chart (Grouped)    │
│                                  │
│   ██  ██        New Business     │
│   ██  ██  ██    Renewal          │
│   ██  ██  ██  ██                 │
│  -10  -5   0   5                 │
└──────────────────────────────────┘

┌──────────────────────────────────┐
│  Waterfall Chart (Unchanged)     │
│                                  │
│  ███       +10                   │
│  ███  ──►  ███                   │
│  Stage1    Stage2                │
└──────────────────────────────────┘
```

## Key Differences: With vs Without Renewal

```
┌─────────────────────────────────────────────────────────────────┐
│                   WITHOUT RENEWAL (Original)                     │
├─────────────────────────────────────────────────────────────────┤
│  • All columns from first file kept                             │
│  • Single set of premium columns                                │
│  • Single set of differences                                    │
│  • Single series charts                                         │
│  • One band distribution per step                               │
└─────────────────────────────────────────────────────────────────┘

                            ▼ vs ▼

┌─────────────────────────────────────────────────────────────────┐
│                    WITH RENEWAL (New Feature)                    │
├─────────────────────────────────────────────────────────────────┤
│  • Only segment columns kept (filtered)                         │
│  • Two sets of premium columns (NB + RN)                        │
│  • Two sets of differences (NB + RN)                            │
│  • Grouped charts with two series                               │
│  • Two band distributions per step (NB + RN)                    │
└─────────────────────────────────────────────────────────────────┘
```

## Component Interactions

```
┌──────────────┐
│ ConfigLoader │
└──────┬───────┘
       │ provides config & flags
       ▼
┌──────────────┐     reads      ┌──────────────┐
│DataProcessor │ ─────────────► │    Data      │
└──────┬───────┘                │    Files     │
       │ merged_df +            └──────────────┘
       │ comparison_mapping
       ▼
┌──────────────┐
│DataAnalyser  │
└──────┬───────┘
       │ dict_distribution_summary +
       │ dict_comparison_summary
       ▼
┌──────────────┐
│ChartGenerator│
└──────┬───────┘
       │ charts_html
       ▼
┌──────────────┐
│ Visualizer   │
└──────┬───────┘
       │ HTML report
       ▼
┌──────────────┐
│  Dashboard   │
└──────────────┘
```

## Legend

```
┌────┐  Component/Module
│    │
└────┘

────►  Data flow direction

 ↓     Sequential step

 ...   Continued/More items

 ██    Chart bar

 ─rn   Renewal suffix identifier
```

# Dashboard Refactoring - Using Full HTML Report

## Summary of Changes

The dashboard has been refactored to use the complete HTML report from `visualizer.generate_html_report()` instead of generating individual charts and tabs separately.

## What Changed

### 1. `app_dash_components.py`

**Before:**
- `create_charts_section()` took three parameters: `charts_html_dict`, `dict_distribution_summary`, `dict_comparison_summary`
- Built complex tab structure with individual iframes for each chart
- Generated summary tables, waterfall charts, and distribution charts separately

**After:**
- `create_charts_section()` now takes one parameter: `html_report_content`
- Displays the complete HTML report in a single iframe
- Simpler, cleaner implementation

**Legacy Function:**
- The old implementation is preserved as `create_charts_section_legacy()` for reference

### 2. `app_callbacks.py` - `refresh_results` callback

**Before:**
```python
# Generate charts with tabs and sub-tabs
charts_html_dict = analyzer.visualizer.chart_generator.generate_all_charts_html(
    dict_distribution_summary, dict_comparison_summary
)

# Create charts display with new tab-based layout including summary tables
charts_display = create_charts_section(
    charts_html_dict, 
    dict_distribution_summary,
    dict_comparison_summary
)
```

**After:**
```python
# Generate full HTML report using visualizer
html_report_content = analyzer.visualizer.generate_html_report(
    dict_distribution_summary, dict_comparison_summary
)

# Create charts display with full HTML report
charts_display = create_charts_section(html_report_content)
```

## Benefits

1. **Consistency**: The dashboard now shows exactly the same report as the saved HTML file
2. **Simplicity**: Reduced complexity - single iframe instead of nested tabs with multiple iframes
3. **Maintainability**: Single source of truth for report rendering (Jinja2 template)
4. **Less Code**: Removed redundant chart generation and tab building logic
5. **Better UX**: Users see the same layout whether viewing in dashboard or saved HTML

## Technical Details

### Display Settings

The report is displayed in an iframe with the following styling:
- Width: 100%
- Height: 1200px (adjustable if needed)
- Border: 1px solid border with rounded corners
- Scrollable if content exceeds height

### Template Path

The visualizer uses the Jinja2 template located at:
- `impact_analysis/templates/report_template.html`

The template is loaded correctly via `ModularImpactAnalyzer` which sets the proper template directory path.

## How to Adjust

### Change Iframe Height

In `app_dash_components.py`, modify the style in `create_charts_section()`:

```python
html.Iframe(
    srcDoc=html_report_content,
    style={
        'width': '100%', 
        'height': '1500px',  # <-- Change this value
        'border': '1px solid #dee2e6',
        'borderRadius': '4px'
    }
)
```

### Revert to Legacy Tab-based Layout

If you need to revert to the old tab-based layout:

1. In `app_dash_components.py`: Rename `create_charts_section_legacy` back to `create_charts_section`
2. In `app_callbacks.py`: Change the callback to use the old pattern:

```python
charts_html_dict = analyzer.visualizer.chart_generator.generate_all_charts_html(
    dict_distribution_summary, dict_comparison_summary
)
charts_display = create_charts_section(
    charts_html_dict, 
    dict_distribution_summary,
    dict_comparison_summary
)
```

## Testing

To test the changes:

1. Run the dashboard: `python run_dashboard.py`
2. Load a configuration and run the analysis
3. Click "Refresh Results" to see the full HTML report
4. Verify that all charts, tables, and data display correctly
5. Compare with the saved HTML file (should be identical)

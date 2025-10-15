# Data Converter

Using python, write me a tool to universally convert one data format into another. The input file can be either excel files or CSV files. This tool needs to be compatible with both format.

There should be a mapping file mapping original column names to new column names. The mapping file is in xlsx format, tab name is "column mapping". This tab should contain 4 columns. The first column lists out all the column names in the original data file; the second column list out or the column names in the new data file; the third column list out all the data type in the new data file; the fourth column indicates whether the column in the new format is optional

There is no restriction on the input file column names but in the new file, all the column headers needs to be in uppercase, datatypes are also in uppercase, it can be INTEGER, BIGDEC for float, TEXT

There should be a config.yaml file containing all the configurations which include the file path to the input data file. And file path to the new data file.

The python code needs to be modularised for flexibility purpose

Put all the required packages into requirements.txt file

Set up the code structure and some sample input and output files as well as the mapping file for me. This is insurance company data, so in the sample you want to include columns like inception date, expiry date, building construction type, building fire protection factors, and so on

---

In my input file there could be multiple columns of fire protection factors such as smoke alarm, fire extinguisher, fire blanket. These columns will be in the form of flags with values 1 or 0. In the new format these multiple columns will be coerced into a list, so in the mapping file or three column names will be mapped into the same column name called fire protection and the data type should be 'LIST', the list should contain the column name as values whenever the flag is one, implement this in the code

---

When there's a list in the output, it needs to be exploded with each value in a separate columns, and all other columns should be NA, except for the policy number column, which should fill down

---

Sorry not all NA, values in the other columns should remain there for the first row, then for the second and below rows when list expanded, they should be NA

---

The previous "whole list as text string" format is also useful, create a new parameter in the config.yaml to specify which format to use - "list_in_single_string" or "list_in_multiple_rows".

When "list_in_single_string" is specified, instead of "[item1,item2,item3]", the value should present as this format: "item1;item2;item3", if empty list, then it will be empty string ""

---

When format is "list_in_multiple_rows", if empty list, then it will be empty string "" instead of "[]"

---

I've updated my mapping_column.xlsx to rename the data types:
- TEXT to CODE (validation rules: all capital letter, no longer than 12 chars including space)
- INTEGER to INTEGE, validation rules: raise error if longer than 12 digits
- BIGDEC to DECIMA: float with max 4 decimal places and max 12 digit long (total number of digits on both sides of decimal point), round to 4 dp if longer, and raise error if total length (exclusive of the decimal point) is longer than 12

New types:
- DATE: text in the format of 'dd/mm/yyyy', convert to this format if data provided was integer, use Excel origin date

New column:
- List: indicate whether a field is part of a list, this flag replaces the LIST type, each value in a list should follow the data type provided in the previous column

---

## Impact Analysis

Now i want to generate an impact analysis report based on this output, I've created a new config file for this - "config_impact_analysis.yaml", in there:

I've specified a mapping file with a "sheet_input" parameter indicating the tab containing the following data:

The input files required for this exercise are in "Benchmark File" and "Target File" columns, and the columns needed for assessing the impact are specified in the "Benchmark Column" and "Target Column" columns, the values specified in the same row are to be compared against each other, i.e. You want compare values in column "PREMIUM_AMOUNT" from the target file against column "PREMIUM_AMOUNT" in the benchmark file. Your task is to import the files specified, only keep the first row for each value in the column specified in the "ID" column, in this case, "POLICY_NUMBER", then merge all the data based on their policy number, keep all unique columns that's not used for comparison from all files (drop duplicate columns with the same names); for the comparison columns, add prefix using the file name (without extension)

Now from the tab specified in "sheet_segment" in the config file, get the list of columns to aggregate the comparison columns by, then compute the percentage difference, which is derived by "Target Column / Benchmark Column - 1", column name should be "diff_" + column name.

Then in the tab specified in "sheet_band", map the difference computed above to the band name, then plot a bar chart using highchart, output a html file in the output dir in the config file

Also output the merged date file to the output folder

---

Modularise the approach for the impact analysis and data conversion

Use polars instead of pandas

I changed how i use the segment field. In the bar chart, y axis should be the proportion of policy, x axis should be bands, the segment field is used as filters, for each field in the segment list, create separate tabs for each unique value, then filter the data using the segment field's values, plot one bar chart for each tab

---

Arrange my files for the converter function, adopt a modularised approach

---

Refactor the visualizer module to use the Jinja2 package, save the template in a separate file, and make this visualizer flexible by importing the components created by analyzer and chart_generator

---

In chart generator, the bar chart should be vertical bars (maybe this is another chart type i can't remember), x axis labels should be the band names, y-axis should be the proportion, and put the x axis labels in the original order as specified in the mapping file, do not sort

---

Now i have added a second column in file1 and file2 for comparison, and added a new row in the impact_analysis_mapping file indicating that this column also needs comparison. I've also added a column 'Item' to indicate what this comparison is named. you need to treat all columns specified in the mapping_column tab in the mapping file as target and benchmark column, fix the data processing code for the merging, and need to calculate percentage difference for each comparison item, and there needs to have multiple column charts, each for the distribution for each comparison item, create tabs (arranged in a horizontal bar) for users to click through the charts, same apply to the summary tables, take the value from 'Item' as the tab names

---

In the band_distribution tab, the band column needs to have the union of all bands for all comparison item, and it should have a pair of the 'count' and 'percentage' columns for each pair of comparison, put the comparison name as prefix to distinguish the columns

---

In data_processor.py: the overall logic should be:
- Get all benchmark and target columns from all files, and rename them first
- Get all column names from all files and get the union set
- Merge all files and keep unique columns in the union set, when there are common columns, keep the columns from the first file only
- Calculate differences for each comparison item specified in the mapping file
- Clean up the code using the logic above

---

I've updated my impact_analysis_config_new.xlsx again, added new steps, and new input data file, in data_processor.py, make the following changes:

1. There is no target or benchmark concept, merge all columns to be compared on to the first file (first row), use the {Column}_{Item}_{Step} naming format, do not merge columns not specified in the mapping file to the first file
2. Then do a comparison for each step in each Item (step 2 vs step 1, step 3 vs step 2), use "diff_{Item}_step_{Step}" naming format (use the higher step number in the comparison)
3. Apply the banding to each comparison, then output to merge_data.csv
4. Summarise the count and percentage in each band for each Item and output to band_distribution.csv
5. In the html report, create nested tabs, first level is Item, second level is StepName (in the mapping file), and plot a distribution column chart in each tab
6. In the summary stats section at the top of the report, show a table of total value of the columns by each Item (in rows) and by each StepName (in columns)
7. After the summary, before the column chart, create another tab section, one tab for each Item, plot a waterfall chart, first bar is the starting point (total value), middle bars are total difference in values in those steps, last bar is the last Step (total value), value label should be expressed as percentage change relative to the first bar, tooltip should show the total value in that step, x axis label should use StepName

---

i realised that i need to distinguish "stage" and "step" in my code:
- stage indicates a single point with value at that stage, stage 1 represents the starting point
- step indicates the difference / impact going from one stage to the next, step 1 is going from stage 1 to stage 2, step 0 is the overall impact between the last and the first stage

refactor my code to distinguish the 2 and assign the correct dict name and column names to the variables and outputs

---

change visualizer.generate_html_report to output the html content and create a separate function to save the report

---

i want to create multiple functions:
1. a function to convert the chart_data (list of dict) into ColumnSeries object that's ready to be added to a Chart object - this function can apply to both chart_data and renewal_chart_data, input should be chart_data and band_order
2. a function to create the canva (foundation) of a bar chart, keep the function name as create_bar_chart, it takes title, chart_id, band_order as input and output a Chart object will as many as options set
3. a function to add series to the Chart object, this function takes a Chart object and ChartSeries object as input and output another Chart object
4. finally in the overarhing generate_all_charts_html function, assemble these components and convert to html


### New feature - Renewal
now i want to add a new feature for renewals:
- in the config file, i've added a new dict called renewal, once this is set to 'true', you will add a new set of columns to the distribution charts, which becomes a grouped column chart - one series for existing values (New Business), one series for new values (Renewal)
- this new series of values is obtained by comparing the differences between the renewal columns defined in the newly created 'RNColumn' column in tab 'mapping_column' in the xlsx config file
- you might need to add new functions to the data_processor code to enable:
  1. refactor functions in config_loader.py to adopt the new renewal flag and config xlsx file
  2. rename renewal columns with standard naming convention by adding '_rn' as suffix
  3. change the existing load_and_merge_data to only keep certain non-premium columns in the merged file, these columns are defined in tab 'segment_columns' in the xlsx file, you need to list out all column names from all data files and pick the first occurence of these columns
  4. merge renewal columns & diff columns into the merged_data
  5. add renewal related items to comparison_mapping
  6. add renewal related items to dict_distribution_summary
  7. refactor create_bar_chart to take a flag of renewal as input, if the flag is yes, create grouped column chart
  8. enable this renewal flag in places you think it's required, refactor the rest of the code as you see suitable
  9. this renewal feature should not impact waterfall charts

---

the 'keep only segment columns' in load and merge applies regardless of whether renewal is enabled or not

---

### New feature - breakdown
i want to allow people to see more breakdown, by a maximum of 3 dimensions. i've added a 'breakdown' component in the yaml config, you need to create a new aggregate_merged_data function called aggregate_impact_breakdown in data_analyser, it should work pretty similar to the existing aggregate_merged_data function but it takes the list of columns to break down as an addition parameter and the output should be a pd.df instead of dict. The function should:
1. validate the length of the list passed in - if longer than 3, cut to 3 and print a warning
2. the output should have the following columns
  - the breakdown columns including unique values in those columns, each row should also include unique combination of the values from all breakdown columns, rows ordered by the breakdown column values
  - value_total_start (total value in the first stage in that segment)
  - value_total_end (total value in the last stage in that segment)
  - policy count (count of rows in that segment)
  - value_diff (between last and first stage only)
  - value_diff_percent (between last and first stage only)

in visualizer, create a function to convert this df from the above function to html format to display in the html report, overall it should look like an Excel pivot table with subtotal rows and grand total row at the bottom

in html template, create a section called "Segment and Policy Level Rate Change" to present this table

## Dashboard App

Create a dash dashboard in Python which serves as a front end for 2 functions:

### Page 1 - Allow users to import data and perform the data conversion

In this page, there is a zone that allows users to drag in their import data. Give a preview of the data for the first few lines.

Secondly, the page should allow users to drag in a mapping file and give a preview of the output format.

Thirdly, there is a zone for users to preview the current config, which connects to config_data_conversion.yaml. Users can edit and update through front end.

Then it should have a button for users to start converting.

There should also be a log screen to show users what is happening and any error messages

### Page 2 - Show the impact summary and chart

Similarly, there is a zone for users to preview the current config, which connects to config_impact_analysis.yaml. Users can edit and update through front end.

This app should utilise as much existing modules / code as possible through import

---

I got 18 errors with the following message:

> Attempting to connect a callback Input item to component: "run-impact-analysis" but no components with that id exist in the layout. If you are assigning callbacks to components that are generated by other callbacks (and therefore not in the initial layout), you can suppress this exception by setting `suppress_callback_exceptions=True`. This ID was used in the callback(s) for Output(s): impact-analysis-status.children

Can you fix this? And you can use my browser to test any errors after fixing

---

In impact_analysis backend, use the python package of highchart instead of js strings, and put the charts functions into a separate module so that it'll be useful in dash callback, as well as in static report generation

---

Create a dash dashboard in Python for this impact analysis, it should has the following sections and functions:

- there is a zone for users to preview the current config, which connects to config_impact_analysis.yaml. Users can edit and update through front end through a 'Update Configuration' button
- next to this button, there is a 'Run Impact Analysis' button, which starts loading data, calculate summary and show the report, but do not output csv data or html report
- below this is a 'Filters' section which reads the 'filter' parameter from the config yaml file, which is a list that lists out all columns to filter, each filter contains the unique values in that column in a drop down, multiple options list, which enable users to filter values in these columns. next to the 'Run Impact Analysis' button above, there should be a button 'Refresh results' so that after user select new filtered values, the results will be updated
- below this is 'Analysis Results' section, i want similar thing created in the dashboard app as in the impact analysis html report: total value summary, waterfall chart, distribution chart by steps. The app should utilise as much existing class and functions as possible instead of creating it's own to produce the same result
- the app should store the merged data in memory so that it can recalculate the results without re-loading the data when user apply different filters
- next to the 'Refresh results' button above, there should be a button 'Save as HTML report' which outputs the html report, do not overwrite existing html files, use timestamp to differenciate the files for now
- there should also be a 'Save Data' button to output data csv files, this button should overwrite existing csv files if exist
- in case you need to create new code/modules in the src folder, you should name any new files with prefix 'app_'

---

in this dash app, in the create_charts_section function, i can see you are using iframe, is it possible to take the content from visualizer.generate_html_report?

## To Do

- Refine the output summary data - needs to be useful for readers, and for charts
- Improve efficiency by merging the band instead of loop
- Efficient read in data

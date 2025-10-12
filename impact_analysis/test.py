import pandas as pd
import numpy as np

# Create sample data
ages = [5, 15, 25, 35, 45, 55, 65, 75, 85]
scores = [45, 67, 89, 72, 55, 91, 38, 82, 76]


# Example 2: Custom bin edges
print("2. Custom bin edges:")
custom_bins = [5, 18, 35, 60, float('inf')]
age_categories = pd.cut(ages, bins=custom_bins)
print(f"Bins: {custom_bins}")
print(f"Result: {age_categories.tolist()}\n")

# Example 3: Custom labels
print("3. With custom labels:")
labels = ['Child', 'Young Adult', 'Middle Age', 'Senior']
age_groups = pd.cut(ages, bins=custom_bins, labels=labels)
print(f"Result: {age_groups.tolist()}\n")

# Example 4: Include lowest value
print("4. Include lowest boundary (right=False):")
age_left = pd.cut(ages, bins=custom_bins, labels=labels, right=False)
print(f"Result: {age_left.tolist()}\n")

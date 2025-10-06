import pandas as pd

df = pd.DataFrame({
    'A': [1, 2, 3],
    'B': [4, 5, 6],
    'C': [7, 8, 9]
})

selected_columns = ['A', 'C']
summed_df = pd.DataFrame([df[selected_columns].sum()])
print(summed_df)

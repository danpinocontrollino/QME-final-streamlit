import pandas as pd

# Load both datasets
df_the = pd.read_csv('/Users/danpino/Desktop/Data Science/First year second semester/QME/final_project_QME/actual_implementation/THE_Rankings_2026_only.csv')
df_gdp = pd.read_csv('/Users/danpino/Desktop/Data Science/First year second semester/QME/final_project_QME/cleaned_world_gdp_data.csv')

# Get a list of the unique, actual countries from the University dataset
real_countries = df_the['Country'].unique()

# Filter the GDP dataset to ONLY keep rows where the Country name is in our real_countries list
df_gdp_clean = df_gdp[df_gdp['Country'].isin(real_countries)]

# Now perform the merge!
df_final = pd.merge(df_the, df_gdp_clean, on='Country', how='left')
# Save the final merged dataset
df_final.to_csv('/Users/danpino/Desktop/Data Science/First year second semester/QME/final_project_QME/actual_implementation/final_merged_dataset.csv', index=False)
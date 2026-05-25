import pandas as pd

# 1. Load the raw World Bank dataset, skipping the first 4 metadata rows
df_raw_gdp = pd.read_csv('/Users/danpino/Desktop/Data Science/First year second semester/QME/final_project_QME/actual_implementation/gdp_per_capita.csv', skiprows=4)

# 2. "Melt" the dataframe: Collapse all the year columns into two columns ('Year' and 'GDP_per_Capita')
df_melted = df_raw_gdp.melt(
    id_vars=['Country Name', 'Country Code'], 
    value_vars=[col for col in df_raw_gdp.columns if col.isnumeric()],
    var_name='Year', 
    value_name='GDP_per_Capita'
)

# 3. Clean the data: Drop missing values
df_melted = df_melted.dropna(subset=['GDP_per_Capita'])

# 4. Sort by Year descending, then drop duplicates to keep ONLY the most recent year per country
df_melted = df_melted.sort_values(by=['Country Name', 'Year'], ascending=[True, False])
df_latest_gdp = df_melted.drop_duplicates(subset=['Country Name'], keep='first')

# 5. Keep only the columns we need and rename 'Country Name' to 'Country' for the merge
df_clean_gdp = df_latest_gdp[['Country Name', 'GDP_per_Capita']].rename(columns={'Country Name': 'Country'})

# Save the clean dataset
df_clean_gdp.to_csv('cleaned_world_gdp_data.csv', index=False)
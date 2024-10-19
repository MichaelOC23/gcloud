import pandas as pd
import streamlit as st

# Sample DataFrame for examples
df = pd.DataFrame({
    'Name': ['Alice', 'Bob', 'Charlie', 'David', 'Eve'],
    'Age': [25, 32, 22, 45, 28],
    'Salary': [50000, 55000, 60000, 52000, 58000],
    'Department': ['HR', 'Engineering', 'HR', 'Engineering', 'HR']
})

# Streamlit code to display before and after
st.title("Pandas DataFrame Cheat Sheet")

# Helper function to show side by side dataframes
def show_before_after(before_df, after_df, before_title="Before", after_title="After"):
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"##### {before_title}")
        st.dataframe(before_df)
    with col2:
        st.markdown(f"##### {after_title}")
        st.dataframe(after_df)
    st.divider()

st.markdown("#### :blue[1. Sort by column]")
with st.echo():    
    sorted_df = df.sort_values(by='Age')
    show_before_after(df, sorted_df, "Original", "Sorted by Age")

st.markdown("#### :blue[2. Grouping with totals (e.g., summing Salary by Department)]")
with st.echo():    
    grouped_total = df.groupby('Department')['Salary'].sum().reset_index()
    show_before_after(df, grouped_total, "Original", "Total Salary by Department")

st.markdown("#### :blue[3. Grouping with custom math (e.g., mean of Salary by Department)]")
with st.echo():    
    grouped_mean = df.groupby('Department')['Salary'].mean().reset_index()
    show_before_after(df, grouped_mean, "Original", "Mean Salary by Department")

st.markdown("#### :blue[4. Max of a text column (e.g., last alphabetically by Name)]")
with st.echo():    
    max_name = pd.DataFrame({'Max Name': [df['Name'].max()]})
    show_before_after(df, max_name, "Original", "Max Name")

st.markdown("#### :blue[5. Row count (number of rows in the DataFrame)]")
with st.echo():    
    row_count = pd.DataFrame({'Row Count': [df.shape[0]]})
    show_before_after(df, row_count, "Original", "Row Count")

st.markdown("#### :blue[6. Add a new column (e.g., Bonus = 10% of Salary)]")
with st.echo():    
    df_with_bonus = df.copy()
    df_with_bonus['Bonus'] = df_with_bonus['Salary'] * 0.1
    show_before_after(df, df_with_bonus, "Original", "Added Bonus Column")

st.markdown("#### :blue[7. Change values based on criteria (e.g., increase Salary for HR by 5%)]")
with st.echo():    
    df_salary_increase = df.copy()
    df_salary_increase.loc[df_salary_increase['Department'] == 'HR', 'Salary'] *= 1.05
    show_before_after(df, df_salary_increase, "Original", "Salary Increase for HR")

st.markdown("#### :blue[8. Top 10 rows based on sorted values (e.g., highest Salary)]")

with  st.echo():
    top_salary_df = df.nlargest(3, 'Salary')  #st.markdown("#### :blue[Adjust to 10 for larger DataFrame]")
    show_before_after(df, top_salary_df, "Original", "Top 3 by Salary")

st.markdown("#### :blue[9. Drop a column (e.g., drop Department)]")
with st.echo():    
    df_drop_column = df.drop(columns=['Department'])
    show_before_after(df, df_drop_column, "Original", "Dropped Department Column")

st.markdown("#### :blue[10. Filter rows based on condition (e.g., Age > 30)]")
with st.echo():    
    filtered_age_df = df[df['Age'] > 30]
    show_before_after(df, filtered_age_df, "Original", "Age > 30")

st.markdown("#### :blue[11. Rename columns]")
with st.echo():    
    renamed_df = df.rename(columns={'Name': 'Employee Name', 'Age': 'Employee Age'})
    show_before_after(df, renamed_df, "Original", "Renamed Columns")

st.markdown("#### :blue[12. Get distinct values in a column (e.g., Department)]")
with st.echo():    
    distinct_values = pd.DataFrame(df['Department'].unique(), columns=['Distinct Department'])
    show_before_after(df, distinct_values, "Original", "Distinct Department Values")

st.markdown("#### :blue[13. Pivot table (e.g., Salary by Department)]")
with st.echo():    
    pivot_table = pd.pivot_table(df, values='Salary', index='Department', aggfunc='sum').reset_index()
    show_before_after(df, pivot_table, "Original", "Pivot Table of Salary by Department")

st.markdown("#### :blue[14. Reset index]")
with st.echo():    
    df_reset_index = df.reset_index(drop=True)
    show_before_after(df, df_reset_index, "Original", "Reset Index")

st.markdown("#### :blue[15. Drop duplicates (e.g., based on Name)]")
with st.echo():    
    df_no_duplicates = df.drop_duplicates(subset=['Name'])
    show_before_after(df, df_no_duplicates, "Original", "Dropped Duplicates by Name")

st.markdown("#### :blue[16. Fill missing values (e.g., fill NaN in Salary with 0)]")
with st.echo():    
    df_with_nan = df.copy()
    df_with_nan.loc[2, 'Salary'] = None
    df_filled = df_with_nan.fillna({'Salary': 0})
    show_before_after(df_with_nan, df_filled, "Original with NaN", "Filled NaN in Salary")

st.markdown("#### :blue[17. Apply a function to a column (e.g., convert Age to string)]")
with st.echo():    
    df_age_str = df.copy()
    df_age_str['Age'] = df_age_str['Age'].astype(str)
    show_before_after(df, df_age_str, "Original", "Age as String")

st.markdown("#### :blue[18. Get column names]")
with st.echo():    
    column_names = pd.DataFrame({'Column Names': df.columns})
    show_before_after(df, column_names, "Original", "Column Names")

st.markdown("#### :blue[19. Calculate the mean of a column (e.g., Age)]")
with st.echo():    
    age_mean = pd.DataFrame({'Age Mean': [df['Age'].mean()]})
    show_before_after(df, age_mean, "Original", "Mean Age")

st.markdown("#### :blue[20. Filter rows by multiple conditions (e.g., Age > 25 and Salary > 50000)]")
with st.echo():    
    filtered_df = df[(df['Age'] > 25) & (df['Salary'] > 50000)]
    show_before_after(df, filtered_df, "Original", "Filtered Age > 25 and Salary > 50K")

st.markdown("#### :blue[21. Select specific columns]")
with st.echo():    
    selected_columns_df = df[['Name', 'Salary']]
    show_before_after(df, selected_columns_df, "Original", "Selected Name and Salary")

st.markdown("#### :blue[22. Convert column to datetime (e.g., converting an existing date column)]")
with st.echo():    
    df_with_date = df.copy()
    df_with_date['Date'] = pd.to_datetime(['2023-01-01', '2023-01-02', '2023-01-03', '2023-01-04', '2023-01-05'])
    show_before_after(df, df_with_date, "Original", "Added Date Column")

st.markdown("#### :blue[23. Convert DataFrame to dictionary]")
with st.echo():    
    df_dict = df.to_dict()
    st.write("DataFrame as Dictionary", df_dict)

# st.markdown("#### :blue[24. Append rows to DataFrame]")
# with st.echo():    
#     df_new_row = df.append({'Name': 'Frank', 'Age': 30, 'Salary': 61000, 'Department': 'HR'}, ignore_index=True)
#     show_before_after(df, df_new_row, "Original", "Appended Row")

st.markdown("#### :blue[25. Merge two DataFrames]")
with st.echo():    
    df_additional = pd.DataFrame({'Name': ['Alice', 'Bob'], 'Bonus': [5000, 4000]})
    df_merged = pd.merge(df, df_additional, on='Name', how='left')
    show_before_after(df, df_merged, "Original", "Merged with Bonus Data")

st.markdown("#### :blue[26. Calculate column statistics (e.g., sum of Salary)]")
with st.echo():    
    salary_sum = pd.DataFrame({'Salary Sum': [df['Salary'].sum()]})
    show_before_after(df, salary_sum, "Original", "Sum of Salary")

st.markdown("#### :blue[27. Transpose the DataFrame]")
with st.echo():    
    transposed_df = df.T
    st.write("Transposed DataFrame")
    st.dataframe(transposed_df)

st.markdown("#### :blue[28. Get the first or last n rows]")
with st.echo():    
    first_n_rows = df.head(3)
    last_n_rows = df.tail(3)
    show_before_after(df, first_n_rows, "Original", "First 3 Rows")
    show_before_after(df, last_n_rows, "Original", "Last 3 Rows")

st.markdown("#### :blue[29. Set a column as the index]")
with st.echo():    
    df_set_index = df.set_index('Name')
    show_before_after(df, df_set_index, "Original", "Set Name as Index")

st.markdown("#### :blue[30. Remove missing values (e.g., drop rows with missing Salary)]")
with st.echo():    
    df_dropna = df_with_nan.dropna(subset=['Salary'])
    show_before_after(df_with_nan, df_dropna, "Original with NaN", "Dropped Rows with NaN Salary")
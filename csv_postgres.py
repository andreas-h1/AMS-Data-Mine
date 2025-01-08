from dotenv import load_dotenv
import os
import glob
import pandas as pd
import psycopg2
import shutil  # Import shutil to move files

load_dotenv()

# Directory containing your CSV files
csv_dir = '/home/ams/postgres/csv_files/'

# Directory where processed CSV files will be moved
csv_dir_old = '/home/ams/postgres/csv_files_old/'

# Ensure the csv_dir_old exists
if not os.path.exists(csv_dir_old):
    os.makedirs(csv_dir_old)

# Get a list of all CSV files in the directory
csv_files = glob.glob(os.path.join(csv_dir, '*.csv'))

# Connect to the PostgreSQL database
conn = psycopg2.connect(
    host="172.26.0.3",
    database="analytics_team",
    user=os.getenv("POSTGRES_USER"),
    password=os.getenv("POSTGRES_PASSWORD")
)
cur = conn.cursor()

for csv_file in csv_files:
    # Read the CSV file into a DataFrame with low_memory=False
    df = pd.read_csv(csv_file, low_memory=False)

    # Drop columns that are completely empty
    df.dropna(axis=1, how='all', inplace=True)

    # Replace NaN values with None to handle NULLs in PostgreSQL
    df = df.where(pd.notnull(df), None)

    # Get the filename without the extension
    filename = os.path.splitext(os.path.basename(csv_file))[0]

    # Define the table name
    table_name = f'survey_data_{filename}'

    # Drop the table if it already exists
    cur.execute(f'DROP TABLE IF EXISTS "{table_name}";')
    conn.commit()

    # Generate the CREATE TABLE query based on DataFrame's columns and data types
    columns = []
    for col, dtype in zip(df.columns, df.dtypes):
        col_name = col.replace('"', '""')  # Escape double quotes in column names
        if 'int' in str(dtype):
            columns.append(f'"{col_name}" INTEGER')
        elif 'float' in str(dtype):
            columns.append(f'"{col_name}" FLOAT')
        else:
            columns.append(f'"{col_name}" TEXT')

    create_table_query = f'CREATE TABLE "{table_name}" ({", ".join(columns)});'
    print(f"Creating table {table_name}...")

    # Execute the CREATE TABLE query
    cur.execute(create_table_query)
    conn.commit()

    # Insert DataFrame records into the table
    for index, row in df.iterrows():
        placeholders = ', '.join(['%s'] * len(row))
        insert_query = f'INSERT INTO "{table_name}" VALUES ({placeholders});'
        cur.execute(insert_query, tuple(row))

    conn.commit()
    print(f"Data imported into {table_name} successfully!")

    # Move the processed file to the 'csv_files_old' directory
    shutil.move(csv_file, os.path.join(csv_dir_old, os.path.basename(csv_file)))

# Close the cursor and connection
cur.close()
conn.close()

import pandas as pd
import re
import sys

def sanitize_column_name(col):
    # Remove newline characters and leading/trailing whitespace
    col = col.replace('\n', ' ').replace('\r', ' ').strip()
    # Replace spaces and special characters with underscores
    col = re.sub(r'\W+', '_', col)
    # Ensure the column name is not empty
    if not col:
        col = 'column'
    return col

def make_unique(columns):
    counts = {}
    new_columns = []
    for col in columns:
        if col in counts:
            counts[col] += 1
            new_col = f"{col}_{counts[col]+1}"
        else:
            counts[col] = 0
            new_col = col
        new_columns.append(new_col)
    return new_columns

def sanitize_csv_columns(input_csv, output_csv):
    # Read the CSV file into a DataFrame
    df = pd.read_csv(input_csv, low_memory=False)

    # Sanitize column names
    df.columns = [sanitize_column_name(col) for col in df.columns]

    # Make column names unique by appending a number
    df.columns = make_unique(df.columns)

    # Save the sanitized DataFrame to a new CSV file
    df.to_csv(output_csv, index=False)
    print(f"Sanitized CSV saved to {output_csv}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python sanitize_columns.py input_csv output_csv")
    else:
        input_csv = sys.argv[1]
        output_csv = sys.argv[2]
        sanitize_csv_columns(input_csv, output_csv)

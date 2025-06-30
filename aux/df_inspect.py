import pandas as pd
import os
from datetime import datetime
from pathlib import Path

data_dir = Path('../src/factorsums/data/')
latest_file = None
latest_date = None

for file_obj in data_dir.iterdir():
    if file_obj.is_file() and file_obj.name.endswith('.pkl') and 'primes_' in file_obj.name:
        try:
            date_str = file_obj.name.split('primes_')[1].replace('.pkl', '')
            current_date = datetime.strptime(date_str, '%Y%m%d')
            if latest_date is None or current_date > latest_date:
                latest_date = current_date
                latest_file = file_obj
        except (IndexError, ValueError):
            pass

if latest_file:
    df = pd.read_pickle(str(latest_file))
    print('--- DataFrame Info ---')
    df.info()
    print('\n--- First 5 Rows ---')
    print(df.head())
    print('\n--- Example partitions_data entry ---')
    # Find a row with partitions_data that is not empty
    partitions_exist = df[df['num_partitions'] > 0]
    if not partitions_exist.empty:
        example_row = partitions_exist.iloc[0]
        example_partition_data = example_row['partitions_data']
        print(f'Type of partitions_data entry: {type(example_partition_data)}')
        print(f'Content: {example_partition_data}')
        if example_partition_data:
            print(f'Type of first element in partitions_data: {type(example_partition_data[0])}')
            print(f'Content of first element: {example_partition_data[0]}')
            print(f'Type of elements within first tuple (p,j,q,k): {type(example_partition_data[0][0])}, {type(example_partition_data[0][1])}, {type(example_partition_data[0][2])}, {type(example_partition_data[0][3])}')
        else:
            print('partitions_data is empty for the example row.')
    else:
        print('No rows with partitions found in the DataFrame.')
else:
    print('No PKL file found.')

from glob import glob
import os
import sys

import pandas as pd
from tqdm import tqdm

import parse as ps

PATH = '../data'
OUT_PATH = os.path.join(PATH, 'parsed_data')

DATA2FUNC = {
    'ukrinform': ps.extract_from_ukrinform,
    'sputnik': ps.extract_from_sputnik,
    'nv': ps.extract_from_nv,
    'tyzhden': ps.extract_from_tyzhden,
    'hro': ps.extract_from_hro,
}


if __name__ == '__main__':
    'works like this: from the folder "code" python parse_and_save.py <dataset_name>'
    if len(sys.argv) != 2:
        print('Usage: <dataset name>')
        sys.exit(1)

    dataset_name = sys.argv[1]
    if dataset_name not in DATA2FUNC:
        print(f"Dataset {dataset_name} is not supported")
        sys.exit(1)
        
    out_path = os.path.join(OUT_PATH, f'{dataset_name}.csv')
    log_path = os.path.join(OUT_PATH, f'{dataset_name}_log.txt')
    files = glob(os.path.join(PATH, f'swe-{dataset_name}', '*'))

    parse_func = DATA2FUNC[dataset_name]

    parsed_files, logs = [], []

    for file_path in tqdm(files, desc="Processing files", unit="file"):
        if "tag" in file_path.lower():
            print(f'Skipping tag file... {file_path}')
            continue
        try:
            # not relevant but good to keep in mind: 
            # add the id of the article of handle it in some other way bc UKRINFORM has doubling aricles
            # maybe just like write a script which will check which articles are in UKRINFORM
            # and which are in www.ukrinform.ua folders -- the same id of an article means the same content
            parsed = parse_func(file_path)
            if not parsed:
                print('No meta or body found')
                print('Skipping article....')
                logs.append(file_path)
                continue
            parsed_files.append(parsed)
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            logs.append(f"Error processing {file_path}: {e}")

    df = pd.DataFrame(parsed_files)
    df.to_csv(out_path, index=False)

    with open(log_path, 'w', encoding='utf-8') as fp:
        fp.write('\n'.join(logs))






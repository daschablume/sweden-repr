from glob import glob
import os
import sys

import pandas as pd
from tqdm import tqdm

from parse import extract_article_info

if __name__ == '__main__':
    if len(sys.argv) != 4:
        print('Usage: <path> <out_path> <log_path>')
        sys.exit(1)

    path, out_path, log_path = sys.argv[1:4]
    
    files = glob(os.path.join(path, '*'))
    parsed_files, logs = [], []

    for file_path in tqdm(files, desc="Processing files", unit="file"):
        try:
            with open(file_path, encoding='utf-8') as fp:
                html = fp.read()
            parsed = extract_article_info(html)
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






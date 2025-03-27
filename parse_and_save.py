import glob
import os
import sys

import pandas as pd
from tqdm import tqdm

from extractors import (
    SputnikExtractor, UkrinformExtractor, NvExtractor,
    HromadskeExtractor, KyivPostExtractor, TyzhdenExtractor,
    EuractivExtractor, KyivPostArchiveExtractor
)

PATH = '../data'
OUT_PATH = os.path.join(PATH, 'parsed_data')

DATASET_CONFIG = {
    'sputnik': {
        'extractor': SputnikExtractor,
        'path_schema': f"{'[0-9]' * 8}/*.html",
    },
    'ukrinform': {
        'extractor': UkrinformExtractor,
        'path_schema': "**/*.html",
    },
    'nv': {
        'extractor': NvExtractor,
        'path_schema': "**/*.html",
    },
    'hromadske': {
        'extractor': HromadskeExtractor,
        'path_schema': '*.html',
    },
    'kyivpost': {
        'extractor': KyivPostExtractor,
        'path_schema': 'www.kyivpost.com/**/*.html',
    },
    'kyivpost_archive': {
        'extractor': KyivPostArchiveExtractor,
        'path_schema': 'kyivpost/archive_kyivpost/**/*.html',
    },
    'tyzhden': {
        'extractor': TyzhdenExtractor,
        'path_schema': '**/*.HTM',
    },
    'euractiv': {
        'extractor': EuractivExtractor,
        'path_schema': '**/*.html',
    }
}


if __name__ == '__main__':
    'works like this: from the folder "code" python parse_and_save.py <dataset_name>'
    if len(sys.argv) < 2:
        print('Usage: <dataset name>')
        sys.exit(1)

    dataset_name = sys.argv[1]
    if dataset_name not in DATASET_CONFIG:
        print(f"Dataset {dataset_name} is not supported")
        sys.exit(1)

    rerun = False
    if len(sys.argv) == 3:
        if sys.argv[2] == 'rerun':
            rerun = True
        else: 
            print('The second argument is not recognized. '
                'Use "rerun" to rerun the parsing. '
                'Continuing without rerun'
            )

    os.makedirs(OUT_PATH, exist_ok=True)
    if dataset_name == 'kyivpost_archive' or dataset_name == 'kyivpost':
        OUT_PATH = os.path.join(OUT_PATH, 'kyivpost_splitted')
        os.makedirs(OUT_PATH, exist_ok=True)
    
    out_path = os.path.join(OUT_PATH, f'{dataset_name}.csv')
    log_path = os.path.join(OUT_PATH, f'{dataset_name}_log.txt')

    extractor = DATASET_CONFIG[dataset_name]['extractor']()
    path_schema = DATASET_CONFIG[dataset_name]['path_schema']

    filepaths = os.path.join(PATH, dataset_name, path_schema)
    files = glob.iglob(filepaths, recursive=True)  # generator cause there might be 10k files

    parsed_files, logs = [], []

    # don't load again the files which were already processed
    processed_files = set()
    existing_df = None
    # if rerun, process all files from the top
    if not rerun:
        existing_df = pd.read_csv(out_path) if os.path.exists(out_path) else None
        if existing_df is not None:
            processed_files = set(existing_df['file_path'])
    
    already_processed = set()  # relevant for "euractiv" only
    for file_path in tqdm(files, desc="Processing files\n", unit="file"):
        if 'index-pages' in file_path:
            continue
        article_folder = file_path.split('/')[-2]
        if dataset_name == 'euractiv':
            if article_folder in already_processed:
                continue
            already_processed.add(article_folder)
        print(f'Processing file: {file_path}')
        normalized_path = file_path.replace('../data/', '')
        if normalized_path in processed_files:
            print(f'File already processed: {normalized_path}')
            continue
        try:
            parsed = extractor.extract(file_path)
            if not parsed:
                message = f'No valid article data found in {file_path}'
                print(message)
                logs.append(message)
                continue
            parsed_files.append(parsed)
        except Exception as e:
            message = f"Error processing {file_path}: {e}"
            print(message)
            logs.append(message)

    if parsed_files:
        df = pd.DataFrame(parsed_files)
    else:
        print('No data to save')
        sys.exit(1)
    
    if existing_df is None:
        df.to_csv(out_path, index=False)
    else:
        df.to_csv(out_path, index=False, mode='a', header=False)

    with open(log_path, 'w', encoding='utf-8') as fp:
        fp.write('\n'.join(logs))
import os
import shutil
import sys

PATH = '../data'


def move_files(txt, destination_dir):
    '''
    This script is problematic for cases when the file name is like "SOME_NAME/INDEX.HTM",
    because then there are several files which end with "INDEX" and they will be overwritten,
    ending up with only one file in the destination directory instead of several.
    Don't use / use cautiously.
    (This is because of `shutil.copy` line)
    '''
    with open(txt, "r") as f:
        for line in f:
            # ignore .htmls with "tag" for Ukrinform dataset
            if 'tag' in line.lower():
                print(f"Skipping {line}")
                continue
            file_path = os.path.join(PATH, line.strip())            
            if os.path.exists(file_path) and file_path.lower().endswith((".html", ".htm")):
                shutil.copy(file_path, destination_dir)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        raise ValueError('Please provide arguments in the order: txt_file to_dir')

    txt, to_dir = sys.argv[1], sys.argv[2]

    if not txt.endswith('.txt'):
        raise ValueError('The first argument should be a txt file!')

    txt = os.path.join(PATH, txt)
    to_dir = os.path.join(PATH, to_dir)

    os.makedirs(to_dir, exist_ok=True)
    move_files(txt, to_dir)

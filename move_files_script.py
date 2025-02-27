import os
import shutil
import sys

PATH = '../data'

def move_files(txt, destination_dir):
    with open(txt, "r") as f:
        for line in f:
            # ignore .htmls with "tag" for Ukrinform dataset
            if 'tag' in line.lower():
                continue
            file_path = os.path.join(PATH, line.strip())
            if os.path.exists(file_path) and (file_path.endswith(".html") or file_path.endswith(".HTM")):
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

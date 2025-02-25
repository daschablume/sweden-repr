import os
import shutil
import sys


def move_files(txt, destination_dir):
    with open(txt, "r") as f:
        for line in f:
            file_path = line.strip()
            if os.path.exists(file_path) and file_path.endswith(".html"):
                shutil.copy(file_path, destination_dir)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        raise ValueError('Please provide arguments in the order: txt_file to_dir')

    txt, to_dir = sys.argv[1], sys.argv[2]

    if not txt.endswith('.txt'):
        raise ValueError('The first argument should be a txt file!')

    os.makedirs(to_dir, exist_ok=True)
    move_files(txt, to_dir)

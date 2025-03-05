import os
import hashlib
import argparse

# A simple utility to find and print out paths for duplicate files

def parse_args():
    parser = argparse.ArgumentParser(description="Find duplicate files by size and checksum.")
    parser.add_argument("path", nargs="?", default=".", help="Root directory to scan (default: .)")
    parser.add_argument("--min-size", type=int, default=10000, help="Minimum file size in bytes to consider (default: 10000)")
    parser.add_argument("--exclude-file", type=str, help="File containing list of paths to exclude")
    return parser.parse_args()

def ignore_file(path):
    if '.app/' in path or '/.' in path:
        return True # Ignore apps, app resources, and hidden files for now
    if os.path.islink(path):
        return True # Ignore symlinks for now
    return False

def insert_duplicate(key, value, uniques, dups):
    """
    Inserts values in a set of dictionaries that keep unique values and duplicate values separate.
    NOTE: this is for finding duplicates only--unique values are not removed from uniques when
    they get shifted to the duplicates map.
    :param key:
    :param value:
    :param uniques:
    :param dups:
    :return:
    """
    if key in dups:
        dups[key].append(value)
    elif key in uniques:
        # promote to duplicate map
        dups[key] = uniques[key]
        dups[key].append(value)
    else:
        uniques[key] = [value]

def find_size_duplicates(path, min_size):
    unique_map = {}
    dup_map = {}
    for root, dirs, files in os.walk(path):
        for name in files:
            fpath = os.path.join(root, name)
            if ignore_file(fpath):
                continue

            file_size = os.path.getsize(fpath)

            # if file size is below a certain threshold, don't bother with it
            if file_size < min_size:
                continue # Ignore empty files

            insert_duplicate(file_size, fpath, unique_map, dup_map)

    return dup_map

def get_file_checksum(file_path, algorithm="sha256"):
    hash_func = hashlib.new(algorithm)
    with open(file_path, "rb") as f:
        while chunk := f.read(4096):
            hash_func.update(chunk)
    return hash_func.hexdigest()

def get_checksum_dups(dup_map):
    """
    :param dup_map: a dictionary of lists containing potential duplicate files
    :return:
    """

    chksum_uniques = {}
    chksum_dups = {}

    for key, paths in dup_map.items():
        for path in paths:
            checksum = get_file_checksum(path)
            insert_duplicate(checksum, path, chksum_uniques, chksum_dups)

    return chksum_dups

def print_dups(dup_map):
    for key, paths in dup_map.items():
        print(key)
        print("-" * len(str(key)))
        print('\n'.join(paths), end='\n\n')

if __name__ == '__main__':
    args = parse_args()
    abspath = os.path.abspath(os.path.expanduser(args.path))


    size_dups = find_size_duplicates(abspath, args.min_size)
    chksum_dups = get_checksum_dups(size_dups)

    print_dups(chksum_dups)

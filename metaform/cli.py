from argparse import ArgumentParser
from pathlib import Path


def find_and_generate_metaf_files(root_dir: str = "."):
    for files in Path(root_dir).rglob("*.tf.py"):
        print(f"In file {files}")
        with open(files, "r") as f:
            exec(f.read())


def main():
    parser = ArgumentParser()
    parser.add_argument("--chdir", type=str, default=".")
    parser.add_argument("--version", "-v", action="store_true")
    args = parser.parse_args()
    if args.version:
        print("metaform 0.1.0")
    else:
        find_and_generate_metaf_files(args.chdir)

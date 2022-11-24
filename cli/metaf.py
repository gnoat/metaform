from argparse import ArgumentParser
from pathlib import Path


def find_metaf_files(root_dir: str = "."):
    for files in Path(root_dir).rglob("*.tf.py"):
        pass


def main():
    parser = ArgumentParser()
    parser.add_argument("--chdir", type=str, default=".")
    args = parser.parse_args()

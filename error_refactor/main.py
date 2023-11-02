from sys import argv, exit
from pathlib import Path
from typing import List

from error_refactor.source_folder import SourceFolder


def run(_argv: List[str]) -> int:
    if len(_argv) < 2:
        print("Bad command line, pass in the source directory to process...")
        return 1
    root_path = Path(_argv[1])
    sf = SourceFolder(root_path)
    return len(sf.matched_files)  # TODO: Actually do stuff...


if __name__ == '__main__':
    exit(run(argv))

from argparse import ArgumentParser
from sys import argv, exit
from pathlib import Path
from typing import List

from error_refactor.source_folder import SourceFolder


def run_with_args(source_path: Path, output_path: Path) -> int:  # pragma: no cover
    file_names_to_ignore = ['UtilityRoutines.cc']
    sf = SourceFolder(source_path, file_names_to_ignore)
    sf.analyze()
    sf.generate_outputs(output_path)
    return 0


def run_cli(_argv: List[str]) -> int:
    parser = ArgumentParser(
        prog='ErrorRefactorHelper',
        description='Provides parsing, analysis, and refactoring services for error call work',
        epilog='This may be expanded to provide additional services')
    parser.add_argument(
        'source_directory',
        action='store',
        help='Source directory to analyze, usually {repo_root}/src/EnergyPlus'
    )
    parser.add_argument(
        'output_directory',
        action='store',
        help='Target directory for output files/results'
    )
    args = parser.parse_args(args=_argv[1:])
    source_path = Path(args.source_directory)
    output_path = Path(args.output_directory)
    return run_with_args(source_path, output_path)


if __name__ == '__main__':
    exit(run_cli(argv))

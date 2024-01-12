from argparse import ArgumentParser
from sys import argv, exit
from pathlib import Path
from typing import List

from energyplus_refactor_helper.configs import all_configs


def run_cli(_argv: List[str]) -> int:
    parser = ArgumentParser(
        prog='ErrorRefactorHelper',
        description='Provides parsing, analysis, and refactoring services for error call work',
        epilog='This may be expanded to provide additional services')
    valid_config_keys = all_configs.keys()
    parser.add_argument(
        'config_to_run',
        action='store',
        type=str,
        choices=valid_config_keys,
        help='Configuration/Action to run, see the list of valid options'
    )
    parser.add_argument(
        'source_repository',
        action='store',
        help='Source repository to analyze, the root of the repo itself'
    )
    parser.add_argument(
        'output_directory',
        action='store',
        help='Target directory for output logs and results'
    )
    parser.add_argument(
        '--in-place', '-i',
        action='store_true',
        default=False,
        help='Make changes in place in the source directory'
    )
    args = parser.parse_args(args=_argv[1:])
    source_repo = Path(args.source_repository)
    output_path = Path(args.output_directory)
    config_class = all_configs[args.config_to_run]
    config_instance = config_class()
    return config_instance.run_with_args(source_repo, output_path, args.in_place)


if __name__ == '__main__':
    exit(run_cli(argv))

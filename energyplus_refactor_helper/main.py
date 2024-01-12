from argparse import ArgumentParser
from sys import argv, exit
from pathlib import Path

from energyplus_refactor_helper.action import all_actions


def run_cli(_argv: list[str]) -> int:
    parser = ArgumentParser(
        prog='ErrorRefactorHelper',
        description='Provides parsing, analysis, and refactoring services for error call work',
        epilog='This may be expanded to provide additional services')
    valid_action_keys = all_actions.keys()
    parser.add_argument(
        'action_to_run',
        action='store',
        type=str,
        choices=valid_action_keys,
        help='Action to run, see the list of valid options'
    )
    parser.add_argument(
        'source_repository',
        action='store',
        help='Source repository to operate upon: the root of the repo itself'
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
        help='If True, make changes in place in the source directory'
    )
    args = parser.parse_args(args=_argv[1:])
    source_repo = Path(args.source_repository)
    output_path = Path(args.output_directory)
    action_class = all_actions[args.action_to_run]
    action_instance = action_class()
    return action_instance.run(source_repo, output_path, args.in_place)


if __name__ == '__main__':
    exit(run_cli(argv))

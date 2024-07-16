import argparse
from argparse import ArgumentParser
from sys import argv, exit
from pathlib import Path

from energyplus_refactor_helper.action import all_actions


def run(args: list[str]) -> int:
    """
    This is the primary entry point for running the error refactor package as a library, where arguments are
    passed in to this function from your Python code.  In this calling approach, you pass in the arguments exactly as
    they are passed to the command line.  You don't need to pass a dummy 0 argument, just pass in command args.

    :param args: A list of command line arguments/switches to run this operation.
    :return: Exit code, 0 if no errors were encountered, or 1 if there were errors
    """
    parser = ArgumentParser(
        prog='ErrorRefactorHelper',
        description='Provides parsing, analysis, and refactoring services for EnergyPlus code',
        epilog='This may be expanded to provide additional services',
        formatter_class=lambda prog: argparse.HelpFormatter(prog, width=150)
    )
    valid_action_keys = all_actions.keys()
    parser.add_argument(
        'action_to_run',
        action='store',
        type=str,
        choices=valid_action_keys,
        help='Action to run, this is the list of valid options'
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
    parser.add_argument(
        '--skip-plots', '-s',
        action='store_true',
        default=False,
        help='If True, skip making the plot, which can take a long time'
    )
    args = parser.parse_args(args=args)
    source_repo = Path(args.source_repository)
    output_path = Path(args.output_directory)
    action_class = all_actions[args.action_to_run]
    action_instance = action_class()
    return action_instance.run(source_repo, output_path, args.in_place, args.skip_plots)


def run_cli() -> int:  # pragma: no cover
    """
    This is the primary command line entry point for this package.  This function requires no function arguments because
    the arguments are retrieved from sys.argv.  Command line arguments options are available by running with "-h"

    :return: Exit code, 0 if no errors were encountered, or 1 if there were errors
    """
    return run(argv[1:])


def show_usage() -> None:
    """
    Just a simple worker function to exercise the -h command line flag and emit usage content to stdout.

    :return: None, because ArgParse calls SystemExit if given a -h
    """
    run(['-h'])


if __name__ == '__main__':  # pragma: no cover
    # show_usage()
    exit(run_cli())

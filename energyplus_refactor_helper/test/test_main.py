from contextlib import redirect_stdout
from os import devnull
from pathlib import Path
from tempfile import mkdtemp

from pytest import raises

from energyplus_refactor_helper.main import run, show_usage


def test_overall_flow():
    this_file = Path(__file__).resolve()
    fake_source_folder = str(this_file.parent / 'fake_source_folder')
    dummy_output_dir = mkdtemp()
    run(['error_call_refactor', fake_source_folder, dummy_output_dir])


def test_usage():
    with raises(SystemExit):
        with open(devnull, 'w') as f:
            with redirect_stdout(f):
                show_usage()

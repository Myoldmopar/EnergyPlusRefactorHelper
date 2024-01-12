from pathlib import Path
from tempfile import mkdtemp

from energyplus_refactor_helper.main import run_cli


class TestMainRun:

    def test_overall_flow(self):
        this_file = Path(__file__).resolve()
        fake_source_folder = str(this_file.parent / 'fake_source_folder')
        dummy_output_dir = mkdtemp()
        run_cli(['', 'error_call_refactor', fake_source_folder, dummy_output_dir])

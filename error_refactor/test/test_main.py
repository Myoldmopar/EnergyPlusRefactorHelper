from pathlib import Path
from tempfile import mkdtemp

from error_refactor.main import run_with_args


class TestMainRun:

    def test_overall_flow(self):
        this_file = Path(__file__).resolve()
        fake_source_folder = this_file.parent / 'fake_source_folder'
        dummy_output_dir = Path(mkdtemp())
        run_with_args(fake_source_folder, dummy_output_dir)

from pathlib import Path
from tempfile import mkdtemp
from unittest import TestCase

from error_refactor.main import run


class TestMainRun(TestCase):

    def setUp(self):
        this_file = Path(__file__).resolve()
        self.fake_source_folder = str(this_file.parent / 'fake_source_folder')
        self.dummy_output_dir = mkdtemp()

    def test_overall_flow(self):
        run([self.fake_source_folder, self.dummy_output_dir])

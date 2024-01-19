from shutil import copytree
import tempfile
from pathlib import Path
from tempfile import mkdtemp

from energyplus_refactor_helper.action import ErrorCallRefactor
from energyplus_refactor_helper.source_folder import SourceFolder

funcs = ErrorCallRefactor().function_calls()  # just create a dummy instance here for convenience


class TestSourceFolder:
    @staticmethod
    def set_up_dirs() -> tuple[Path, Path]:
        this_file = Path(__file__).resolve()
        fake_source_folder = this_file.parent / 'fake_source_folder' / 'src' / 'EnergyPlus'
        dummy_output_folder = Path(mkdtemp())
        return fake_source_folder, dummy_output_folder

    def test_it_finds_matching_files_recursively(self):
        fake_source_folder, dummy_output_folder = TestSourceFolder.set_up_dirs()
        sf = SourceFolder(fake_source_folder, dummy_output_folder, [], funcs, False)
        assert len(sf.matched_files) == 4

    def test_it_finds_matching_files_including_ignored(self):
        fake_source_folder, dummy_output_folder = TestSourceFolder.set_up_dirs()
        sf = SourceFolder(
            fake_source_folder, dummy_output_folder, ['file_to_ignore.cc'], funcs, False
        )
        assert len(sf.matched_files) == 3

    def test_full_workflow(self):
        fake_source_folder, dummy_output_folder = TestSourceFolder.set_up_dirs()
        sf = SourceFolder(
            fake_source_folder, dummy_output_folder, ['file_to_ignore.cc'], funcs, False
        )
        assert sf.success
        output_files_found = list(dummy_output_folder.glob('*'))
        assert len(output_files_found) > 0

    def test_it_creates_output_folder_if_not_exists(self):
        fake_source_folder, dummy_output_folder = TestSourceFolder.set_up_dirs()
        nonexistent_dummy_output_folder = dummy_output_folder / 'dummy'
        sf = SourceFolder(
            fake_source_folder, nonexistent_dummy_output_folder, ['file_to_ignore.cc'], funcs, False
        )
        assert sf.success
        output_files_found = list(nonexistent_dummy_output_folder.glob('*'))
        assert len(output_files_found) > 0

    def test_edit_in_place_workflow(self):
        new_scratch_dir = Path(tempfile.mkdtemp()) / 'new_scratch_dir'
        test_source_dir, dummy_output_folder = TestSourceFolder.set_up_dirs()
        copytree(test_source_dir, new_scratch_dir)
        sf = SourceFolder(
            new_scratch_dir, dummy_output_folder, ['file_to_ignore.cc'], funcs, True
        )
        assert sf.success
        output_files_found = list(dummy_output_folder.glob('*'))
        assert len(output_files_found) > 0
        # TODO: Check contents of modified source tree in new_scratch_dir

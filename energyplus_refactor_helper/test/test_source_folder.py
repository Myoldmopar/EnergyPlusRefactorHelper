from shutil import copytree
import tempfile
from pathlib import Path
from tempfile import mkdtemp

from energyplus_refactor_helper.source_folder import SourceFolder

funcs = ['ShowSevereError', 'ShowContinueError', 'ShowFatalError', 'ShowWarningError']


class TestSourceFolder:
    @staticmethod
    def set_up_dirs() -> tuple[Path, Path]:
        this_file = Path(__file__).resolve()
        fake_source_folder = this_file.parent / 'fake_source_folder' / 'src' / 'EnergyPlus'
        dummy_output_folder = Path(mkdtemp())
        return fake_source_folder, dummy_output_folder

    def test_it_finds_matching_files_recursively(self):
        fake_source_folder, dummy_output_folder = TestSourceFolder.set_up_dirs()
        sf = SourceFolder(
            fake_source_folder, funcs
        )
        assert len(sf.find_files()) == 4

    def test_it_finds_matching_files_including_ignored(self):
        fake_source_folder, dummy_output_folder = TestSourceFolder.set_up_dirs()
        sf = SourceFolder(fake_source_folder, funcs)
        assert len(sf.find_files(['file_to_ignore.cc'])) == 3

    def test_full_workflow(self):
        fake_source_folder, dummy_output_folder = TestSourceFolder.set_up_dirs()
        sf = SourceFolder(fake_source_folder, funcs)
        assert sf.success
        matched_source_files = sf.find_files(['file_to_ignore.cc'])
        processed_source_files = sf.analyze_source_files(matched_source_files)
        sf.generate_reports(processed_source_files, dummy_output_folder, skip_plots=True)
        output_files_found = list(dummy_output_folder.glob('*'))
        assert len(output_files_found) > 0

    def test_it_creates_output_folder_if_not_exists(self):
        src_folder, dummy_output_folder = TestSourceFolder.set_up_dirs()
        nonexistent_dummy_output_folder = dummy_output_folder / 'dummy'
        sf = SourceFolder(src_folder, funcs)
        matched_source_files = sf.find_files(['file_to_ignore.cc'])
        processed_source_files = sf.analyze_source_files(matched_source_files)
        sf.generate_reports(processed_source_files, nonexistent_dummy_output_folder, skip_plots=True)
        output_files_found = list(nonexistent_dummy_output_folder.glob('*'))
        assert len(output_files_found) > 0

    @staticmethod
    def function_visitor(f):
        args = ', '.join(f.parse_arguments())
        return f"ShowSevereError({args});"

    def test_edit_in_place_workflow(self):
        new_scratch_dir = Path(tempfile.mkdtemp()) / 'new_scratch_dir'
        test_source_dir, _ = TestSourceFolder.set_up_dirs()
        copytree(test_source_dir, new_scratch_dir)
        sf = SourceFolder(new_scratch_dir, funcs)
        matched_source_files = sf.find_files(['file_to_ignore.cc'])
        processed_source_files = sf.analyze_source_files(matched_source_files)
        sf.rewrite_files_in_place(processed_source_files, self.function_visitor, False)
        assert sf.success
        print(f"trying to process files in {new_scratch_dir}")
        output_files_found = list(new_scratch_dir.glob('*'))
        assert len(output_files_found) > 0
        file_to_check = new_scratch_dir / 'test_file.cc'
        assert file_to_check.exists()
        file_text = file_to_check.read_text()
        assert 'ShowSevereError(state, "Something Bad");' in file_text  # it should have rewritten as a single line

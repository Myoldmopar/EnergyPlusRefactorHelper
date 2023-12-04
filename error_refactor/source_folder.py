from itertools import zip_longest
import matplotlib.pyplot as plt
from pathlib import Path
from sys import stdout
from typing import List

from error_refactor.source_file import SourceFile


class SourceFolder:
    def __init__(self, root_path: Path):
        self.root = root_path
        self.matched_files = self.locate_source_files()
        self.results = []
        for i, source_file in enumerate(sorted(self.matched_files)):
            percent_done = 100 * (i / len(self.matched_files))
            if source_file.name == 'UtilityRoutines.cc':
                continue  # don't process the actual error functions themselves
            self.results.append(SourceFile(source_file))
            filled_length = int(80 * (percent_done / 100.0))
            bar = "*" * filled_length + '-' * (80 - filled_length)
            print(f"\rProgress: |{bar}| {percent_done}% - {source_file.name}")
            stdout.flush()
        print("Finished Processing, about to generate results")

    def locate_source_files(self) -> List[Path]:
        known_patterns = ["*.cc", "*.cpp"]  # "*.hh", could include hh here
        all_files = []
        for pattern in known_patterns:
            files_matching = self.root.glob(f"**/{pattern}")
            all_files.extend(list(files_matching))
        return all_files

    def generate_file_summary_csv(self, output_csv_file: Path) -> None:
        s = "File,Good,Bad\n"
        for result in self.results:
            if result.path.name == 'UtilityRoutines.cc':
                continue  # don't process the actual error functions themselves
            good = sum([1 if fe.appears_successful else 0 for fe in result.found_errors])
            bad = sum([0 if fe.appears_successful else 1 for fe in result.found_errors])
            s += f"{result.path},{good},{bad}\n"
        output_csv_file.write_text(s)

    def generate_line_details_csv(self, output_csv_file: Path) -> None:
        all_lists = [[x.path.name, *x.error_distribution] for x in self.results]
        zipped_lists = zip_longest(*all_lists, fillvalue='')
        csv_string = ''.join([",".join(map(str, row)) + "\n" for row in zipped_lists])
        output_csv_file.write_text(csv_string)

    def generate_line_details_plot(self, output_file_file: Path) -> None:
        file_names = [x.path.name for x in self.results]
        data = [x.error_distribution for x in self.results]
        fig, axes = plt.subplots(len(self.results), 1, layout='constrained')
        fig.set_size_inches(8, int(len(self.results) / 2))
        for i, x in enumerate(data):
            percent_done = 100 * (i / len(data))
            axes[i].plot(x)
            axes[i].set_ylabel(file_names[i], rotation=0, labelpad=150)
            axes[i].set_yticklabels([])
            axes[i].get_xaxis().set_visible(False)
            axes[i].set_ylim([0, 1])
            filled_length = int(80 * (percent_done / 100.0))
            bar = "*" * filled_length + '-' * (80 - filled_length)
            print(f"\rProgress: |{bar}| {percent_done}% - {file_names[i]}")
            stdout.flush()
        print("Results processed, plot being set up now")
        plt.savefig(output_file_file)


if __name__ == "__main__":
    p = Path("/eplus/repos/4eplus/src/EnergyPlus")
    f = SourceFolder(p)
    f.generate_file_summary_csv(Path("/tmp/err_file_summary.csv"))
    f.generate_line_details_csv(Path("/tmp/err_line_details.csv"))
    f.generate_line_details_plot(Path("/tmp/err_error_plot.png"))

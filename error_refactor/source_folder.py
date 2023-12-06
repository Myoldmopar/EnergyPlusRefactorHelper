from itertools import zip_longest
import matplotlib.pyplot as plt
from pathlib import Path
from typing import List

from error_refactor.logger import logger
from error_refactor.source_file import SourceFile


class SourceFolder:
    def __init__(self, root_path: Path, file_names_to_ignore: List[str]):
        self.root = root_path
        self.file_names_to_ignore = file_names_to_ignore
        self.matched_files = self.locate_source_files()
        logger.log(f"SourceFolder object constructed, identified {len(self.matched_files)} files ready to analyze.")
        self.processed_files = []

    def locate_source_files(self) -> List[Path]:
        known_patterns = ["*.cc", "*.cpp"]  # "*.hh", could include hh here
        all_files = []
        for pattern in known_patterns:
            files_matching = self.root.glob(f"**/{pattern}")
            all_files.extend(list(files_matching))
        files_to_keep = []
        for file in all_files:
            if file.name in self.file_names_to_ignore:
                logger.log(f"Encountered ignored file: {file.name}; skipping")
                continue  # don't process the actual error functions themselves
            files_to_keep.append(file)
        return files_to_keep

    def analyze(self):
        for file_num, source_file in enumerate(sorted(self.matched_files)):
            percent_done = round(100 * (file_num / len(self.matched_files)), 3)
            self.processed_files.append(SourceFile(source_file))
            filled_length = int(80 * (percent_done / 100.0))
            bar = "*" * filled_length + '-' * (80 - filled_length)
            print(f"\r   Progress: |{bar}| {percent_done}% - {source_file.name}", end='')
        print()
        logger.log("Finished Processing, ready to generate results")

    def generate_outputs(self, output_dir: Path) -> None:
        self.generate_file_summary_csv(output_dir / 'file_summary.csv')
        self.generate_line_details_csv(output_dir / 'lines_summary.csv')
        self.generate_line_details_plot(output_dir / 'error_plot.png')

    def generate_file_summary_csv(self, output_csv_file: Path) -> None:
        s = "File,Good,Bad\n"
        for result in self.processed_files:
            good = sum([1 if fe.appears_successful else 0 for fe in result.found_errors])
            bad = sum([0 if fe.appears_successful else 1 for fe in result.found_errors])
            s += f"{result.path},{good},{bad}\n"
        output_csv_file.write_text(s)

    def generate_line_details_csv(self, output_csv_file: Path) -> None:
        all_lists = [[x.path.name, *x.error_distribution] for x in self.processed_files]
        zipped_lists = zip_longest(*all_lists, fillvalue='')
        csv_string = ''.join([",".join(map(str, row)) + "\n" for row in zipped_lists])
        output_csv_file.write_text(csv_string)

    def generate_line_details_plot(self, output_file_file: Path) -> None:
        file_names = [x.path.name for x in self.processed_files]
        data = [x.error_distribution for x in self.processed_files]
        fig, axes = plt.subplots(len(self.processed_files), 1, layout='constrained')
        fig.set_size_inches(8, int(len(self.processed_files) / 2))
        for i, x in enumerate(data):
            percent_done = 100 * (i / len(data))
            axes[i].plot(x)
            axes[i].set_ylabel(file_names[i], rotation=0, labelpad=150)
            axes[i].set_yticklabels([])
            axes[i].get_xaxis().set_visible(False)
            axes[i].set_ylim([0, 1])
            filled_length = int(80 * (percent_done / 100.0))
            bar = "*" * filled_length + '-' * (80 - filled_length)
            print(f"\r   Progress: |{bar}| {percent_done}% - {file_names[i]}", end='')
        print()
        print("Results processed, plot being set up now")
        plt.savefig(output_file_file)

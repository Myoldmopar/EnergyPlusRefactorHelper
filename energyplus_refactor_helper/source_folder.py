from itertools import zip_longest
from json import dumps
import matplotlib.pyplot as plt
from pathlib import Path
from typing import List

from energyplus_refactor_helper.logger import logger
from energyplus_refactor_helper.source_file import SourceFile


class SourceFolder:
    def __init__(self, root_path: Path, file_names_to_ignore: List[str], function_call_list: list[str]):
        self.root = root_path
        self.function_call_list = function_call_list
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
            percent_done = round(100 * ((file_num + 1) / len(self.matched_files)), 3)
            self.processed_files.append(SourceFile(source_file, self.function_call_list))
            filled_length = int(80 * (percent_done / 100.0))
            bar = "*" * filled_length + '-' * (80 - filled_length)
            print(f"\r                  Progress : |{bar}| {percent_done}% - {source_file.name}", end='')
        print()
        logger.log("Finished Processing, ready to generate results")

    def generate_outputs(self, output_dir: Path) -> None:
        if not output_dir.exists():
            output_dir.mkdir()
        self.generate_error_json(output_dir / 'errors.json')
        self.generate_file_summary_csv(output_dir / 'file_summary.csv')
        self.generate_line_details_csv(output_dir / 'lines_summary.csv')
        self.generate_line_details_plot(output_dir / 'distribution_plot.png')

    def generate_error_json(self, output_json_file: Path) -> None:
        full_json_content = {}
        for file_num, source_file in enumerate(self.processed_files):
            percent_done = round(100 * ((file_num + 1) / len(self.matched_files)), 3)
            full_json_content[source_file.path.name] = source_file.get_call_info_dict()
            filled_length = int(80 * (percent_done / 100.0))
            bar = "*" * filled_length + '-' * (80 - filled_length)
            print(f"\r                  Progress : |{bar}| {percent_done}% - {source_file.path.name}", end='')
        print()
        output_json_file.write_text(dumps(full_json_content, indent=2))
        logger.log("Finished Building JSON outputs")

    def generate_file_summary_csv(self, output_csv_file: Path) -> None:
        s = "File,Good,Bad\n"
        for result in self.processed_files:
            good = sum([1 if fe.appears_successful else 0 for fe in result.found_functions])
            bad = sum([0 if fe.appears_successful else 1 for fe in result.found_functions])
            s += f"{result.path},{good},{bad}\n"
        output_csv_file.write_text(s)

    def generate_line_details_csv(self, output_csv_file: Path) -> None:
        all_lists = [[x.path.name, *x.function_distribution] for x in self.processed_files]
        zipped_lists = zip_longest(*all_lists, fillvalue='')
        csv_string = ''.join([",".join(map(str, row)) + "\n" for row in zipped_lists])
        output_csv_file.write_text(csv_string)

    def generate_line_details_plot(self, output_file_file: Path) -> None:
        file_names = [x.path.name for x in self.processed_files]
        data = [x.advanced_function_distribution for x in self.processed_files]
        data_not_none = [d for d in data if d is not None]
        num_not_none = len(data_not_none)
        if num_not_none > 1:
            fig, axes = plt.subplots(num_not_none, 1, layout='constrained')
            fig.set_size_inches(8, int(num_not_none / 2))
            plot_num = -1
            for data_num, distribution in enumerate(data):
                percent_done = 100 * ((data_num + 1) / len(data))
                if distribution is None:
                    continue
                plot_num += 1
                axes[plot_num].plot(distribution)
                axes[plot_num].set_ylabel(file_names[data_num], rotation=0, labelpad=150)
                axes[plot_num].set_yticklabels([])
                axes[plot_num].get_xaxis().set_visible(False)
                axes[plot_num].set_ylim([0, 20])
                filled_length = int(80 * (percent_done / 100.0))
                bar = "*" * filled_length + '-' * (80 - filled_length)
                print(f"\r                  Progress : |{bar}| {percent_done}% - {file_names[data_num]}", end='')
            print()
            logger.log("Results processed, plot being set up now (may take some time!)")
        else:
            ax = plt.axes()
            ax.plot(data_not_none[0])
        plt.savefig(output_file_file)

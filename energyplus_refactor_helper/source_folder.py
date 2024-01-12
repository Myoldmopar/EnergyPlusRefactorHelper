from itertools import zip_longest
from json import dumps
import matplotlib.pyplot as plt
from pathlib import Path

from energyplus_refactor_helper.logger import logger
from energyplus_refactor_helper.source_file import SourceFile


class SourceFolder:
    def __init__(
            self, root_path: Path, output_dir: Path, file_names_to_ignore: list[str],
            function_calls: list[str], edit_in_place: bool
    ):
        self.success = True  # assume success
        self.root = root_path
        self.function_call_list = function_calls
        self.file_names_to_ignore = file_names_to_ignore
        self.matched_files = self.locate_source_files()
        logger.log(f"SourceFolder object constructed, identified {len(self.matched_files)} files ready to analyze.")
        self._analyze()
        self.generate_outputs(output_dir)
        if edit_in_place:
            self.fixup_files_in_place()
        # make sure to update self.success if something goes wrong

    def locate_source_files(self) -> list[Path]:
        known_patterns = ["*.cc", "*.cpp"]  # "*.hh", could include hh here
        all_files = []
        for pattern in known_patterns:
            files_matching = self.root.glob(f"**/{pattern}")
            all_files.extend(list(files_matching))
        files_to_keep = []
        for file in all_files:
            if file.name in self.file_names_to_ignore:
                logger.log(f"Encountered ignored file: {file.name}; skipping")
                continue
            files_to_keep.append(file)
        return files_to_keep

    def _analyze(self):
        self.processed_files = []
        for file_num, source_file in enumerate(sorted(self.matched_files)):
            self.processed_files.append(SourceFile(source_file, self.function_call_list))
            logger.terminal_progress_bar(file_num + 1, len(self.matched_files), source_file.name)
        logger.terminal_progress_bar(1, 1, '\n')
        logger.log("Finished Processing, ready to generate results")

    def fixup_files_in_place(self):
        for s in self.processed_files:
            s.fixup_file_in_place()  # rewrite the file contents

    def generate_outputs(self, output_dir: Path) -> None:
        if not output_dir.exists():
            output_dir.mkdir()
        self.generate_json_outputs(output_dir / 'results.json')
        self.generate_file_summary_csv(output_dir / 'file_summary.csv')
        self.generate_line_details_csv(output_dir / 'lines_summary.csv')
        self.generate_line_details_plot(output_dir / 'distribution_plot.png')

    def generate_json_outputs(self, output_json_file: Path) -> None:
        full_json_content = {}
        for file_num, source_file in enumerate(self.processed_files):
            full_json_content[source_file.path.name] = source_file.group_and_summarize_function_calls()
            logger.terminal_progress_bar(file_num + 1, len(self.processed_files), source_file.path.name)
        logger.terminal_progress_bar(1, 1, '\n')
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
        num_data_sets = len(data)
        fig, axes = plt.subplots(num_data_sets, 1, layout='constrained')
        fig.set_size_inches(8, int(num_data_sets / 2))
        plot_num = -1
        for data_num, distribution in enumerate(data):
            plot_num += 1
            axes[plot_num].plot(distribution)
            axes[plot_num].set_ylabel(file_names[data_num], rotation=0, labelpad=150)
            axes[plot_num].set_yticklabels([])
            axes[plot_num].get_xaxis().set_visible(False)
            axes[plot_num].set_ylim([0, 20])
            logger.terminal_progress_bar(data_num + 1, len(data), '')
        logger.terminal_progress_bar(1, 1, '\n')
        logger.log("Results processed, plot being set up now (may take some time!)")
        plt.savefig(output_file_file)

from itertools import zip_longest
from json import dumps

import matplotlib.pyplot
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Optional

from energyplus_refactor_helper.logger import logger
from energyplus_refactor_helper.source_file import SourceFile


class SourceFolder:
    def __init__(self, root: Path, functions: list[str]):
        """
        The SourceFolder class represents a folder that is to be analyzed during this refactor.  The SourceFolder is
        aware of all settings and will recursively search for matching functions and analyze/edit as needed.

        :param root: The root directory to search for this pass.
        :param functions: A list of function calls to search for in the source files.
        """
        self.success = True  # assume success
        self.root = root
        self.function_call_list = functions
        # make sure to update self.success if something goes wrong

    def find_files(self, ignore: Optional[list[str]] = None, match_patterns: Optional[list[str]] = None) -> list[Path]:
        """
        A small worker function to locate source files inside the source directory.

        :param ignore: A list of file names to ignore when looking for source files to analyze.
        :param match_patterns: A list of match patterns for filenames, which will match using glob functionality.
        :return: A list of absolute paths to source files found during the search.
        """
        if ignore is None:
            ignore = []
        if match_patterns is None:
            match_patterns = ["*.cc", "*.cpp"]  # could include *.hh
        all_files = []
        for pattern in match_patterns:
            files_matching = self.root.glob(f"**/{pattern}")
            all_files.extend(list(files_matching))
        files_to_keep = []
        for file in all_files:
            if file.name in ignore:
                logger.log(f"Encountered ignored file: {file.name}; skipping")
                continue
            files_to_keep.append(file)
        return files_to_keep

    def analyze_source_files(self, matched_files: list[Path]) -> list[SourceFile]:
        """
        An internal worker function that processes all located source files and creates a list of SourceFile instances
        to be held on the self.processed_files member variable.

        :param matched_files: A list of Path instances to all matched source files to be processed here
        :return: Returns a list of SourceFile instances which have been parsed for function calls.
        """
        logger.log("Processing files to identify function calls (usually ~15 seconds)")
        processed_files = []
        for file_num, source_file in enumerate(sorted(matched_files)):
            processed_files.append(SourceFile(source_file, self.function_call_list))
            logger.terminal_progress_bar(file_num + 1, len(matched_files), source_file.name)
        logger.terminal_progress_done()
        return processed_files

    @staticmethod
    def rewrite_files_in_place(processed_files: list[SourceFile], visitor, operate_on_group: bool) -> None:
        """
        This function will loop over all processed files and fixup the function calls in place, overwriting the contents
        of the file.  Make sure the repository to be modified is prepared for this...git commit, etc.

        :param processed_files: A list of SourceFile instances that has been built by calling analyze_source_files
        :param visitor: A callable function that takes either a FunctionCall or a FunctionCallInstance and returns a
                        string.  The type should depend on the group_flag argument.
        :param operate_on_group: A flag indicating whether the action will operate on groups of function calls (if True)
                                 or individual function calls (if False)
        :return: None
        """
        logger.log("Now fixing up files in place with new function calls")
        num_files = len(processed_files)
        for file_num, s in enumerate(processed_files):
            s.write_new_text_to_file(visitor, operate_on_group)  # rewrite the file contents
            logger.terminal_progress_bar(file_num + 1, num_files, s.path.name)
        logger.terminal_progress_done()

    def generate_reports(self, processed_files: list[SourceFile], output_dir: Path, skip_plots: bool) -> None:
        """
        This function will generate all output files for this analysis, and drop them all into the specified output
        directory.  The output files will grow over time, and may be dependent on input arguments later.  For now the
        list includes a JSON summary, a file summary CSV, a line-by-line summary CSV, and a
        difficult-to-read-but-maybe-interesting plot showing the function distribution in each file.

        :param processed_files: A list of SourceFile instances that has been built by calling analyze_source_files
        :param output_dir: The output directory to write the outputs.  It will be created if it doesn't exist.
        :param skip_plots: A flag for whether we are skipping plot generation, which can be time-consuming
        :return: None
        """
        if not output_dir.exists():
            output_dir.mkdir()
        self.generate_json_outputs(processed_files, output_dir / 'results.json')
        self.generate_file_summary_csv(processed_files, output_dir / 'file_summary.csv')
        self.generate_line_details_csv(processed_files, output_dir / 'lines_summary.csv')
        if not skip_plots:
            self.generate_line_details_plot(processed_files, output_dir / 'distribution_plot.png')

    @staticmethod
    def generate_json_outputs(processed_files: list[SourceFile], output_json_file: Path) -> None:
        """
        This function generates an output JSON summary.  The summary includes each function call, along with the full
        list of parsed arguments, and the starting and ending line of each.  It also includes a special summary of each
        "group" of function calls, where a group is defined as function calls that exist on adjacent lines of code.
        This is primarily useful for refactoring "groups" of function calls together in a meaningful way.

        :param processed_files: A list of SourceFile instances that has been built by calling analyze_source_files
        :param output_json_file: The output file path to write.
        :return: None
        """
        logger.log("Building JSON summary output (usually ~10 seconds)")
        full_json_content = {}
        for file_num, source_file in enumerate(processed_files):
            full_json_content[source_file.path.name] = [g.to_json() for g in source_file.get_function_call_groups()]
            logger.terminal_progress_bar(file_num + 1, len(processed_files), source_file.path.name)
        logger.terminal_progress_done()
        output_json_file.write_text(dumps(full_json_content, indent=2))

    @staticmethod
    def generate_file_summary_csv(processed_files: list[SourceFile], output_csv_file: Path) -> None:
        """
        This function generates a file-by-file summary of how many function calls were parsed in each file.  Each row
        is a different file, with the number of successful function call parses and the number of failed parses.  This
        file is primarily a debugging aid, but could be useful for understanding how many function calls are in each.

        :param processed_files: A list of SourceFile instances that has been built by calling analyze_source_files
        :param output_csv_file: The output file path to write.
        :return: None
        """
        s = "File,Good,Bad\n"
        for result in processed_files:
            good = sum([1 if fe.appears_successful else 0 for fe in result.found_functions])
            bad = sum([0 if fe.appears_successful else 1 for fe in result.found_functions])
            s += f"{result.path},{good},{bad}\n"
        output_csv_file.write_text(s)

    @staticmethod
    def generate_line_details_csv(processed_files: list[SourceFile], output_csv_file: Path) -> None:
        """
        This function generates a basic distribution of function calls found in each file.  The file is a CSV where
        each file is a different column.  The rows are lines of code in that file, and the value in the dataset is
        either a 0 if that line does not contain a matched function call, and a 1 if it does.  A single column can be
        plotted to show how the function calls are distributed in that file.  This data could potentially be fed to
        other algorithms to help analyze/visualize/whatever this distribution.

        :param processed_files: A list of SourceFile instances that has been built by calling analyze_source_files
        :param output_csv_file: The output file path to write.
        :return: None
        """
        all_lists = [[x.path.name, *x.function_distribution] for x in processed_files]
        zipped_lists = zip_longest(*all_lists, fillvalue='')
        csv_string = ''.join([",".join(map(str, row)) + "\n" for row in zipped_lists])
        output_csv_file.write_text(csv_string)

    def generate_line_details_plot(self, processed_files: list[SourceFile], output_file_file: Path) -> None:
        """
        This function generates a (potentially huge) png plot of the matched function distribution in each file.  The
        generated png plots the function distribution based on the integer function types, so if this particular
        refactor is matching 10 different function names, the y-axis for each file will range from 0 to 9.  The png
        will be very tall if you are analyzing lots of files.  It is possible this output will be enabled/disabled
        based on input flags later.

        :param processed_files: A list of SourceFile instances that has been built by calling analyze_source_files
        :param output_file_file: The output file path to write.
        :return: None
        """
        logger.log("Building plot data (usually ~30 seconds)")
        y_max = len(self.function_call_list)
        file_names = [x.path.name for x in processed_files]
        data = [x.advanced_function_distribution for x in processed_files]
        num_data_sets = len(data)
        plot_data = plt.subplots(num_data_sets, 1, layout='constrained')
        fig: matplotlib.pyplot.Figure = plot_data[0]
        axes: list[matplotlib.pyplot.axes] = plot_data[1]
        fig.set_size_inches(8, int(num_data_sets / 2))
        plot_num = -1
        for data_num, distribution in enumerate(data):
            plot_num += 1
            axes[plot_num].plot(distribution)
            axes[plot_num].set_ylabel(file_names[data_num], rotation=0, labelpad=150)
            axes[plot_num].set_yticklabels([])
            axes[plot_num].get_xaxis().set_visible(False)
            axes[plot_num].set_ylim([0, y_max])
            logger.terminal_progress_bar(data_num + 1, len(data), '')
        logger.terminal_progress_done()
        logger.log("Results processed, plot being set up now (usually ~1 minute)")
        plt.savefig(output_file_file)

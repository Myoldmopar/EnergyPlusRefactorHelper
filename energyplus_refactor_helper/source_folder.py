from itertools import zip_longest
from json import dumps
import matplotlib.pyplot as plt
from pathlib import Path

from energyplus_refactor_helper.logger import logger
from energyplus_refactor_helper.source_file import SourceFile


class SourceFolder:
    def __init__(self, root: Path, out: Path, ignore: list[str], functions: list[str], edit: bool, match=None):
        """
        The SourceFolder class represents a folder that is to be analyzed during this refactor.  The SourceFolder is
        aware of all settings and will recursively search for matching functions and analyze/edit as needed.

        :param root: The root directory to search for this pass.
        :param out: The output directory to write logs and analysis files.
        :param ignore: A list of file names to ignore when looking for source files to analyze.
        :param functions: A list of function calls to search for in the source files.
        :param edit: A flag for whether to actually edit the found source files in place or not.
        :param match: A list of source file name patterns to match when searching.  If nothing is passed in, it will
                      default to finding all .cc and .cpp files.
        """
        self.success = True  # assume success
        self.root = root
        self.function_call_list = functions
        self.file_names_to_ignore = ignore
        self.matched_files = self.locate_source_files(match if match else ["*.cc", "*.cpp"])  # could include *.hh
        logger.log(f"SourceFolder object constructed, identified {len(self.matched_files)} files ready to analyze.")
        self._analyze()
        self.generate_outputs(out)
        if edit:
            self.fixup_files_in_place()
        # make sure to update self.success if something goes wrong

    def locate_source_files(self, match_patterns: list[str]) -> list[Path]:
        """
        A small worker function to locate source files inside the source directory.

        :param match_patterns: A list of match patterns for filenames, which will match using glob functionality.
        :return: A list of absolute paths to source files found during the search.
        """
        all_files = []
        for pattern in match_patterns:
            files_matching = self.root.glob(f"**/{pattern}")
            all_files.extend(list(files_matching))
        files_to_keep = []
        for file in all_files:
            if file.name in self.file_names_to_ignore:
                logger.log(f"Encountered ignored file: {file.name}; skipping")
                continue
            files_to_keep.append(file)
        return files_to_keep

    def _analyze(self) -> None:
        """
        An internal worker function that processes all located source files and creates a list of SourceFile instances
        to be held on the self.processed_files member variable.

        :return: None
        """
        logger.log("Processing files to identify function calls in each")
        self.processed_files = []
        for file_num, source_file in enumerate(sorted(self.matched_files)):
            self.processed_files.append(SourceFile(source_file, self.function_call_list))
            logger.terminal_progress_bar(file_num + 1, len(self.matched_files), source_file.name)
        logger.terminal_progress_done()

    def fixup_files_in_place(self) -> None:
        """
        This function will loop over all processed files and fixup the function calls in place, overwriting the contents
        of the file.  Make sure the repository to be modified is prepared for this...git commit, etc.

        :return: None
        """
        logger.log("Now fixing up files in place with new function calls")
        num_files = len(self.processed_files)
        for file_num, s in enumerate(self.processed_files):
            s.fixup_file_in_place()  # rewrite the file contents
            logger.terminal_progress_bar(file_num + 1, num_files, s.path.name)
        logger.terminal_progress_done()

    def generate_outputs(self, output_dir: Path) -> None:
        """
        This function will generate all output files for this analysis, and drop them all into the specified output
        directory.  The output files will grow over time, and may be dependent on input arguments later.  For now the
        list includes a JSON summary, a file summary CSV, a line-by-line summary CSV, and a
        difficult-to-read-but-maybe-interesting plot showing the function distribution in each file.

        :param output_dir: The output directory to write the outputs.  It will be created if it doesn't exist.
        :return: None
        """
        if not output_dir.exists():
            output_dir.mkdir()
        self.generate_json_outputs(output_dir / 'results.json')
        self.generate_file_summary_csv(output_dir / 'file_summary.csv')
        self.generate_line_details_csv(output_dir / 'lines_summary.csv')
        self.generate_line_details_plot(output_dir / 'distribution_plot.png')

    def generate_json_outputs(self, output_json_file: Path) -> None:
        """
        This function generates an output JSON summary.  The summary includes each function call, along with the full
        list of parsed arguments, and the starting and ending line of each.  It also includes a special summary of each
        "group" of function calls, where a group is defined as function calls that exist on adjacent lines of code.
        This is primarily useful for refactoring "groups" of function calls together in a meaningful way.

        :param output_json_file: The output file path to write.
        :return: None
        """
        logger.log("Building JSON summary output")
        full_json_content = {}
        for file_num, source_file in enumerate(self.processed_files):
            full_json_content[source_file.path.name] = source_file.group_and_summarize_function_calls()
            logger.terminal_progress_bar(file_num + 1, len(self.processed_files), source_file.path.name)
        logger.terminal_progress_done()
        output_json_file.write_text(dumps(full_json_content, indent=2))

    def generate_file_summary_csv(self, output_csv_file: Path) -> None:
        """
        This function generates a file-by-file summary of how many function calls were parsed in each file.  Each row
        is a different file, with the number of successful function call parses and the number of failed parses.  This
        file is primarily a debugging aid, but could be useful for understanding how many function calls are in each.

        :param output_csv_file: The output file path to write.
        :return: None
        """
        s = "File,Good,Bad\n"
        for result in self.processed_files:
            good = sum([1 if fe.appears_successful else 0 for fe in result.found_functions])
            bad = sum([0 if fe.appears_successful else 1 for fe in result.found_functions])
            s += f"{result.path},{good},{bad}\n"
        output_csv_file.write_text(s)

    def generate_line_details_csv(self, output_csv_file: Path) -> None:
        """
        This function generates a basic distribution of function calls found in each file.  The file is a CSV where
        each file is a different column.  The rows are lines of code in that file, and the value in the dataset is
        either a 0 if that line does not contain a matched function call, and a 1 if it does.  A single column can be
        plotted to show how the function calls are distributed in that file.  This data could potentially be fed to
        other algorithms to help analyze/visualize/whatever this distribution.

        :param output_csv_file: The output file path to write.
        :return: None
        """
        all_lists = [[x.path.name, *x.function_distribution] for x in self.processed_files]
        zipped_lists = zip_longest(*all_lists, fillvalue='')
        csv_string = ''.join([",".join(map(str, row)) + "\n" for row in zipped_lists])
        output_csv_file.write_text(csv_string)

    def generate_line_details_plot(self, output_file_file: Path) -> None:
        """
        This function generates a (potentially huge) png plot of the matched function distribution in each file.  The
        generated png plots the function distribution based on the integer function types, so if this particular
        refactor is matching 10 different function names, the y-axis for each file will range from 0 to 9.  The png
        will be very tall if you are analyzing lots of files.  It is possible this output will be enabled/disabled
        based on input flags later.

        :param output_file_file: The output file path to write.
        :return: None
        """
        logger.log("Building plot data")
        y_max = len(self.function_call_list)
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
            axes[plot_num].set_ylim([0, y_max])
            logger.terminal_progress_bar(data_num + 1, len(data), '')
        logger.terminal_progress_done()
        logger.log("Results processed, plot being set up now (may take some time!)")
        plt.savefig(output_file_file)

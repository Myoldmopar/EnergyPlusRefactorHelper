# this file will include an abstract base class for any specific refactor
# it will, for now, also include any example refactor configs
from pathlib import Path
from typing import Type

import spacy

from energyplus_refactor_helper.logger import logger
from energyplus_refactor_helper.source_folder import SourceFolder


class RefactorBase:
    """
    This is an abstract base class for refactors in this package.  Right now it only supports finding function calls, so
    the only thing really needed from a derived class is to override the function_calls() pure virtual method here.
    There are other methods which can be used to set/override refactor parameters if needed.
    """

    # noinspection PyMethodMayBeStatic
    def file_names_to_ignore(self) -> list[str]:
        """
        This method returns a list of file names that should be ignored during this refactor.  The primary reason for
        this is to avoid having the refactor engine match the actual function definition/declaration.  By default, this
        returns an empty list, but should return file names as strings if it is overridden.

        :return: A list of file names that should be ignored during this refactor.
        """
        return []

    # noinspection PyMethodMayBeStatic
    def analysis_root_from_repo_root(self, repo_root_path: Path) -> Path:
        """
        This method returns a Path to the root of the refactor search.  The primary use of this method is to isolate the
        refactor to only a certain subdirectory.  By default, this method returns the src/EnergyPlus directory within
        the repository, but can be overridden to return any directory relative to the EnergyPlus project/repo root.

        :param repo_root_path: The root of the EnergyPlus repository/project.
        :return: A Path object relative to the passed in repository root.
        """
        return repo_root_path / 'src' / 'EnergyPlus'

    def function_calls(self) -> list[str]:  # return something better eventually
        """
        This method returns a list of function names that should be matched during this refactor.  In the future, it is
        expected that this function returns more meaningful information, but this is all that is needed right now.

        :return: A list of function names.
        """
        raise NotImplementedError()

    @staticmethod
    def default_function_call_visitor(function_call) -> str:
        """
        This is a small helper function that simply takes a function call argument, and rewrites it in a functionally
        equivalent manner, returning that string.

        :param function_call: The FunctionCall instance to operate on
        ;return str: The function call in a functionally equivalent string
        """
        return function_call.rewrite()

    @staticmethod
    def default_function_group_visitor(function_group) -> str:
        individual_call_strings = []
        for i, function in enumerate(function_group.function_calls):
            full_call = function.rewrite()
            include_prefix = len(function_group.function_calls) > 0 and i > 0
            including_prefix = (function.preceding_text + full_call) if include_prefix else full_call
            individual_call_strings.append(including_prefix)
        return '\n'.join(individual_call_strings)

    # noinspection PyMethodMayBeStatic
    def visitor(self, function_call_or_group) -> str:
        """
        This method will visit _either_ each function call, or each function call group, and generate a new string
        representation of that call or group.  The object passed in is determined by the visits_each_group() member
        method on this class.  By default, it will be False, indicating that this action should operate on each function
        call.  However, if that method returns True, this method will need to expect an entire function call group.

        :param function_call_or_group: The FunctionCall or FunctionCallGroup to inspect, and from that, generate a new
                                       string representation.  By default, the base action will get visited on each
                                       function call, and generate a 'single line' version of the function call.
                                       The advantage of this is that we can verify our parsing by simply rewriting all
                                       function calls in the source code, reapplying Clang Format, and making sure we
                                       didn't break anything.
        :return: A string representation of the function call or function call group.
        """
        return RefactorBase.default_function_call_visitor(function_call_or_group)

    # noinspection PyMethodMayBeStatic
    def visits_each_group(self) -> bool:
        return False

    def run(self, source_repo: Path, output_path: Path, edit_in_place: bool, skip_plots: bool) -> int:
        """
        This method performs the actual run operations based on input arguments.  The method calls (possibly overridden)
        methods to get run data, then creates a SourceFolder instance, performs operations, and returns a success flag
        with 0 if successful and 1 if not.

        :param source_repo: The root of the EnergyPlus repository to operate upon.
        :param output_path: An output directory where logs and results should be dumped.
        :param edit_in_place: A flag for whether we are actually editing the repository files in place.  If not, then
                              this will mostly just result in analysis, with outputs in the output_path provided.
        :param skip_plots: A flag for whether to skip plot generation, which can be time-consuming.
        :return: A status flag, 0 if successful, 1 if not.
        """
        root_path = self.analysis_root_from_repo_root(source_repo)
        sf = SourceFolder(root_path, self.function_calls())
        matched_source_files = sf.find_files(self.file_names_to_ignore())
        processed_source_files = sf.analyze_source_files(matched_source_files)
        sf.generate_reports(processed_source_files, output_path, skip_plots=skip_plots)
        if edit_in_place:
            sf.rewrite_files_in_place(processed_source_files, self.visitor, self.visits_each_group())
        return 0 if sf.success else 1


class ErrorCallRefactor(RefactorBase):
    """
    This is a specific derived refactor class focused on error calls.  Some of the virtual methods have been overridden
    and have their own description below.
    """

    def file_names_to_ignore(self) -> list[str]:
        """
        This method returns just UtilityRoutines.cc, which is where these error functions are located.

        :return: A list with a single object, a string UtilityRoutines.cc
        """
        return ['UtilityRoutines.cc']

    class CallSymbols:
        ShowFatalError = 0
        ShowSevereError = 1
        ShowSevereMessage = 2
        ShowContinueError = 3
        ShowWarningError = 6

    def function_calls(self) -> list[str]:
        """
        This method returns all the error functions we want to match during this refactor.

        :return: A list of error function names
        """
        return [
            "ShowFatalError",
            "ShowSevereError",
            "ShowSevereMessage",
            "ShowContinueError",
            "ShowContinueErrorTimeStamp",
            "ShowMessage",
            "ShowWarningError",
            "ShowWarningMessage",
            "ShowRecurringSevereErrorAtEnd",
            "ShowRecurringWarningErrorAtEnd",
            "ShowRecurringContinueErrorAtEnd",
            "StoreRecurringErrorMessage",
            # "ShowErrorMessage",  not in the public interface anymore
            "SummarizeErrors",
            "ShowRecurringErrors",
            "ShowSevereDuplicateName",
            "ShowSevereItemNotFound",
            "ShowSevereInvalidKey",
            "ShowSevereInvalidBool",
            "ShowSevereEmptyField",
            "ShowWarningInvalidKey",
            "ShowWarningInvalidBool",
            "ShowWarningEmptyField",
            "ShowWarningItemNotFound"
        ]

    def visitor(self, function_group) -> str:
        """
        For this action class, this function will be visited for each function call "group".  This function will assess
        the function group, looking for different ways to rewrite the group as a new string.  For right now, this will
        simply iterate over the function group as a whole and rewrite each function call on a new line.  This allows for
        a nice quick test where we can re-apply Clang Format and get back nearly identical code.  In upcoming versions,
        this function will instead group multiple function calls into a single new interface with the messages passed as
        an initializer-list-based array of strings, and also a (for now) dummy error code.  In the final version, this
        will write correct error codes.

        :param function_group: The FunctionCallGroup to inspect, and from that, generate a new string representation.
        :return: A string representation of the function call group.
        """
        if any([f.preceding_text != "" for f in function_group.function_calls]):
            # if there is meaningful text in the group, outside the function calls themselves, just ignore this group
            return RefactorBase.default_function_group_visitor(function_group)
        else:
            # get some convenience variables
            one_liner = len(function_group.function_calls) == 1
            first_call = function_group.function_calls[0]
            last_call = function_group.function_calls[-1]
            middle_calls = function_group.function_calls[1:-1]
            # Look for specific opportunities to refactor.  Let's start with a severe + [N>=0 continue error] + fatal.
            starts_with_fatal = first_call.call_type == self.CallSymbols.ShowFatalError
            starts_with_severe = first_call.call_type == self.CallSymbols.ShowSevereError
            starts_with_warning = first_call.call_type == self.CallSymbols.ShowWarningError
            ends_with_fatal = last_call.call_type == self.CallSymbols.ShowFatalError
            ends_with_continue = last_call.call_type == self.CallSymbols.ShowContinueError
            if len(function_group.function_calls) <= 2:
                valid_middle = True
            else:
                valid_middle = all([f.call_type == self.CallSymbols.ShowContinueError for f in middle_calls])
            state = function_group.function_calls[0].parse_arguments()[0]
            remaining_arguments = [f.parse_arguments()[1] for f in function_group.function_calls]
            argument_one = function_group.function_calls[0].parse_arguments()[1]
            argument_listing = "{" + ", ".join(remaining_arguments) + "}"
            # regroup the errors into a single function call, with a default error code for now
            if starts_with_severe and valid_middle and ends_with_fatal:
                return f"emitErrorMessages({state}, -999, {argument_listing}, true);"
            elif starts_with_severe and valid_middle and ends_with_continue:
                return f"emitErrorMessages({state}, -999, {argument_listing}, false);"
            elif starts_with_warning and valid_middle and ends_with_continue:
                return f"emitWarningMessages({state}, -999, {argument_listing});"
            elif one_liner and starts_with_warning:
                return f"emitWarningMessage({state}, -999, {argument_one});"
            elif one_liner and starts_with_severe:
                return f"emitErrorMessage({state}, -999, {argument_one}, false);"
            elif one_liner and starts_with_fatal:
                return f"emitErrorMessage({state}, -999, {argument_one}, true);"
            else:
                return RefactorBase.default_function_group_visitor(function_group)

    # noinspection PyMethodMayBeStatic
    def visits_each_group(self) -> bool:
        return True

    def run(self, source_repo: Path, output_path: Path, edit_in_place: bool, skip_plots: bool) -> int:
        """This method performs the actual run operations based on input arguments for the error call action.
        This is similar to the base class run() method, but with some specializations.  For example, this run() method
        gathers the error calls into a special structure where we can find similarities and lookup meaningful grouping
        information.

        :param source_repo: The root of the EnergyPlus repository to operate upon.
        :param output_path: An output directory where logs and results should be dumped.
        :param edit_in_place: A flag for whether we are actually editing the repository files in place.  If not, then
                              this will mostly just result in analysis, with outputs in the output_path provided.
        :param skip_plots: A flag for whether to skip plot generation, which can be time-consuming.
        :return: A status flag, 0 if successful, 1 if not.
        """
        root_path = self.analysis_root_from_repo_root(source_repo)
        source_folder = SourceFolder(root_path, self.function_calls())
        matched_source_files = source_folder.find_files(self.file_names_to_ignore())
        processed_source_files = source_folder.analyze_source_files(matched_source_files)
        error_message_texts = []
        for source_file in processed_source_files:
            for group in source_file.found_function_groups:
                new_group_text = self.visitor(group)
                error_message_texts.append(new_group_text.replace('\n', ' '))
        nlp = spacy.load("en_core_web_md")
        encounters = set()
        compares = set()
        docs = list(nlp.pipe(error_message_texts))
        n = len(docs)
        expected_comparison_count = (n * n - n) / 2
        counter = 0
        logger.log("About to determine text similarities between messages")
        for i, d1 in enumerate(docs):
            for j, d2 in enumerate(docs):
                if i == j or (i, j) in encounters or (j, i) in encounters:
                    continue
                encounters.add((i, j))
                compares.add((d1.text, d2.text, d1.similarity(d2)))
                counter += 1
                if counter % 200 == 0:
                    logger.terminal_progress_bar(counter, expected_comparison_count, (i, j))
        logger.terminal_progress_done()
        with open('/tmp/output.txt', 'w') as f:
            for i, compare in enumerate(sorted(compares, key=lambda x: x[2], reverse=True)):
                if i > 10000:
                    break
                f.write(f"{compare[0]} 😊 {compare[1]} 😊 {compare[2]}\n")
        source_folder.generate_reports(processed_source_files, output_path, skip_plots=skip_plots)
        if edit_in_place:
            source_folder.rewrite_files_in_place(processed_source_files, self.visitor, self.visits_each_group())
        return 0 if source_folder.success else 1


all_actions: dict[str, Type[RefactorBase]] = {
    'error_call_refactor': ErrorCallRefactor
}

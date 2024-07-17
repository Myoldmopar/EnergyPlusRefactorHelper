from json import loads
from os import environ
from pathlib import Path
from time import time

import spacy
from spacy.tokens import Doc

from energyplus_refactor_helper.logger import logger
from energyplus_refactor_helper.source_folder import SourceFolder
from energyplus_refactor_helper.actions.base import RefactorBase


class ErrorCallRefactor(RefactorBase):
    """
    This is a specific derived refactor class focused on error calls.  Some of the virtual methods have been overridden
    and have their own description below.
    """

    class CallSymbols:
        ShowFatalError = 0
        ShowSevereError = 1
        ShowSevereMessage = 2
        ShowContinueError = 3
        ShowWarningError = 6
        ShowWarningMessage = 7

    class NewErrorCodes:
        error_code_unclassified = -999
        error_code_input_invalid = 1000
        error_code_input_field_not_found = 1100
        error_code_input_field_blank = 1200
        error_code_input_object_not_found = 1300
        error_code_input_cannot_find_object = 1350  # after input processing is done, this is when it can't get an index
        error_code_input_topology_problem = 1400
        error_code_input_unused = 1500
        error_code_input_fatal = 1800
        error_code_runtime_general = 2000
        error_code_runtime_flow_out_of_range = 2100
        error_code_runtime_temp_out_of_range = 2200
        error_code_runtime_airflow_network = 2300
        error_code_fatal_general = 3000
        error_code_developer_general = 4000
        error_code_developer_invalid_index = 4100

        @staticmethod
        def get_value(code_name: str) -> int:
            if code_name == 'error_code_unclassified':
                return ErrorCallRefactor.NewErrorCodes.error_code_unclassified
            elif code_name == 'error_code_input_invalid':
                return ErrorCallRefactor.NewErrorCodes.error_code_input_invalid
            elif code_name == 'error_code_input_field_not_found':
                return ErrorCallRefactor.NewErrorCodes.error_code_input_field_not_found
            elif code_name == 'error_code_input_field_blank':
                return ErrorCallRefactor.NewErrorCodes.error_code_input_field_blank
            elif code_name == 'error_code_input_object_not_found':
                return ErrorCallRefactor.NewErrorCodes.error_code_input_object_not_found
            elif code_name == 'error_code_input_cannot_find_object':
                return ErrorCallRefactor.NewErrorCodes.error_code_input_cannot_find_object
            elif code_name == 'error_code_input_topology_problem':
                return ErrorCallRefactor.NewErrorCodes.error_code_input_topology_problem
            elif code_name == 'error_code_input_unused':
                return ErrorCallRefactor.NewErrorCodes.error_code_input_unused
            elif code_name == 'error_code_input_fatal':
                return ErrorCallRefactor.NewErrorCodes.error_code_input_fatal
            elif code_name == 'error_code_runtime_general':
                return ErrorCallRefactor.NewErrorCodes.error_code_runtime_general
            elif code_name == 'error_code_runtime_flow_out_of_range':
                return ErrorCallRefactor.NewErrorCodes.error_code_runtime_flow_out_of_range
            elif code_name == 'error_code_runtime_temp_out_of_range':
                return ErrorCallRefactor.NewErrorCodes.error_code_runtime_temp_out_of_range
            elif code_name == 'error_code_runtime_airflow_network':
                return ErrorCallRefactor.NewErrorCodes.error_code_runtime_airflow_network
            elif code_name == 'error_code_fatal_general':
                return ErrorCallRefactor.NewErrorCodes.error_code_fatal_general
            elif code_name == 'error_code_developer_general':
                return ErrorCallRefactor.NewErrorCodes.error_code_developer_general
            elif code_name == 'error_code_developer_invalid_index':
                return ErrorCallRefactor.NewErrorCodes.error_code_developer_invalid_index
            else:
                raise ValueError(f"Bad error code in NewErrorCodes.get_value: {code_name}")

    def __init__(self):
        super().__init__()
        self.matched_error_codes = 0
        self.missed_error_codes = 0
        self.nlp = spacy.load("en_core_web_md")
        actions_dir = Path(__file__).resolve().parent
        known_errors_file = actions_dir / "known_error_calls.json"
        json_data = loads(known_errors_file.read_text())
        codes = json_data["known_error_codes"]
        self.known_codes = [(self.nlp(c["message"]), self.NewErrorCodes.get_value(c['code'])) for c in codes]

    @staticmethod
    def function_calls() -> list[str]:
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
            return RefactorBase.base_function_group_visitor(function_group)
        else:
            # get some convenience variables
            one_liner = len(function_group.function_calls) == 1
            first_call = function_group.function_calls[0]
            last_call = function_group.function_calls[-1]
            middle_calls = function_group.function_calls[1:-1]
            # Look for specific opportunities to refactor.  Let's start with a severe + [N>=0 continue error] + fatal.
            starts_with_fatal = first_call.call_type == self.CallSymbols.ShowFatalError
            starts_with_severe = first_call.call_type == self.CallSymbols.ShowSevereError
            starts_with_warning = first_call.call_type == self.CallSymbols.ShowWarningMessage
            starts_with_warning_error = first_call.call_type == self.CallSymbols.ShowWarningError
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

            def text(code: int = -999) -> str:
                if starts_with_severe and valid_middle and ends_with_fatal:
                    return f"emitErrorMessages({state}, {code}, {argument_listing}, true);"
                elif starts_with_severe and valid_middle and ends_with_continue:
                    return f"emitErrorMessages({state}, {code}, {argument_listing}, false);"
                elif starts_with_warning and valid_middle and ends_with_continue:
                    return f"emitWarningMessages({state}, {code}, {argument_listing});"
                elif starts_with_warning_error and valid_middle and ends_with_continue:
                    return f"emitWarningMessages({state}, {code}, {argument_listing}, true);"
                elif one_liner and starts_with_warning:
                    return f"emitWarningMessage({state}, {code}, {argument_one});"
                elif one_liner and starts_with_warning_error:
                    return f"emitWarningMessage({state}, {code}, {argument_one}, true);"
                elif one_liner and starts_with_severe:
                    return f"emitErrorMessage({state}, {code}, {argument_one}, false);"
                elif one_liner and starts_with_fatal:
                    return f"emitErrorMessage({state}, {code}, {argument_one}, true);"
                else:
                    return RefactorBase.base_function_group_visitor(function_group)

            unclassified_text = text()
            potential_error_code = self.get_error_code(self.nlp(unclassified_text))
            if potential_error_code == self.NewErrorCodes.error_code_unclassified:
                return unclassified_text
            else:
                return text(potential_error_code)

    def get_error_code(self, error_message_spacy_doc: Doc) -> int:
        high_score = 0
        high_score_index = -1
        for i, x in enumerate(self.known_codes):
            doc, code_number = x
            score = error_message_spacy_doc.similarity(doc)
            if score > high_score:
                high_score = score
                high_score_index = i
        if high_score > 0.9:
            return self.known_codes[high_score_index][1]
        return self.NewErrorCodes.error_code_unclassified

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
        root_path = source_repo / 'src' / 'EnergyPlus'
        source_folder = SourceFolder(root_path, self.function_calls())
        matched_source_files = source_folder.find_files(['UtilityRoutines.cc'])
        processed_source_files = source_folder.analyze_source_files(matched_source_files)
        error_message_texts = []
        for source_file in processed_source_files:
            for group in source_file.found_function_groups:
                new_group_text = self.visitor(group)
                error_message_texts.append(new_group_text.replace('\n', ' '))
        nlp = spacy.load("en_core_web_md")
        encounters = set()
        compares = set()
        logger.log("Generating SpaCy text structures (usually ~20 seconds)")
        docs = list(nlp.pipe(error_message_texts))
        n = len(docs)
        expected_comparison_count = (n * n - n) / 2
        counter = 0
        start_time = time()
        logger.log("About to determine text similarities between messages (usually ~20+ minutes)")
        for i, d1 in enumerate(docs):
            for j, d2 in enumerate(docs):
                if i == j or (i, j) in encounters or (j, i) in encounters:
                    continue
                encounters.add((i, j))
                compares.add((d1.text, d2.text, d1.similarity(d2)))
                counter += 1
                if counter % 200 == 0:  # pragma: no cover
                    elapsed_time = time() - start_time
                    estimated_total_time = (elapsed_time / (counter + 1)) * expected_comparison_count
                    estimated_seconds_remaining = estimated_total_time - elapsed_time
                    estimated_time = f"Estimated time remaining: {estimated_seconds_remaining:.1f}s"
                    if estimated_seconds_remaining >= 60:
                        minutes = int(estimated_seconds_remaining // 60)
                        remaining_seconds = estimated_seconds_remaining % 60
                        estimated_time = f"Estimated time remaining: {minutes}m {remaining_seconds:.1f}s"
                    logger.terminal_progress_bar(counter, expected_comparison_count, estimated_time)
        logger.terminal_progress_done()
        # don't do this on CI
        if 'CI' not in environ:  # pragma: no cover
            comparison_file_path = output_path / 'comparisons.txt'
            with comparison_file_path.open('w') as f:
                for i, compare in enumerate(sorted(compares, key=lambda x: x[2], reverse=True)):
                    if i > 10000:  # pragma: no cover
                        break
                    f.write(f"{compare[0]} 😊 {compare[1]} 😊 {compare[2]}\n")
        source_folder.generate_reports(processed_source_files, output_path, skip_plots=skip_plots)
        if edit_in_place:  # pragma: no cover
            # the rewrite files in place method is already being tested, not including it in coverage here
            source_folder.rewrite_files_in_place(processed_source_files, self.visitor, True)
        return 0 if source_folder.success else 1

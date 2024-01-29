from pathlib import Path
from typing import Optional

from energyplus_refactor_helper.function_call_group import FunctionCallGroup
from energyplus_refactor_helper.function_call import FunctionCall


class SourceFile:

    def __init__(self, path: Path, function_calls: list[str], group_flag: bool, visitor):
        """
        This class represents a single source code file, processing it to find all matching function calls, and
        providing functionality to refactor them into a new form automatically.

        :param path: The Path instance pointing to this source file
        :param function_calls: The list of function calls currently being searched
        :param group_flag: A flag indicating whether the action will operate on groups of function calls (if True)
                                 or individual function calls (if False)
        :param visitor: A callable function that takes either a FunctionCall or a FunctionCallInstance and returns a
                        string.  The type should depend on the group_flag argument.
        """
        self.path = path
        self.visitor = visitor
        self.operate_on_group = group_flag
        self.functions = function_calls
        self.original_file_text = self.path.read_text()
        self.file_lines = self.original_file_text.split('\n')
        self.found_functions = self.find_functions_in_original_text()
        self.found_function_groups = self.get_function_call_groups()
        self.function_distribution = self.get_binary_function_distribution()
        self.advanced_function_distribution = self.get_advanced_function_distribution()

    @staticmethod
    def find_function_in_raw_line(functions: list[str], full_raw_line: str) -> tuple[Optional[int], int]:
        """
        A simple worker function that searches a source line looking for one of the function call strings, and if found,
        returns both the found value along with the index in the line where it was found.

        :param functions: A list of function calls as defined in one of the config classes
        :param full_raw_line: A full line from the rwa source code, to be searched.
        :return: A tuple, where the first item is an optional found error call type int, and the second is the index.
        """
        for func_index, func in enumerate(functions):
            func_call = f"{func}("
            if func_call in full_raw_line:
                return func_index, full_raw_line.index(func)
        return None, -1

    def find_functions_in_original_text(self) -> list[FunctionCall]:
        """
        Processes the original source code for this file, identifying all function calls.
        This function fills an array with FunctionCall objects for each function call processed.

        :return: A list of FunctionCall instances, one for each function call processed.
        """
        line_number = 1
        call: Optional[FunctionCall] = None
        parsing_multiline = False
        raw_line_start_char_index = 0
        raw_line_end_char_index = -1
        found_functions = []
        while line_number <= len(self.file_lines):
            raw_line = self.file_lines[line_number - 1]
            raw_line_end_char_index += len(raw_line) + 1  # includes the \n at the end of the line
            cleaned_line = raw_line
            if '//' in raw_line:  # TODO: danger -- could be inside a string literal
                cleaned_line = raw_line[:cleaned_line.index('//')]
            if parsing_multiline:
                call.add_to_multiline_text(raw_line)
                reset = False
                if len(call.multiline_text) > FunctionCall.MAX_LINES_FOR_SINGLE_CALL:
                    character_end_index = call.char_start_in_file + len(raw_line)
                    call.finalize(character_end_index, False)
                    reset = True
                elif cleaned_line.strip().endswith(';'):
                    character_end_index = raw_line_start_char_index + raw_line.rfind(';')
                    call.finalize(character_end_index, True)
                    reset = True
                if reset:
                    found_functions.append(call)
                    call = None
                    parsing_multiline = False
            else:
                if any([f"{x}(" in cleaned_line for x in self.functions]):
                    call_type, call_index_in_line = self.find_function_in_raw_line(self.functions, raw_line)
                    function_name = self.functions[call_type]
                    character_start_index = raw_line_start_char_index + call_index_in_line
                    call = FunctionCall(
                        call_type, function_name, line_number, character_start_index, call_index_in_line, raw_line
                    )
                    if cleaned_line.strip().endswith(';'):
                        character_end_index = raw_line_start_char_index + raw_line.rfind(';')
                        call.finalize(character_end_index, True)
                        found_functions.append(call)
                        call = None
                    else:
                        parsing_multiline = True
            raw_line_start_char_index = raw_line_end_char_index + 1
            line_number += 1
        return found_functions

    def get_binary_function_distribution(self) -> list[int]:
        """
        Returns a distribution of function calls for the given file.  This simply returns a 0 or 1, where
        1 indicates the line is part of a function call, and 0 means it is not.

        :return: An array of integers, one per line of original source code, indicating function call for that line.
        """
        lines_with_functions = []
        for fe in self.found_functions:
            for line_num in range(fe.starting_line_number - 1, fe.ending_line_number):
                if line_num not in lines_with_functions:
                    lines_with_functions.append(line_num)
        return [1 if x + 1 in lines_with_functions else 0 for x in range(len(self.file_lines))]

    def get_advanced_function_distribution(self) -> list[int]:
        """
        Returns a distribution of function calls for the given file.  This returns an integer for the function
        call type from the specific function call search config list, from 1 to N, where N is the number of
        function calls being searched.

        :return: An array of integers, one per line of original source code, indicating function call for that line.
        """
        line_values = [0] * len(self.file_lines)
        for fe in self.found_functions:
            for line_num in range(fe.starting_line_number - 1, fe.ending_line_number):
                line_values[line_num] = max(line_values[line_num], fe.call_type)
        return line_values

    def get_new_file_text_function_based(self, func_visitor) -> str:
        """
        Modifies the original file text, replacing every function call with the modified version.

        :return: Returns the modified source code as a Python string.
        """
        new_text = self.original_file_text
        for fc in reversed(self.found_functions):
            new_text = new_text[:fc.char_start_in_file] + func_visitor(fc) + new_text[fc.char_end_in_file + 1:]
        return new_text

    def get_new_file_text_group_based(self, group_visitor) -> str:
        """
        Modifies the original file text, replacing every function call group with the modified version.

        :return: Returns the modified source code as a Python string.
        """
        # TODO: Add a unit test that works on function call groups
        # TODO: Just create dummy RefactorBase-d test action classes that we use in all the unit tests
        new_text = self.original_file_text
        for fg in reversed(self.found_function_groups):
            first = fg.function_calls[0]
            last = fg.function_calls[-1]
            new_text = new_text[:first.char_start_in_file] + group_visitor(fg) + new_text[last.char_end_in_file + 1:]
        return new_text

    def write_new_text_to_file(self) -> None:
        """
        Overwrites existing file contents with the modified version, replacing each function call with the new version
        as defined by the action instance itself.

        :return: None
        """
        if self.operate_on_group:
            self.path.write_text(self.get_new_file_text_group_based(self.visitor))
        else:
            self.path.write_text(self.get_new_file_text_function_based(self.visitor))

    def get_function_call_groups(self) -> list[FunctionCallGroup]:
        """
        This function loops over all found function calls in this file, groups them together into FunctionCallChunk
        instances.

        :return: A list of FunctionCallChunk instances containing full function call info for this file.
        """
        all_args_for_file = []
        last_call_ended_on_line_number = -1
        group = FunctionCallGroup()
        last_call_index = len(self.found_functions) - 1
        for i, f in enumerate(self.found_functions):
            if f.starting_line_number == last_call_ended_on_line_number + 1:
                group.add_function_call(f)
                if i == last_call_index:
                    all_args_for_file.append(group)
            else:
                if group.started:
                    all_args_for_file.append(group)
                group = FunctionCallGroup(f)  # reset the list starting with the current one
                if i == last_call_index:  # this is the last error, add it to the list before leaving
                    all_args_for_file.append(group)
            last_call_ended_on_line_number = f.ending_line_number
        return all_args_for_file

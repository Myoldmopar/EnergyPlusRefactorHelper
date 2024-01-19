from itertools import groupby
from pathlib import Path
from typing import Optional

from energyplus_refactor_helper.function_call import FunctionCall


class SourceFile:
    """
    This class represents a single source code file, processing it to find all matching function calls, and
    providing functionality to refactor them into a new form automatically.
    """

    def __init__(self, path: Path, function_call_list: list[str]):
        self.path = path
        self.functions = function_call_list
        self.original_file_text = self.path.read_text()
        self.file_lines = self.original_file_text.split('\n')
        self.found_functions = self.find_functions_in_original_text()
        self.function_distribution = self.get_function_distribution()
        self.advanced_function_distribution = self.get_advanced_function_distribution()

    @staticmethod
    def type_and_start_index_from_raw_line(functions: list[str], full_raw_line: str) -> tuple[Optional[int], int]:
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
                    call_type, call_index_in_line = self.type_and_start_index_from_raw_line(self.functions, raw_line)
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

    def get_function_distribution(self) -> list[int]:
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

    def file_text_fixed_up(self) -> str:
        """
        Modifies the original file text, replacing every function call with the modified version.

        :return: Returns the modified source code as a Python string.
        """
        new_text = self.original_file_text
        for fe in reversed(self.found_functions):
            new_text = new_text[:fe.char_start_in_file] + fe.as_new_version() + new_text[fe.char_end_in_file + 1:]
        return new_text

    def fixup_file_in_place(self) -> None:
        # open the file, rewrite with new text
        self.path.write_text(self.file_text_fixed_up())

    @staticmethod
    def create_function_call_chunk_summary(call_group: list[dict]) -> dict:
        """
        This function creates a dict summary of a chunk of contiguous function calls.  It is expected this function will
        change to returning a nice structure instead of a loosely defined dictionary.

        :param call_group: A list of dictionaries where each item is a single function call dict.  It is expected that
                           this argument will change to a list of structs eventually.
        :return: A single dictionary summary.
        """
        # TODO: Change this to return a struct, not a dict
        num_calls_in_this_chunk = len(call_group)
        call_types = [e['type'] for e in call_group]
        cleaned_call_types = [i[0] for i in groupby(call_types)]  # remove duplicates
        chunk_start_line = call_group[0]['line_start']
        chunk_end_line = call_group[-1]['line_end']
        try:
            concatenated_messages = ' *** '.join([e['args'][1] for e in call_group])
        except IndexError:  # pragma: no cover
            # this is almost certainly indicative of a parser problem, so we can't cover it
            raise Exception(f"Something went wrong with the arg processing for this chunk! {call_group}")
        return {
            'num_calls_in_this_chunk': num_calls_in_this_chunk,
            'call_types': call_types,
            'cleaned_call_types': cleaned_call_types,
            'chunk_start_line': chunk_start_line,
            'chunk_end_line': chunk_end_line,
            'concatenated_messages': concatenated_messages
        }

    def group_and_summarize_function_calls(self) -> list[dict]:
        """
        This function loops over all found function calls in this file, groups them together into contiguous chunks,
        and results in a list summary of all the function calls.

        :return: A list of dicts containing full function call info for this file.  It is expected that this will
                 eventually be converted over to return a list of structs instead of a list of dicts.
        """
        # TODO: Change this to return a struct, not a dict
        all_args_for_file = []
        last_call_ended_on_line_number = -1
        latest_chunk = []
        last_call_index = len(self.found_functions) - 1
        for i, fe in enumerate(self.found_functions):
            this_single_call = {
                'type': fe.call_type, 'line_start': fe.starting_line_number,
                'line_end': fe.ending_line_number, 'args': fe.parse_arguments()
            }
            if fe.starting_line_number == last_call_ended_on_line_number + 1:
                latest_chunk.append(this_single_call)
                if i == last_call_index:
                    summary = self.create_function_call_chunk_summary(latest_chunk)
                    all_args_for_file.append({'summary': summary, 'original': latest_chunk})
            else:
                if latest_chunk:
                    summary = self.create_function_call_chunk_summary(latest_chunk)
                    all_args_for_file.append({'summary': summary, 'original': latest_chunk})
                latest_chunk = [this_single_call]  # reset the list starting with the current one
                if i == last_call_index:  # this is the last error, add it to the list before leaving
                    summary = self.create_function_call_chunk_summary(latest_chunk)
                    all_args_for_file.append({'summary': summary, 'original': latest_chunk})
            last_call_ended_on_line_number = fe.ending_line_number
        return all_args_for_file

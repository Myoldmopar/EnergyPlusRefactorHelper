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
        self.function_call_list = function_call_list
        self.original_file_text = self.path.read_text()
        self.file_lines = self.original_file_text.split('\n')
        self.found_functions = self.find_functions_in_original_text()
        self.function_distribution = self.get_function_distribution()
        self.advanced_function_distribution = self.get_advanced_function_distribution()
        self.new_file_text = self.get_file_text_with_functions_replaced()

    @staticmethod
    def get_call_type_and_starting_index_from_raw_line(
            function_call_list: list[str], full_raw_line: str) -> tuple[Optional[int], int]:
        """
        A simple worker function that searches a source line looking for one of the function call strings, and if found,
        returns both the found value along with the index in the line where it was found.

        :param function_call_list: A list of function calls as defined in one of the config classes
        :param full_raw_line: A full line from the rwa source code, to be searched.
        :return: A tuple, where the first item is an optional found error call type int, and the second is the index.
        """
        ect_index = -1
        for ect in function_call_list:
            ect_index += 1
            if ect in full_raw_line:
                return ect_index, full_raw_line.index(ect)
        return None, -1

    def find_functions_in_original_text(self) -> list[FunctionCall]:
        """
        Processes the original source code for this file, identifying all function calls.
        This function fills an array with FunctionCall objects for each function call processed.

        :return: A list of FunctionCall instances, one for each function call processed.
        """
        num_lines_in_file = len(self.file_lines)
        current_line_number = 1
        err: Optional[FunctionCall] = None
        parsing_multiline = False
        raw_line_starting_character_index = 0
        raw_line_ending_character_index = -1
        found_errors = []
        while current_line_number <= num_lines_in_file:
            raw_line = self.file_lines[current_line_number - 1]
            raw_line_ending_character_index += len(raw_line) + 1  # includes the \n at the end of the line
            cleaned_line = raw_line
            if '//' in raw_line:  # danger -- could be inside a string literal
                cleaned_line = raw_line[:cleaned_line.index('//')]
            if parsing_multiline:
                err.add_to_multiline_text(raw_line)
                if len(err.multiline_text) > FunctionCall.MAX_LINES_FOR_SINGLE_CALL:
                    character_end_index = err.char_start_in_file + len(raw_line)
                    err.complete(current_line_number, character_end_index, False)
                    found_errors.append(err)
                    err = None
                    parsing_multiline = False
                elif cleaned_line.strip().endswith(';'):
                    character_end_index = raw_line_starting_character_index + raw_line.rfind(';')
                    err.complete(current_line_number, character_end_index, True)
                    found_errors.append(err)
                    err = None
                    parsing_multiline = False
            else:
                if any([x in cleaned_line for x in self.function_call_list]):
                    call_type, call_index_in_line = self.get_call_type_and_starting_index_from_raw_line(
                        self.function_call_list, raw_line)
                    character_start_index = raw_line_starting_character_index + call_index_in_line
                    err = FunctionCall(
                        call_type, current_line_number, character_start_index, call_index_in_line, raw_line
                    )
                    if cleaned_line.strip().endswith(';'):
                        character_end_index = raw_line_starting_character_index + raw_line.rfind(';')
                        err.complete(current_line_number, character_end_index, True)
                        found_errors.append(err)
                        err = None
                    else:
                        parsing_multiline = True
            raw_line_starting_character_index = raw_line_ending_character_index + 1
            current_line_number += 1
        return found_errors

    def get_function_distribution(self) -> list[int]:
        """
        Returns a distribution of function calls for the given file.  This simply returns a 0 or 1, where
        1 indicates the line is part of a function call, and 0 means it is not.

        :return: An array of integers, one per line of original source code, indicating function call for that line.
        """
        lines_with_functions = []
        for fe in self.found_functions:
            for line_num in range(fe.line_start - 1, fe.line_end):
                if line_num not in lines_with_functions:
                    lines_with_functions.append(line_num)
        all_lines = [1 if x + 1 in lines_with_functions else 0 for x in range(len(self.file_lines))]
        return all_lines

    def get_advanced_function_distribution(self) -> list[int]:
        """
        Returns a distribution of function calls for the given file.  This returns an integer for the function
        call type from the specific function call search config list, from 1 to N, where N is the number of
        function calls being searched.

        :return: An array of integers, one per line of original source code, indicating function call for that line.
        """
        line_values = [0] * len(self.file_lines)
        for fe in self.found_functions:
            for line_num in range(fe.line_start - 1, fe.line_end):
                line_values[line_num] = max(line_values[line_num], fe.call_type)
                return line_values

    def get_file_text_with_functions_replaced(self) -> str:
        """
        Modifies the original file text, replacing every function call with the modified version.

        :return: Returns the modified source code as a Python string.
        """
        new_text = self.original_file_text
        for fe in reversed(self.found_functions):
            new_text = new_text[:fe.char_start_in_file] + fe.as_single_line() + new_text[fe.char_end_in_file + 1:]
        return new_text

    @staticmethod
    def create_function_call_chunk_summary(error_chunk: list[dict]) -> dict:
        num_calls_in_this_chunk = len(error_chunk)
        call_types = [e['type'] for e in error_chunk]
        cleaned_call_types = [i[0] for i in groupby(call_types)]  # remove duplicates
        chunk_start_line = error_chunk[0]['line_start']
        chunk_end_line = error_chunk[-1]['line_end']
        try:
            concatenated_messages = ' *** '.join([e['args'][1] for e in error_chunk])
        except IndexError:  # pragma: no cover
            # this is almost certainly indicative of a parser problem, so we can't cover it
            raise Exception(f"Something went wrong with the arg processing for this chunk! {error_chunk}")
        return {
            'num_calls_in_this_chunk': num_calls_in_this_chunk,
            'call_types': call_types,
            'cleaned_call_types': cleaned_call_types,
            'chunk_start_line': chunk_start_line,
            'chunk_end_line': chunk_end_line,
            'concatenated_messages': concatenated_messages
        }

    def get_call_info_dict(self) -> list[dict]:
        all_args_for_file = []
        last_call_ended_on_line_number = -1
        latest_chunk = []
        last_call_index = len(self.found_functions) - 1
        for i, fe in enumerate(self.found_functions):
            this_single_call = {
                'type': fe.call_type, 'line_start': fe.line_start, 'line_end': fe.line_end, 'args': fe.parse_arguments()
            }
            if fe.line_start == last_call_ended_on_line_number + 1:
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
            last_call_ended_on_line_number = fe.line_end
        return all_args_for_file

    def preview(self) -> str:
        """
        Generates a nice summary of all function calls found in this source file.

        :return: A human-readable string previewing the refactor about to be done.
        """
        ret = ''
        for i, fe in enumerate(self.found_functions):
            ret += f"#{i:04d}: {fe.preview()}\n"
        return ret

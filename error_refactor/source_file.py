from itertools import groupby
from pathlib import Path
from typing import List, Optional, Tuple

from error_refactor.error_call import ErrorCall, ErrorCallStrings


class SourceFile:
    """
    This class represents a single source code file, processing it to find all existing error message calls, and
    providing functionality to refactor them into a new form automatically.
    """

    def __init__(self, path: Path):
        self.path = path
        self.original_file_text = self.path.read_text()
        self.file_lines = self.original_file_text.split('\n')
        self.found_errors = self.find_errors_in_original_text()
        self.error_distribution = self.get_error_distribution()
        self.advanced_error_distribution = self.get_error_distribution(advanced=True)
        self.new_file_text = self.get_file_text_with_errors_replaced()

    @staticmethod
    def get_call_type_and_starting_index_from_raw_line(full_raw_line: str) -> Tuple[Optional[int], int]:
        """
        A simple worker function that searches a source line looking for one of the error message strings, and if found,
        returns both the found value along with the index in the line where it was found.

        :param full_raw_line: A full line from the rwa source code, to be searched.
        :return: A tuple, where the first item is an optional found error call type int, and the second is the index.
        """
        ect_index = -1
        for ect in ErrorCallStrings.all_calls():
            ect_index += 1
            if ect in full_raw_line:
                return ect_index, full_raw_line.index(ect)
        return None, -1

    def find_errors_in_original_text(self) -> List[ErrorCall]:
        """
        Processes the original source code for this file, identifying all error messages.
        This function fills an array with ErrorCall objects for each error message processed.

        :return: A list of ErrorCall instances, one for each error message processed.
        """
        num_lines_in_file = len(self.file_lines)
        current_line_number = 1
        err: Optional[ErrorCall] = None
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
                if len(err.multiline_text) > ErrorCall.MAX_LINES_FOR_ERROR_CALL:
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
                if any([x in cleaned_line for x in ErrorCallStrings.all_calls()]):
                    call_type, call_index_in_line = self.get_call_type_and_starting_index_from_raw_line(raw_line)
                    character_start_index = raw_line_starting_character_index + call_index_in_line
                    err = ErrorCall(call_type, current_line_number, character_start_index, call_index_in_line, raw_line)
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

    def get_error_distribution(self, advanced: bool = False) -> List[int]:
        """
        Returns a distribution of error lines for the given file.  For now, this simply returns a 0 or 1, where
        1 indicates the line is part of an error message, and 0 means it is not.  This will be modified to return more
        meaningful values, such as 1 is a warning, 2 is a severe, 3 is a continue, 4 is a fatal, etc.

        :param advanced: By default, this is false, and the function will only return 0 or 1 in the list, but if this
                         is True, the value will contain integers from the
        :return: An array of integers, one per line of original source code, indicating error status for that line.
        """
        if advanced:
            line_values = [0] * len(self.file_lines)
            for fe in self.found_errors:
                for line_num in range(fe.line_start - 1, fe.line_end):
                    line_values[line_num] = max(line_values[line_num], fe.call_type)
                    return line_values
        lines_with_errors = []
        for fe in self.found_errors:
            for line_num in range(fe.line_start - 1, fe.line_end):
                if line_num not in lines_with_errors:
                    lines_with_errors.append(line_num)
        all_lines = [1 if x + 1 in lines_with_errors else 0 for x in range(len(self.file_lines))]
        return all_lines

    def get_file_text_with_errors_replaced(self) -> str:
        """
        Modifies the original file text, replacing every found error with the modified version.

        :return: Returns the modified source code as a Python string.
        """
        new_text = self.original_file_text
        for fe in reversed(self.found_errors):
            new_text = new_text[:fe.char_start_in_file] + fe.as_single_line() + new_text[fe.char_end_in_file + 1:]
        return new_text

    @staticmethod
    def create_error_chunk_summary(error_chunk: list[dict]) -> dict:
        num_error_calls_in_chunk = len(error_chunk)
        error_call_types = [e['type'] for e in error_chunk]
        cleaned_error_call_types = [i[0] for i in groupby(error_call_types)]  # remove duplicates
        chunk_start_line = error_chunk[0]['line_start']
        chunk_end_line = error_chunk[-1]['line_end']
        try:
            concatenated_messages = ' *** '.join([e['args'][1] for e in error_chunk])
        except IndexError:  # pragma: no cover
            # this is almost certainly indicative of a parser problem, so we can't cover it
            raise Exception(f"Something went wrong with the arg processing for this chunk! {error_chunk}")
        return {
            'num_error_calls_in_chunk': num_error_calls_in_chunk,
            'error_call_types': error_call_types,
            'cleaned_error_call_types': cleaned_error_call_types,
            'chunk_start_line': chunk_start_line,
            'chunk_end_line': chunk_end_line,
            'concatenated_messages': concatenated_messages
        }

    def get_all_error_call_info_dict(self) -> list[dict]:
        all_args_for_file = []
        last_error_ended_on_line_number = -1
        latest_error_chunk = []
        last_error_index = len(self.found_errors) - 1
        for i, fe in enumerate(self.found_errors):
            this_single_error = {
                'type': fe.call_type, 'line_start': fe.line_start, 'line_end': fe.line_end, 'args': fe.parse_arguments()
            }
            if fe.line_start == last_error_ended_on_line_number + 1:
                latest_error_chunk.append(this_single_error)
                if i == last_error_index:
                    summary = self.create_error_chunk_summary(latest_error_chunk)
                    all_args_for_file.append({'summary': summary, 'original': latest_error_chunk})
            else:
                if latest_error_chunk:
                    summary = self.create_error_chunk_summary(latest_error_chunk)
                    all_args_for_file.append({'summary': summary, 'original': latest_error_chunk})
                latest_error_chunk = [this_single_error]  # reset the list starting with the current one
                if i == last_error_index:  # this is the last error, add it to the list before leaving
                    summary = self.create_error_chunk_summary(latest_error_chunk)
                    all_args_for_file.append({'summary': summary, 'original': latest_error_chunk})
            last_error_ended_on_line_number = fe.line_end
        return all_args_for_file

    def preview(self) -> str:
        """
        Generates a nice summary of all errors found in this source file.

        :return: A human-readable string previewing the refactor about to be done.
        """
        ret = ''
        for i, fe in enumerate(self.found_errors):
            ret += f"#{i:04d}: {fe.preview()}\n"
        return ret


if __name__ == "__main__":  # pragma: no cover
    p = Path("/eplus/repos/4eplus/src/EnergyPlus/UnitarySystem.cc")
    sf = SourceFile(p)
    p.write_text(sf.get_file_text_with_errors_replaced())

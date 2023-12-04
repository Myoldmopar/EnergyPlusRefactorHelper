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
        self.new_file_text = self.get_file_text_with_errors_replaced()

    @staticmethod
    def get_call_type_and_starting_index_from_raw_line(full_raw_line: str) -> Tuple[Optional[str], int]:
        """
        A simple worker function that searches a source line looking for one of the error message strings, and if found,
        returns both the found value along with the index in the line where it was found.

        :param full_raw_line: A full line from the rwa source code, to be searched.
        :return: A tuple, where the first item is an optional found error call string, and the second is the index.
        """
        for ect in ErrorCallStrings.all_calls():
            if ect in full_raw_line:
                return ect, full_raw_line.index(ect)
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
            raw_line = self.file_lines[current_line_number-1]
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
                    err = ErrorCall(current_line_number, character_start_index, call_index_in_line, raw_line)
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

    def get_error_distribution(self) -> List[int]:
        """
        Returns a distribution of error lines for the given file.  For now, this simply returns a 0 or 1, where
        1 indicates the line is part of an error message, and 0 means it is not.  This will be modified to return more
        meaningful values, such as 1 is a warning, 2 is a severe, 3 is a continue, 4 is a fatal, etc.

        :return: An array of integers, one per line of original source code, indicating error status for that line.
        """
        lines_with_errors = []
        for fe in self.found_errors:
            for line_num in range(fe.line_start, fe.line_end+1):
                if line_num not in lines_with_errors:  # shouldn't be needed...
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
            new_text = new_text[:fe.char_start_in_file] + fe.modified_version() + new_text[fe.char_end_in_file + 1:]
        return new_text

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

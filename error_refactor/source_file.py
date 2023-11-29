from pathlib import Path
from typing import List, Optional, Tuple

from error_refactor.error_call import ErrorCall, ErrorCallStrings


class SourceFile:
    def __init__(self, path: Path):
        self.path = path
        self.found_errors: List[ErrorCall] = []

    @staticmethod
    def get_call_type_and_starting_index_from_raw_line(full_raw_line: str) -> Tuple[Optional[str], int]:
        for ect in ErrorCallStrings.all_calls():
            if ect in full_raw_line:
                return ect, full_raw_line.index(ect)
        return None, -1

    def process_error_calls_in_file(self):
        file_text = self.path.read_text()
        file_lines = file_text.split('\n')
        num_lines_in_file = len(file_lines)
        current_line_number = 1
        err: Optional[ErrorCall] = None
        parsing_multiline = False
        raw_line_starting_character_index = 0
        raw_line_ending_character_index = -1
        while current_line_number <= num_lines_in_file:
            raw_line = file_lines[current_line_number-1]
            raw_line_ending_character_index += len(raw_line)
            cleaned_line = raw_line
            if '//' in raw_line:  # danger -- could be inside a string literal
                cleaned_line = raw_line[:cleaned_line.index('//')]
            if parsing_multiline:
                err.add_to_multiline_text(raw_line)
                if len(err.multiline_text) > ErrorCall.MAX_LINES_FOR_ERROR_CALL:
                    character_end_index = err.char_start_in_file + len(raw_line)
                    err.complete(current_line_number, character_end_index, False)
                    self.found_errors.append(err)
                    err = None
                    parsing_multiline = False
                elif cleaned_line.strip().endswith(';'):
                    character_end_index = err.char_start_in_file + raw_line.rfind(';')
                    err.complete(current_line_number, character_end_index, True)
                    self.found_errors.append(err)
                    err = None
                    parsing_multiline = False
            else:
                # check if this line has _any_ of the
                if any([x in cleaned_line for x in ErrorCallStrings.all_calls()]):
                    call_type, call_index_in_line = self.get_call_type_and_starting_index_from_raw_line(raw_line)
                    character_start_index = raw_line_starting_character_index + call_index_in_line
                    err = ErrorCall(current_line_number, character_start_index, call_index_in_line, raw_line)
                    if cleaned_line.endswith(';'):
                        character_end_index = err.char_start_in_file + raw_line.rfind(';')
                        err.complete(current_line_number, character_end_index, True)
                        self.found_errors.append(err)
                        err = None
                    else:
                        parsing_multiline = True
            raw_line_starting_character_index = raw_line_ending_character_index + 1
            current_line_number += 1

    def get_summary(self) -> str:
        ret = ''
        for i, fe in enumerate(self.found_errors):
            num = f"#{i:04d}"
            ok = "LOOKS OK" if fe.appears_successful else "PROBLEM"
            lines = f"Lines {fe.line_start:05d}:{fe.line_end:05d}"
            chars = f"Characters {fe.char_start_in_file:08d}:{fe.char_end:08d}"
            one_liner = f"\"{fe.one_line_call()}\""
            arguments = fe.parse_arguments()
            args = f"({len(arguments)}) {arguments}"
            ret += f"{num}: {ok} -- {lines} -- {chars} -- {one_liner} -- {args}\n"
        return ret


if __name__ == "__main__":  # pragma: no cover
    sf = SourceFile(Path("/eplus/repos/1eplus/src/EnergyPlus/UnitarySystem.cc"))
    sf.process_error_calls_in_file()

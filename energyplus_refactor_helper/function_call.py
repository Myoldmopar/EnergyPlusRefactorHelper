from typing import List


class FunctionCall:
    MAX_LINES_FOR_SINGLE_CALL = 13  # to detect/avoid parsing issues

    def __init__(self, call_type: int, line_start: int, char_start_in_file: int, char_start_first_line: int,
                 first_line_raw_text: str):
        self.call_type = call_type
        self.multiline_text = [first_line_raw_text]
        self.line_start = line_start
        self.char_start_in_file = char_start_in_file
        self.char_start_first_line = char_start_first_line
        self.line_end: int = -1
        self.char_end_in_file = -1
        self.appears_successful = True

    def add_to_multiline_text(self, line_content: str) -> None:
        self.multiline_text.append(line_content)

    def complete(self, line_number: int, end_character_index: int, appears_successful: bool) -> None:
        self.line_end = line_number
        self.char_end_in_file = end_character_index
        self.appears_successful = appears_successful

    def as_single_line(self) -> str:
        skip_first_line_to_call_start = []
        for i, t in enumerate(self.multiline_text):
            if i == 0:
                skip_first_line_to_call_start.append(t[self.char_start_first_line:].strip())
            else:
                skip_first_line_to_call_start.append(t.strip())
        return ''.join(skip_first_line_to_call_start).strip()

    def trim_first_line(self) -> list[str]:
        skip_first_line_to_call_start = []
        for i, t in enumerate(self.multiline_text):
            if i == 0:
                skip_first_line_to_call_start.append(t[self.char_start_first_line:].strip())
            else:
                skip_first_line_to_call_start.append(t.strip())
        return [x.strip() for x in skip_first_line_to_call_start]

    def parse_arguments(self) -> List[str]:
        one_string = '\n'.join(self.trim_first_line())
        args = []
        current_arg = ""
        grouping_stack = []
        ignore_next_char = False
        reached_args = False
        about_to_enter_string_literal = False
        reading_comment_until_new_line = False
        for i, c in enumerate(one_string):
            inside_literal = "\"" in grouping_stack or '\'' in grouping_stack
            inside_raw_literal = 'R"(' in grouping_stack
            if not reached_args:  # haven't reached the args yet, just wait for first parenthesis
                if c == '(':
                    grouping_stack.append('(')
                    reached_args = True
                continue
            if reading_comment_until_new_line:
                if c == '\n':
                    reading_comment_until_new_line = False
            elif inside_raw_literal:
                current_arg += c
                if c == '"' and one_string[i-1] == ')':
                    grouping_stack.pop()
            elif inside_literal and c == '\\':
                current_arg += c
                ignore_next_char = True
            elif ignore_next_char:
                current_arg += c
                ignore_next_char = False
            elif c == '\"':
                current_arg += c
                if grouping_stack[-1] == '\"':
                    grouping_stack.pop()
                else:
                    if about_to_enter_string_literal:
                        grouping_stack.append('R"(')
                        about_to_enter_string_literal = False
                    else:
                        grouping_stack.append(c)
            # elif c == '\'':  # no apostrophe for c strings
            #     current_arg += c
            #     if grouping_stack[-1] == '\'':
            #         grouping_stack.pop()
            #     else:
            #         grouping_stack.append(c)
            elif inside_literal:
                current_arg += c
            elif c == '(':
                current_arg += c
                grouping_stack.append(c)
            elif c == ')':
                if grouping_stack[-1] == '(':
                    grouping_stack.pop()
                else:  # pragma: no cover
                    print("UNBALANCED PARENTHESES!")
                    return []  # this really should not happen
                if len(grouping_stack) == 0:  # reached the end
                    args.append(current_arg)
                    break
                current_arg += c
            elif c == ',' and len(grouping_stack) == 1:
                args.append(current_arg)
                current_arg = ''
            else:
                if c == 'R' and one_string[i+1] == '"' and one_string[i+2] == '(':
                    # it appears we are about to enter a raw literal
                    about_to_enter_string_literal = True
                    current_arg += c
                elif c == '/' and one_string[i+1] == '/':
                    reading_comment_until_new_line = True
                elif c == '\n':
                    continue  # just eat the newline
                else:
                    current_arg += c
        return [a.strip() for a in args]

    def preview(self):
        ok = "LOOKS OK" if self.appears_successful else "PROBLEM"
        lines = f"Lines {self.line_start:05d}:{self.line_end:05d}"
        chars = f"Characters {self.char_start_in_file:08d}:{self.char_end_in_file:08d}"
        modified = f"\"{self.as_single_line()}\""
        arguments = self.parse_arguments()
        args = f"({len(arguments)}) {arguments}"
        return f"{ok} -- {lines} -- {chars} -- {modified} -- {args}\n"

    def __str__(self):
        return f"{self.line_start} - {self.line_end} : {self.as_single_line()[:35]}"

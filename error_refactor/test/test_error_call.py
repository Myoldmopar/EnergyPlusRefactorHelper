from pathlib import Path
from tempfile import mkstemp
from unittest import TestCase

from error_refactor.source_file import SourceFile
from error_refactor.error_call import ErrorCall  # , ErrorCallType


class TestErrorCall(TestCase):
    @staticmethod
    def error_call_builder(raw_text: str) -> ErrorCall:
        _, file_path = mkstemp()
        p = Path(file_path)
        p.write_text(raw_text)
        sf = SourceFile(p)
        sf.process_error_calls_in_file()
        return sf.found_errors[0]

    def test_normal_single_line_error_call(self):
        ec = TestErrorCall.error_call_builder("ShowContinueError(state, \"Something happened\", DummyArgument);")
        args = ec.parse_arguments()
        self.assertEqual(3, len(args))

    def test_error_call_with_embedded_quote(self):
        ec = TestErrorCall.error_call_builder('ShowContinueError(state, "Something happened");')
        args = ec.parse_arguments()
        self.assertEqual(2, len(args))

    def test_normal_multiline_error_call(self):
        ec = TestErrorCall.error_call_builder("""ShowContinueError(state,
        format(
            "It might be this: {} or that: {}",
            state.data->Node(1).Temp,
            state.data->CoolVector[x].attributeY
        )
    );        
        """)
        args = ec.parse_arguments()
        self.assertEqual(2, len(args))

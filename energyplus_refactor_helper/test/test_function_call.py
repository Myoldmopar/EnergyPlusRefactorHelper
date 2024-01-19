from pathlib import Path
from tempfile import mkstemp

from energyplus_refactor_helper.action import ErrorCallRefactor
from energyplus_refactor_helper.source_file import SourceFile
from energyplus_refactor_helper.function_call import FunctionCall  # , ErrorCallType

funcs = ErrorCallRefactor().function_calls()  # just create a dummy instance here for convenience


class TestErrorCall:
    @staticmethod
    def error_call_builder(raw_text: str) -> FunctionCall:
        _, file_path = mkstemp()
        p = Path(file_path)
        p.write_text(raw_text)
        sf = SourceFile(p, funcs)
        sf.find_functions_in_original_text()
        return sf.found_functions[0]

    def test_normal_single_line_error_call(self):
        ec = TestErrorCall.error_call_builder("ShowContinueError(state, \"Something happened\", DummyArgument);")
        args = ec.parse_arguments()
        assert len(args) == 3
        assert isinstance(str(ec), str)

    def test_error_call_with_embedded_quote(self):
        ec = TestErrorCall.error_call_builder('ShowContinueError(state, "Something happened");')
        args = ec.parse_arguments()
        assert len(args) == 2

    def test_error_call_with_apostrophe_char_arg(self):
        ec = TestErrorCall.error_call_builder('ShowContinueError(state, \'x\');')
        args = ec.parse_arguments()
        assert len(args) == 2

    def test_error_call_with_complex_escapes(self):
        ec = TestErrorCall.error_call_builder(
            """ShowSevereMessage(state, format("{} \"{}\":",
            DataPlant::PlantEquipTypeNames[static_cast<int>(this->EIRHPType)], this->name));"""
        )
        args = ec.parse_arguments()
        assert len(args) == 2

    def test_normal_multiline_error_call(self):
        ec = TestErrorCall.error_call_builder("""ShowContinueError(state,
        format(
            "It might be this: {} or that: {}, or even that: {}",
            state.data->Node(1).Temp,
            state.data->CoolVector[x].attributeY
        )
    );
        """)
        args = ec.parse_arguments()
        assert len(args) == 2

    def test_another_error_call(self):
        ec = TestErrorCall.error_call_builder("""ShowWarningError( // RecurringWarningErrorAtEnd(
                            state,
                            format("{} \"{}\": HP evaporator DeltaTemp = 0 in mass flow calculation continues...",
                                   DataPlant::PlantEquipTypeNames[static_cast<int>(this->EIRHPType)],
                                   this->name));""")
        args = ec.parse_arguments()
        assert len(args) == 2

    def test_trailing_comment_error_call(self):
        ec = TestErrorCall.error_call_builder("""ShowSevereError(state,
                        "Standard Ratings: Coil:Cooling:DX " + this->name + // TODO: Use dynamic COIL name later
                            " has zero rated total cooling capacity. Standard ratings cannot be calculated.");""")

        args = ec.parse_arguments()
        assert len(args) == 2

    def test_arg_with_apostrophe_char_literal(self):
        ec = TestErrorCall.error_call_builder("""ShowContinueError(s, "(" + c + ')');""")
        args = ec.parse_arguments()
        assert len(args) == 2

    def test_another_weird_apostrophe(self):
        ec = TestErrorCall.error_call_builder("""ShowSevereError(s, "='" + a + "' invalid " + name + "='" + arr);""")
        args = ec.parse_arguments()
        assert len(args) == 2

    def test_more_embedded_apostrophes(self):
        ec = TestErrorCall.error_call_builder("""ShowContinueError(s, "comp='{}', type='{}', key='{}'.");""")
        args = ec.parse_arguments()
        assert len(args) == 2
        assert args[1] == "\"comp='{}', type='{}', key='{}'.\""

    def test_raw_literal_error_call(self):
        ec = TestErrorCall.error_call_builder("""ShowContinueError(state, R"(Extra "Argument" (right) Here)");""")
        args = ec.parse_arguments()
        assert len(args) == 2

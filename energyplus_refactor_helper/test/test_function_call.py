from energyplus_refactor_helper.function_call import FunctionCall


class TestErrorCall:
    @staticmethod
    def helper(full_text: str, function_name: str = "") -> FunctionCall:
        if function_name == "":
            first_open_parenthesis = full_text.find("(")
            function_name = full_text[:first_open_parenthesis]
        f = FunctionCall(0, function_name, 1, 0, 0, full_text)
        f.finalize(len(full_text), True)
        return f

    def test_normal_single_line_error_call(self):
        ec = TestErrorCall.helper("ShowContinueError(state, \"Something happened\", DummyArgument);")
        args = ec.parse_arguments()
        assert len(args) == 3
        assert isinstance(str(ec), str)

    def test_error_call_with_embedded_quote(self):
        ec = TestErrorCall.helper('ShowContinueError(state, "Something happened");')
        args = ec.parse_arguments()
        assert len(args) == 2

    def test_error_call_with_apostrophe_char_arg(self):
        ec = TestErrorCall.helper('ShowContinueError(state, \'x\');')
        args = ec.parse_arguments()
        assert len(args) == 2

    def test_error_call_with_complex_escapes(self):
        ec = TestErrorCall.helper(
            """ShowSevereMessage(state, format("{} \"{}\":",
            DataPlant::PlantEquipTypeNames[static_cast<int>(this->EIRHPType)], this->name));"""
        )
        args = ec.parse_arguments()
        assert len(args) == 2

    def test_normal_multiline_error_call(self):
        ec = TestErrorCall.helper("""ShowContinueError(state,
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
        ec = TestErrorCall.helper("""ShowWarningError( // RecurringWarningErrorAtEnd(
                            state,
                            format("{} \"{}\": HP evaporator DeltaTemp = 0 in mass flow calculation continues...",
                                   DataPlant::PlantEquipTypeNames[static_cast<int>(this->EIRHPType)],
                                   this->name));""")
        args = ec.parse_arguments()
        assert len(args) == 2

    def test_trailing_comment_error_call(self):
        ec = TestErrorCall.helper("""ShowSevereError(state,
                        "Standard Ratings: Coil:Cooling:DX " + this->name + // TODO: Use dynamic COIL name later
                            " has zero rated total cooling capacity. Standard ratings cannot be calculated.");""")

        args = ec.parse_arguments()
        assert len(args) == 2

    def test_arg_with_apostrophe_char_literal(self):
        ec = TestErrorCall.helper("""ShowContinueError(s, "(" + c + ')');""")
        args = ec.parse_arguments()
        assert len(args) == 2

    def test_another_weird_apostrophe(self):
        ec = TestErrorCall.helper("""ShowSevereError(s, "='" + a + "' invalid " + name + "='" + arr);""")
        args = ec.parse_arguments()
        assert len(args) == 2

    def test_more_embedded_apostrophes(self):
        ec = TestErrorCall.helper("""ShowContinueError(s, "comp='{}', type='{}', key='{}'.");""")
        args = ec.parse_arguments()
        assert len(args) == 2
        assert args[1] == "\"comp='{}', type='{}', key='{}'.\""

    def test_raw_literal_error_call(self):
        ec = TestErrorCall.helper("""ShowContinueError(state, R"(Extra "Argument" (right) Here)");""")
        args = ec.parse_arguments()
        assert len(args) == 2

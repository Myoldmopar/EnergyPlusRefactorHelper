from unittest import TestCase

from error_refactor.error_call import ErrorCall, ErrorCallType


class TestErrorCall(TestCase):
    def test_a(self):
        ec = ErrorCall()
        ec.type = ErrorCallType.Severe
        self.assertEqual("1: 1", ec.new_text())

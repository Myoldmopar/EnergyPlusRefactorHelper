from pathlib import Path
from tempfile import mkstemp
from unittest import TestCase

from error_refactor.logger import Logger


class TestLogger(TestCase):

    def test_logger_outputs(self):
        _, log_file_path = mkstemp()
        log_file = Path(log_file_path)
        logger = Logger(log_file=log_file)
        logger.log("Hello")
        log_file_contents = log_file.read_text()
        self.assertTrue("Hello" in log_file_contents)

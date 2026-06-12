import logging
import pytest
from src.core.logger import setup_logging, get_logger


def test_setup_logging_default():
    logger = setup_logging("test_logger", level="DEBUG", debug=True)
    assert logger.level == logging.DEBUG
    assert logger.handlers
    assert logger.name == "test_logger"


def test_get_logger():
    logger = get_logger("test_get")
    assert isinstance(logger, logging.Logger)


def test_logger_file_output(tmp_path):
    log_file = tmp_path / "test.log"
    logger = setup_logging("test_file", log_file=str(log_file), debug=True)
    logger.info("hello test")
    assert log_file.exists()
    content = log_file.read_text()
    assert "hello test" in content

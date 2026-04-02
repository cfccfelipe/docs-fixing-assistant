import logging
import pytest

@pytest.fixture(autouse=True)
def setup_logging():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

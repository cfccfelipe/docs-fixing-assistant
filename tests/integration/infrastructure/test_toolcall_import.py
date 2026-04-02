import pytest
from domain.models.tool_model import ToolCall

def test_toolcall_import():
    assert 'ToolCall' in dir(domain.models.tool_model)

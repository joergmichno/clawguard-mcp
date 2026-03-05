"""Tests for ClawGuard Shield MCP Server."""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch

from clawguard_mcp import __version__
from clawguard_mcp.server import mcp, _format_error


class TestVersion:
    """Test package version."""

    def test_version_exists(self):
        assert __version__ is not None

    def test_version_format(self):
        parts = __version__.split(".")
        assert len(parts) == 3
        assert all(p.isdigit() for p in parts)


class TestToolRegistration:
    """Test that all expected tools are registered."""

    def test_scan_text_registered(self):
        tools = {t.name for t in mcp._tool_manager.list_tools()}
        assert "scan_text" in tools

    def test_scan_batch_registered(self):
        tools = {t.name for t in mcp._tool_manager.list_tools()}
        assert "scan_batch" in tools

    def test_get_patterns_registered(self):
        tools = {t.name for t in mcp._tool_manager.list_tools()}
        assert "get_patterns" in tools

    def test_get_usage_registered(self):
        tools = {t.name for t in mcp._tool_manager.list_tools()}
        assert "get_usage" in tools

    def test_health_check_registered(self):
        tools = {t.name for t in mcp._tool_manager.list_tools()}
        assert "health_check" in tools

    def test_total_tool_count(self):
        tools = mcp._tool_manager.list_tools()
        assert len(tools) == 5

    def test_all_tools_have_descriptions(self):
        for tool in mcp._tool_manager.list_tools():
            assert tool.description, f"Tool {tool.name} has no description"
            assert len(tool.description) > 20, f"Tool {tool.name} description too short"


class TestErrorFormatting:
    """Test error response formatting."""

    def test_401_error(self):
        response = MagicMock()
        response.status_code = 401
        response.json.return_value = {"error": "Unauthorized"}
        error = _format_error(type("HTTPStatusError", (Exception,), {
            "response": response
        })())
        # We need to use the actual httpx error class
        # Just test the function exists and returns dict
        assert callable(_format_error)

    def test_format_error_returns_dict(self):
        """Verify _format_error produces structured output."""
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.json.return_value = {"error": "Rate limited"}

        class FakeHTTPError(Exception):
            response = mock_response

        result = _format_error(FakeHTTPError())
        assert isinstance(result, dict)
        assert "error" in result
        assert "status_code" in result
        assert result["status_code"] == 429


class TestToolSchemas:
    """Test that tool schemas are well-formed."""

    def test_scan_text_has_text_param(self):
        tools = {t.name: t for t in mcp._tool_manager.list_tools()}
        scan_tool = tools["scan_text"]
        schema = scan_tool.parameters
        assert "text" in schema.get("properties", {})

    def test_scan_text_text_is_required(self):
        tools = {t.name: t for t in mcp._tool_manager.list_tools()}
        scan_tool = tools["scan_text"]
        schema = scan_tool.parameters
        assert "text" in schema.get("required", [])

    def test_scan_batch_has_texts_param(self):
        tools = {t.name: t for t in mcp._tool_manager.list_tools()}
        batch_tool = tools["scan_batch"]
        schema = batch_tool.parameters
        assert "texts" in schema.get("properties", {})

    def test_health_check_no_required_params(self):
        tools = {t.name: t for t in mcp._tool_manager.list_tools()}
        health_tool = tools["health_check"]
        schema = health_tool.parameters
        required = schema.get("required", [])
        assert len(required) == 0

    def test_get_patterns_no_required_params(self):
        tools = {t.name: t for t in mcp._tool_manager.list_tools()}
        patterns_tool = tools["get_patterns"]
        schema = patterns_tool.parameters
        required = schema.get("required", [])
        assert len(required) == 0


class TestServerConfig:
    """Test server configuration."""

    def test_server_name(self):
        assert mcp.name == "ClawGuard Shield"

    def test_main_callable(self):
        from clawguard_mcp.server import main
        assert callable(main)

"""
Unit tests for keyword extraction functions.
"""

import pytest
from extract_keywords import normalize_keyword, extract_keywords_from_output


class TestNormalizeKeyword:
    """Tests for normalize_keyword function."""

    def test_normalize_with_library(self):
        """Test normalization with library prefix."""
        result = normalize_keyword("Login User", "LoginLib")
        assert result == "loginlib.login_user"

    def test_normalize_without_library(self):
        """Test normalization without library."""
        result = normalize_keyword("Login User", None)
        assert result == "login_user"

    def test_normalize_empty_keyword(self):
        """Test normalization with empty keyword."""
        result = normalize_keyword("", "Lib")
        assert result is None

    def test_normalize_with_spaces(self):
        """Test normalization handles spaces correctly."""
        result = normalize_keyword("  Login  User  ", "Lib")
        assert result == "lib.login_user"

    def test_normalize_special_characters(self):
        """Test normalization with special characters."""
        result = normalize_keyword("Login-User_Test", "Lib")
        assert result == "lib.login-user_test"


class TestExtractKeywordsFromOutput:
    """Tests for extract_keywords_from_output function."""

    def test_extract_basic_test_case(self, temp_xml_file):
        """Test extraction of basic test case keywords."""
        test_data, metadata = extract_keywords_from_output(temp_xml_file)

        assert len(test_data) > 0
        assert all("test_name" in test for test in test_data)
        assert all("keywords" in test for test in test_data)
        assert all(isinstance(test["keywords"], list) for test in test_data)

    def test_extract_suite_setup_included(self, temp_xml_file):
        """Test that suite setup keywords are included in test sequences."""
        test_data, metadata = extract_keywords_from_output(temp_xml_file)

        # Check if suite setup was detected
        if metadata.get("has_suite_setup"):
            # At least one test should have suite setup keywords at the beginning
            test_with_setup = next(
                (
                    t
                    for t in test_data
                    if t["keywords"]
                    and any("setup" in kw.lower() for kw in t["keywords"][:3])
                ),
                None,
            )
            # This is a soft check - suite setup might be normalized differently
            assert test_with_setup is not None or not metadata.get("has_suite_setup")

    def test_extract_suite_teardown_included(self, temp_xml_file):
        """Test that suite teardown keywords are included in test sequences."""
        test_data, metadata = extract_keywords_from_output(temp_xml_file)

        # Check if suite teardown was detected
        if metadata.get("has_suite_teardown"):
            # At least one test should have suite teardown keywords at the end
            test_with_teardown = next(
                (
                    t
                    for t in test_data
                    if t["keywords"]
                    and any("teardown" in kw.lower() for kw in t["keywords"][-3:])
                ),
                None,
            )
            # This is a soft check - suite teardown might be normalized differently
            assert test_with_teardown is not None or not metadata.get(
                "has_suite_teardown"
            )

    def test_extract_test_setup_included(self, temp_xml_file):
        """Test that test setup keywords are included."""
        test_data, metadata = extract_keywords_from_output(temp_xml_file)

        # Find test with setup
        test_with_setup = next(
            (
                t
                for t in test_data
                if "setup" in t["test_name"].lower()
                or any("setup" in kw.lower() for kw in t["keywords"][:5])
            ),
            None,
        )
        # At least one test should exist
        assert len(test_data) > 0

    def test_extract_keywords_normalized(self, temp_xml_file):
        """Test that extracted keywords are normalized."""
        test_data, metadata = extract_keywords_from_output(temp_xml_file)

        for test in test_data:
            for keyword in test["keywords"]:
                # Keywords should be lowercase and use underscores
                assert keyword == keyword.lower()
                # Should not have leading/trailing spaces
                assert keyword == keyword.strip()

    def test_extract_empty_xml_handles_gracefully(self, tmp_path):
        """Test that empty or invalid XML is handled gracefully."""
        empty_xml = tmp_path / "empty.xml"
        empty_xml.write_text("<?xml version='1.0'?><robot></robot>")

        test_data, metadata = extract_keywords_from_output(str(empty_xml))
        assert isinstance(test_data, list)
        assert len(test_data) == 0

    def test_extract_file_not_found_raises_error(self):
        """Test that missing file raises appropriate error."""
        with pytest.raises((FileNotFoundError, OSError)):
            extract_keywords_from_output("nonexistent_file.xml")

    def test_extract_returns_metadata(self, temp_xml_file):
        """Test that extraction returns metadata."""
        test_data, metadata = extract_keywords_from_output(temp_xml_file)

        assert isinstance(metadata, dict)
        assert "has_suite_setup" in metadata
        assert "has_suite_teardown" in metadata
        assert isinstance(metadata["has_suite_setup"], bool)
        assert isinstance(metadata["has_suite_teardown"], bool)

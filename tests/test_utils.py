"""Tests for ttpa.utils module."""

import pytest

from ttpa.utils import (
    clean_user_name,
    get_file_name_from_url,
    get_profile_url,
    get_tiktok_id_from_url,
    parse_user_names,
)


class TestCleanUserName:
    """Tests for clean_user_name function."""

    def test_strips_whitespace(self) -> None:
        """Test that leading/trailing whitespace is stripped."""
        assert clean_user_name("  testuser  ") == "testuser"

    def test_removes_url_prefix(self) -> None:
        """Test that URL prefix is removed."""
        assert clean_user_name("https://www.tiktok.com/@testuser") == "testuser"

    def test_removes_slash(self) -> None:
        """Test that trailing slash is removed."""
        assert clean_user_name("https://www.tiktok.com/@testuser/") == "testuser"

    def test_removes_at_symbol(self) -> None:
        """Test that leading @ symbol is removed."""
        assert clean_user_name("@testuser") == "testuser"

    def test_converts_to_lowercase(self) -> None:
        """Test that result is converted to lowercase."""
        assert clean_user_name("TestUser") == "testuser"

    def test_handles_full_url_with_path(self) -> None:
        """Test that full URL with path is cleaned."""
        assert clean_user_name("https://www.tiktok.com/@TestUser/video/123456") == "testuser"

    def test_handles_plain_username(self) -> None:
        """Test that plain username is returned as-is (lowercase)."""
        assert clean_user_name("testuser") == "testuser"


class TestParseUserNames:
    """Tests for parse_user_names function."""

    def test_parses_single_username(self) -> None:
        """Test parsing a single username."""
        result = parse_user_names("testuser")
        assert result == ["testuser"]

    def test_parses_multiple_usernames(self) -> None:
        """Test parsing multiple usernames."""
        result = parse_user_names("user1,user2,user3")
        assert result == ["user1", "user2", "user3"]

    def test_removes_duplicates(self) -> None:
        """Test that duplicates are removed while preserving order."""
        result = parse_user_names("user1,user2,user1,user3,user2")
        assert result == ["user1", "user2", "user3"]

    def test_preserves_order(self) -> None:
        """Test that order is preserved after deduplication."""
        result = parse_user_names("b,a,c,b,a")
        assert result == ["b", "a", "c"]

    def test_handles_empty_string(self) -> None:
        """Test that empty string returns empty list."""
        result = parse_user_names("")
        assert result == []

    def test_handles_whitespace_only(self) -> None:
        """Test that whitespace-only string returns empty list."""
        result = parse_user_names("  ,  ,  ")
        assert result == []

    def test_uses_custom_separator(self) -> None:
        """Test that custom separator works."""
        result = parse_user_names("user1;user2;user3", separator=";")
        assert result == ["user1", "user2", "user3"]

    def test_cleaning_is_applied(self) -> None:
        """Test that usernames are cleaned (lowercase, no @)."""
        result = parse_user_names("@User1,@USER2")
        assert result == ["user1", "user2"]


class TestGetProfileUrl:
    """Tests for get_profile_url function."""

    def test_returns_correct_url(self) -> None:
        """Test that correct profile URL is returned."""
        result = get_profile_url("testuser")
        assert result == "https://www.tiktok.com/@testuser"

    def test_handles_lowercase_username(self) -> None:
        """Test that lowercase username is used as-is."""
        result = get_profile_url("testuser")
        assert result == "https://www.tiktok.com/@testuser"

    def test_handles_username_with_numbers(self) -> None:
        """Test that username with numbers is handled correctly."""
        result = get_profile_url("user123")
        assert result == "https://www.tiktok.com/@user123"


class TestGetFileNameFromUrl:
    """Tests for get_file_name_from_url function."""

    def test_extractes_filename_from_url(self) -> None:
        """Test that filename is extracted from URL path."""
        result = get_file_name_from_url("https://example.com/path/to/file.jpg")
        assert result == "file.jpg"

    def test_handles_url_with_query_string(self) -> None:
        """Test that query string is ignored."""
        result = get_file_name_from_url("https://example.com/file.jpg?query=1")
        assert result == "file.jpg"

    def test_handles_url_with_trailing_slash(self) -> None:
        """Test that trailing slash is handled."""
        result = get_file_name_from_url("https://example.com/path/")
        assert result == ""


class TestGetTiktokIdFromUrl:
    """Tests for get_tiktok_id_from_url function."""

    def test_extracts_id_from_video_url(self) -> None:
        """Test that ID is extracted from video URL."""
        result = get_tiktok_id_from_url("https://www.tiktok.com/@user/video/1234567890")
        assert result == "1234567890"

    def test_extracts_id_from_photo_url(self) -> None:
        """Test that ID is extracted from photo URL."""
        result = get_tiktok_id_from_url("https://www.tiktok.com/@user/photo/1234567890")
        assert result == "1234567890"

    def test_returns_none_for_invalid_url(self) -> None:
        """Test that None is returned for invalid URL."""
        result = get_tiktok_id_from_url("https://example.com/not-tiktok")
        assert result is None

    def test_returns_none_for_profile_url(self) -> None:
        """Test that None is returned for profile URL."""
        result = get_tiktok_id_from_url("https://www.tiktok.com/@user")
        assert result is None

    def test_handles_url_with_prefix(self) -> None:
        """Test that URL with prefix is handled."""
        result = get_tiktok_id_from_url("URL: https://www.tiktok.com/@user/video/1234567890")
        assert result == "1234567890"

    def test_handles_case_insensitive(self) -> None:
        """Test that URL matching is case-insensitive."""
        result = get_tiktok_id_from_url("https://www.tiktok.com/@USER/VIDEO/1234567890")
        assert result == "1234567890"

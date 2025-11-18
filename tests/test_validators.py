# tests/test_validators.py
"""Unit tests for backend/utils/validators.py"""

import os
import pytest
from backend.utils.validators import (
    validate_query_parameters,
    sanitize_input,
    ValidationError,
)
from backend.api.models import QueryParameters, RetrievalModel, LLMProvider


@pytest.mark.unit
@pytest.mark.validators
class TestValidateQueryParameters:
    """Tests for validate_query_parameters function"""

    def test_valid_parameters(self, mock_query_parameters):
        """Test validation passes with valid parameters"""
        # Should not raise any exception
        validate_query_parameters(mock_query_parameters)

    def test_empty_query_text_raises_error(self):
        """Test that empty query text raises ValidationError"""
        # Pydantic v2 validates on model creation, so we expect PydanticValidationError
        from pydantic import ValidationError as PydanticValidationError

        with pytest.raises(PydanticValidationError):
            params = QueryParameters(
                query="",
                web_search=True,
                retrieval_model=RetrievalModel.SIGLIP,
                top_k=5,
                max_depth=2,
            )

    def test_whitespace_only_query_raises_error(self):
        """Test that whitespace-only query text raises ValidationError"""
        from pydantic import ValidationError as PydanticValidationError

        with pytest.raises(PydanticValidationError):
            QueryParameters(
                query="   ",
                web_search=True,
                retrieval_model=RetrievalModel.SIGLIP,
                top_k=5,
                max_depth=2,
            )

    def test_query_too_long_raises_error(self):
        """Test that query text over 500 characters raises ValidationError"""
        from pydantic import ValidationError as PydanticValidationError

        long_query = "a" * 501
        with pytest.raises(PydanticValidationError):
            QueryParameters(
                query=long_query,
                web_search=True,
                retrieval_model=RetrievalModel.SIGLIP,
                top_k=5,
                max_depth=2,
            )

    def test_query_exactly_500_chars_is_valid(self):
        """Test that query text of exactly 500 characters is valid"""
        params = QueryParameters(
            query="a" * 500,
            web_search=True,
            retrieval_model=RetrievalModel.SIGLIP,
            top_k=5,
            max_depth=2,
        )

        # Should not raise
        validate_query_parameters(params)

    @pytest.mark.parametrize("top_k", [0, -1, 21, 100])
    def test_invalid_top_k_raises_error(self, top_k):
        """Test that top_k outside range [1, 20] raises ValidationError"""
        from pydantic import ValidationError as PydanticValidationError

        with pytest.raises(PydanticValidationError):
            QueryParameters(
                query="test query",
                web_search=True,
                retrieval_model=RetrievalModel.SIGLIP,
                top_k=top_k,
                max_depth=2,
            )

    @pytest.mark.parametrize("top_k", [1, 5, 10, 20])
    def test_valid_top_k_values(self, top_k):
        """Test that top_k within range [1, 20] is valid"""
        params = QueryParameters(
            query="test query",
            web_search=True,
            retrieval_model=RetrievalModel.SIGLIP,
            top_k=top_k,
            max_depth=2,
        )

        # Should not raise
        validate_query_parameters(params)

    @pytest.mark.parametrize("max_depth", [0, -1, 4, 10])
    def test_invalid_max_depth_raises_error(self, max_depth):
        """Test that max_depth outside range [1, 3] raises ValidationError"""
        from pydantic import ValidationError as PydanticValidationError

        with pytest.raises(PydanticValidationError):
            QueryParameters(
                query="test query",
                web_search=True,
                retrieval_model=RetrievalModel.SIGLIP,
                top_k=5,
                max_depth=max_depth,
            )

    @pytest.mark.parametrize("max_depth", [1, 2, 3])
    def test_valid_max_depth_values(self, max_depth):
        """Test that max_depth within range [1, 3] is valid"""
        params = QueryParameters(
            query="test query",
            web_search=True,
            retrieval_model=RetrievalModel.SIGLIP,
            top_k=5,
            max_depth=max_depth,
        )

        # Should not raise
        validate_query_parameters(params)

    @pytest.mark.parametrize("web_concurrency", [0, -1, 21, 50])
    def test_invalid_web_concurrency_raises_error(self, web_concurrency):
        """Test that web_concurrency outside range [1, 20] raises ValidationError"""
        from pydantic import ValidationError as PydanticValidationError

        with pytest.raises(PydanticValidationError):
            QueryParameters(
                query="test query",
                web_search=True,
                retrieval_model=RetrievalModel.SIGLIP,
                top_k=5,
                max_depth=2,
                web_concurrency=web_concurrency,
            )

    @pytest.mark.parametrize("web_concurrency", [1, 8, 15, 20])
    def test_valid_web_concurrency_values(self, web_concurrency):
        """Test that web_concurrency within range [1, 20] is valid"""
        params = QueryParameters(
            query="test query",
            web_search=True,
            retrieval_model=RetrievalModel.SIGLIP,
            top_k=5,
            max_depth=2,
            web_concurrency=web_concurrency,
        )

        # Should not raise
        validate_query_parameters(params)

    def test_valid_corpus_directory(self, mock_corpus_directory):
        """Test that existing corpus directory passes validation"""
        params = QueryParameters(
            query="test query",
            web_search=True,
            retrieval_model=RetrievalModel.SIGLIP,
            top_k=5,
            max_depth=2,
            corpus_dir=mock_corpus_directory,
        )

        # Should not raise
        validate_query_parameters(params)

    def test_nonexistent_corpus_directory_raises_error(self):
        """Test that non-existent corpus directory raises ValidationError"""
        nonexistent_dir = "/path/to/nonexistent/directory"
        params = QueryParameters(
            query="test query",
            web_search=True,
            retrieval_model=RetrievalModel.SIGLIP,
            top_k=5,
            max_depth=2,
            corpus_dir=nonexistent_dir,
        )

        with pytest.raises(ValidationError, match="Corpus directory does not exist"):
            validate_query_parameters(params)

    def test_none_corpus_directory_is_valid(self):
        """Test that None corpus_dir is valid (optional parameter)"""
        params = QueryParameters(
            query="test query",
            web_search=True,
            retrieval_model=RetrievalModel.SIGLIP,
            top_k=5,
            max_depth=2,
            corpus_dir=None,
        )

        # Should not raise
        validate_query_parameters(params)


@pytest.mark.unit
@pytest.mark.validators
class TestSanitizeInput:
    """Tests for sanitize_input function"""

    def test_clean_input_unchanged(self):
        """Test that clean input text remains unchanged"""
        clean_text = "This is a normal query about quantum physics"
        result = sanitize_input(clean_text)
        assert result == clean_text

    def test_removes_angle_brackets(self):
        """Test that angle brackets are removed"""
        text = "What is <script>alert('xss')</script> quantum computing?"
        result = sanitize_input(text)
        assert "<" not in result
        assert ">" not in result
        assert result == "What is scriptalert('xss')/script quantum computing?"

    def test_removes_curly_braces(self):
        """Test that curly braces are removed"""
        text = "Query with {curly} braces"
        result = sanitize_input(text)
        assert "{" not in result
        assert "}" not in result
        assert result == "Query with curly braces"

    def test_removes_pipe_character(self):
        """Test that pipe character is removed"""
        text = "Query with | pipe"
        result = sanitize_input(text)
        assert "|" not in result
        assert result == "Query with  pipe"

    def test_removes_backslash(self):
        """Test that backslash is removed"""
        text = "Query with \\ backslash"
        result = sanitize_input(text)
        assert "\\" not in result

    def test_removes_caret(self):
        """Test that caret is removed"""
        text = "Query with ^ caret"
        result = sanitize_input(text)
        assert "^" not in result
        assert result == "Query with  caret"

    def test_removes_tilde(self):
        """Test that tilde is removed"""
        text = "Query with ~ tilde"
        result = sanitize_input(text)
        assert "~" not in result
        assert result == "Query with  tilde"

    def test_removes_square_brackets(self):
        """Test that square brackets are removed"""
        text = "Query with [brackets]"
        result = sanitize_input(text)
        assert "[" not in result
        assert "]" not in result
        assert result == "Query with brackets"

    def test_removes_backtick(self):
        """Test that backtick is removed"""
        text = "Query with `backtick`"
        result = sanitize_input(text)
        assert "`" not in result
        assert result == "Query with backtick"

    def test_removes_all_dangerous_chars(self):
        """Test that all dangerous characters are removed"""
        text = "<script>{test}|\\^~[]`"
        result = sanitize_input(text)
        assert result == "scripttest"

    def test_strips_whitespace(self):
        """Test that leading/trailing whitespace is stripped"""
        text = "   query with spaces   "
        result = sanitize_input(text)
        assert result == "query with spaces"

    def test_empty_string(self):
        """Test handling of empty string"""
        result = sanitize_input("")
        assert result == ""

    def test_whitespace_only(self):
        """Test handling of whitespace-only string"""
        result = sanitize_input("   ")
        assert result == ""

    def test_preserves_allowed_special_chars(self):
        """Test that allowed special characters are preserved"""
        text = "What's the cost? $100! #quantum @company.com (2024)"
        result = sanitize_input(text)
        # Should preserve: ' ? $ ! # @ . ( )
        assert "'" in result
        assert "?" in result
        assert "$" in result
        assert "!" in result
        assert "#" in result
        assert "@" in result
        assert "." in result
        assert "(" in result
        assert ")" in result

    def test_unicode_characters_preserved(self):
        """Test that unicode characters are preserved"""
        text = "¿Qué es computación cuántica? 量子计算是什么？"
        result = sanitize_input(text)
        assert "¿" in result
        assert "é" in result
        assert "量" in result

    @pytest.mark.parametrize(
        "input_text,expected",
        [
            ("normal text", "normal text"),
            ("<tag>content</tag>", "tagcontent/tag"),
            ("a{b}c", "abc"),
            ("  trim  ", "trim"),
            ("", ""),
        ],
    )
    def test_various_inputs(self, input_text, expected):
        """Parameterized test for various input scenarios"""
        result = sanitize_input(input_text)
        assert result == expected


@pytest.mark.unit
@pytest.mark.validators
class TestValidationError:
    """Tests for ValidationError exception"""

    def test_validation_error_is_exception(self):
        """Test that ValidationError is an Exception subclass"""
        assert issubclass(ValidationError, Exception)

    def test_validation_error_message(self):
        """Test that ValidationError can be raised with a message"""
        with pytest.raises(ValidationError) as exc_info:
            raise ValidationError("Test error message")

        assert str(exc_info.value) == "Test error message"

    def test_validation_error_can_be_caught(self):
        """Test that ValidationError can be caught and handled"""
        try:
            raise ValidationError("Test error")
        except ValidationError as e:
            assert str(e) == "Test error"

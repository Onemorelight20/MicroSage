# tests/test_export_service.py
"""Unit tests for backend/services/export_service.py"""

import os
import pytest
from backend.services.export_service import ExportService
from backend.api.models import ExportFormat


@pytest.mark.unit
@pytest.mark.services
class TestExportService:
    """Tests for ExportService class"""

    @pytest.fixture
    def export_service(self, temp_dir):
        """Create ExportService instance with temporary directory"""
        export_dir = os.path.join(temp_dir, "exports")
        return ExportService(export_dir=export_dir)

    def test_init_creates_export_directory(self, temp_dir):
        """Test that ExportService creates export directory on init"""
        export_dir = os.path.join(temp_dir, "exports")
        assert not os.path.exists(export_dir)

        service = ExportService(export_dir=export_dir)

        assert os.path.exists(export_dir)
        assert os.path.isdir(export_dir)

    def test_export_markdown(self, export_service, mock_query_result):
        """Test exporting query result to Markdown format"""
        file_path = export_service.export_result(mock_query_result, ExportFormat.MARKDOWN)

        # Check file was created
        assert os.path.exists(file_path)
        assert file_path.endswith(".md")

        # Check file content
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Verify key content is present
        assert "# What is quantum computing?" in content
        assert "test-query-123" in content
        assert "## Query Parameters" in content
        assert "## Result" in content
        assert "## Web Sources" in content
        assert "## Local Sources" in content
        assert "Generated with NanoSage" in content

    def test_export_text(self, export_service, mock_query_result):
        """Test exporting query result to plain text format"""
        file_path = export_service.export_result(mock_query_result, ExportFormat.TEXT)

        # Check file was created
        assert os.path.exists(file_path)
        assert file_path.endswith(".txt")

        # Check file content
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Verify key content is present
        assert "QUERY: What is quantum computing?" in content
        assert "test-query-123" in content
        assert "RESULT" in content
        assert "WEB SOURCES" in content
        assert "LOCAL SOURCES" in content
        assert "Generated with NanoSage" in content

    def test_export_pdf_with_reportlab(self, export_service, mock_query_result):
        """Test exporting query result to PDF format"""
        try:
            file_path = export_service.export_result(mock_query_result, ExportFormat.PDF)

            # Check file was created
            assert os.path.exists(file_path)
            assert file_path.endswith(".pdf")

            # Check file is not empty
            assert os.path.getsize(file_path) > 0

        except ImportError:
            # If reportlab is not installed, test should pass
            pytest.skip("reportlab not installed")

    def test_export_unsupported_format_raises_error(self, export_service, mock_query_result):
        """Test that unsupported export format raises ValueError"""
        with pytest.raises(ValueError, match="Unsupported export format"):
            export_service.export_result(mock_query_result, "unsupported")

    def test_filename_includes_timestamp(self, export_service, mock_query_result):
        """Test that exported filename includes timestamp"""
        file_path = export_service.export_result(mock_query_result, ExportFormat.MARKDOWN)

        filename = os.path.basename(file_path)
        # Filename should include query slug and timestamp
        assert "what_is_quantum_computing" in filename
        assert ".md" in filename
        # Timestamp format: YYYYMMDD_HHMMSS
        assert "_" in filename

    def test_export_creates_unique_filenames(self, export_service, mock_query_result):
        """Test that multiple exports create unique filenames"""
        import time

        file_path1 = export_service.export_result(mock_query_result, ExportFormat.MARKDOWN)
        time.sleep(1)  # Ensure different timestamp
        file_path2 = export_service.export_result(mock_query_result, ExportFormat.MARKDOWN)

        assert file_path1 != file_path2
        assert os.path.exists(file_path1)
        assert os.path.exists(file_path2)


@pytest.mark.unit
@pytest.mark.services
class TestExportServiceHelpers:
    """Tests for ExportService helper methods"""

    @pytest.fixture
    def export_service(self, temp_dir):
        """Create ExportService instance with temporary directory"""
        export_dir = os.path.join(temp_dir, "exports")
        return ExportService(export_dir=export_dir)

    @pytest.mark.parametrize(
        "input_text,expected",
        [
            ("Simple Query", "simple_query"),
            ("What is AI?", "what_is_ai"),
            ("Multiple   Spaces", "multiple_spaces"),
            ("Special-Characters!", "special_characters"),  # Hyphens become underscores
            ("CamelCase Text", "camelcase_text"),
            ("Underscores_Already_Here", "underscores_already_here"),
            ("Query with 123 numbers", "query_with_123_numbers"),
        ],
    )
    def test_slugify(self, export_service, input_text, expected):
        """Test _slugify method converts text to safe filename"""
        result = export_service._slugify(input_text)
        assert result == expected

    def test_slugify_max_length(self, export_service):
        """Test _slugify respects max_length parameter"""
        long_text = "This is a very long query text that should be truncated"
        result = export_service._slugify(long_text, max_length=20)

        assert len(result) <= 20

    def test_slugify_default_max_length(self, export_service):
        """Test _slugify default max_length is 50"""
        long_text = "a" * 100
        result = export_service._slugify(long_text)

        assert len(result) == 50

    @pytest.mark.parametrize(
        "input_text,expected",
        [
            ("# Heading", "Heading"),
            ("## Another Heading", "Another Heading"),
            ("**Bold text**", "Bold text"),
            ("*Italic text*", "Italic text"),
            ("[Link text](url)", "Link text"),
            ("`code`", "code"),
            ("**Bold** and *italic*", "Bold and italic"),
        ],
    )
    def test_strip_markdown(self, export_service, input_text, expected):
        """Test _strip_markdown removes markdown formatting"""
        result = export_service._strip_markdown(input_text)
        assert result == expected

    def test_strip_markdown_code_blocks(self, export_service):
        """Test _strip_markdown removes code blocks"""
        text = "Text before\n```python\ncode here\n```\nText after"
        result = export_service._strip_markdown(text)

        assert "```" not in result
        assert "python" not in result
        assert "code here" not in result

    def test_format_search_tree_single_node(self, export_service):
        """Test _format_search_tree with single node"""
        from backend.api.models import TOCNodeResponse

        node = TOCNodeResponse(
            node_id="node-1",
            query_text="Test Query",
            depth=0,
            summary="Test summary",
            relevance_score=0.95,
        )

        result = export_service._format_search_tree(node)

        assert "**Test Query**" in result
        assert "0.95" in result
        assert "Test summary" in result

    def test_format_search_tree_with_children(self, export_service, mock_toc_node):
        """Test _format_search_tree with nested nodes"""
        result = export_service._format_search_tree(mock_toc_node)

        # Check parent node
        assert "**What is quantum computing?**" in result
        assert "0.95" in result

        # Check child node
        assert "**How do qubits work?**" in result
        assert "0.87" in result

        # Check indentation (child should be indented)
        lines = result.split("\n")
        assert any("  -" in line for line in lines)


@pytest.mark.unit
@pytest.mark.services
class TestExportServiceContent:
    """Tests for exported content formatting"""

    @pytest.fixture
    def export_service(self, temp_dir):
        """Create ExportService instance with temporary directory"""
        export_dir = os.path.join(temp_dir, "exports")
        return ExportService(export_dir=export_dir)

    def test_markdown_export_includes_metadata(self, export_service, mock_query_result):
        """Test that Markdown export includes all metadata"""
        file_path = export_service.export_result(mock_query_result, ExportFormat.MARKDOWN)

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Check metadata
        assert "**Generated:**" in content
        assert "**Query ID:**" in content
        assert "**Processing Time:**" in content
        assert "330000ms" in content

    def test_markdown_export_includes_parameters(self, export_service, mock_query_result):
        """Test that Markdown export includes query parameters"""
        file_path = export_service.export_result(mock_query_result, ExportFormat.MARKDOWN)

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Check parameters section
        assert "## Query Parameters" in content
        assert "**Web Search:**" in content
        assert "**Retrieval Model:**" in content
        assert "**Top K:**" in content
        assert "**Max Depth:**" in content

    def test_markdown_export_web_results_format(self, export_service, mock_query_result):
        """Test that web results are formatted correctly in Markdown"""
        file_path = export_service.export_result(mock_query_result, ExportFormat.MARKDOWN)

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Check web results formatting
        assert "## Web Sources" in content
        assert "Introduction to Quantum Computing" in content
        assert "https://example.com/quantum-intro" in content
        assert "Relevance: 0.92" in content

    def test_markdown_export_local_results_format(self, export_service, mock_query_result):
        """Test that local results are formatted correctly in Markdown"""
        file_path = export_service.export_result(mock_query_result, ExportFormat.MARKDOWN)

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Check local results formatting
        assert "## Local Sources" in content
        assert "quantum_paper.pdf" in content
        assert "This paper discusses quantum algorithms" in content

    def test_text_export_strips_markdown(self, export_service, mock_query_result):
        """Test that text export removes markdown formatting"""
        file_path = export_service.export_result(mock_query_result, ExportFormat.TEXT)

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Markdown should be stripped from final answer
        # Check that we have plain text
        assert "RESULT" in content
        # Headers should be removed
        assert not content.count("#") > 5  # Some # might remain in text

    def test_export_result_without_web_results(self, export_service, mock_query_parameters):
        """Test exporting result without web results"""
        from backend.api.models import QueryResult, QueryStatus

        result = QueryResult(
            query_id="test-no-web",
            status=QueryStatus.COMPLETED,
            query_text="Test query",
            parameters=mock_query_parameters,
            final_answer="Test answer",
            web_results=[],
            local_results=[],
        )

        file_path = export_service.export_result(result, ExportFormat.MARKDOWN)

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Should not have empty web sources section if no results
        assert content.count("## Web Sources") == 0

    def test_export_result_without_local_results(self, export_service, mock_query_parameters):
        """Test exporting result without local results"""
        from backend.api.models import QueryResult, QueryStatus

        result = QueryResult(
            query_id="test-no-local",
            status=QueryStatus.COMPLETED,
            query_text="Test query",
            parameters=mock_query_parameters,
            final_answer="Test answer",
            web_results=[],
            local_results=[],
        )

        file_path = export_service.export_result(result, ExportFormat.MARKDOWN)

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Should not have empty local sources section if no results
        assert content.count("## Local Sources") == 0

    def test_export_result_without_final_answer(self, export_service, mock_query_parameters):
        """Test exporting result without final answer"""
        from backend.api.models import QueryResult, QueryStatus

        result = QueryResult(
            query_id="test-no-answer",
            status=QueryStatus.COMPLETED,
            query_text="Test query",
            parameters=mock_query_parameters,
            final_answer=None,
        )

        file_path = export_service.export_result(result, ExportFormat.MARKDOWN)

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Should not have result section if no final answer
        assert content.count("## Result") == 0

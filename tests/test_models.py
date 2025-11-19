# tests/test_models.py
"""Unit tests for backend/api/models.py"""

import pytest
from pydantic import ValidationError as PydanticValidationError

from backend.api.models import (
    QueryParameters,
    QuerySubmitRequest,
    QuerySubmitResponse,
    QueryStatus,
    QueryResult,
    TOCNodeResponse,
    WebResult,
    LocalResult,
    ExportRequest,
    ExportResponse,
    ExportFormat,
    ProgressUpdate,
    ErrorResponse,
    FileUploadResponse,
    RetrievalModel,
    LLMProvider,
)


@pytest.mark.unit
@pytest.mark.models
class TestEnums:
    """Tests for enum models"""

    def test_retrieval_model_enum_values(self):
        """Test RetrievalModel enum has expected values"""
        assert RetrievalModel.COLPALI.value == "colpali"
        assert RetrievalModel.ALL_MINILM.value == "all-minilm"
        assert RetrievalModel.SIGLIP.value == "siglip"
        assert RetrievalModel.CLIP.value == "clip"

    def test_llm_provider_enum_values(self):
        """Test LLMProvider enum has expected values"""
        assert LLMProvider.OLLAMA.value == "ollama"
        assert LLMProvider.OPENAI.value == "openai"
        assert LLMProvider.ANTHROPIC.value == "anthropic"

    def test_export_format_enum_values(self):
        """Test ExportFormat enum has expected values"""
        assert ExportFormat.MARKDOWN.value == "markdown"
        assert ExportFormat.TEXT.value == "text"
        assert ExportFormat.PDF.value == "pdf"

    def test_query_status_enum_values(self):
        """Test QueryStatus enum has expected values"""
        assert QueryStatus.PENDING.value == "pending"
        assert QueryStatus.PROCESSING.value == "processing"
        assert QueryStatus.COMPLETED.value == "completed"
        assert QueryStatus.FAILED.value == "failed"


@pytest.mark.unit
@pytest.mark.models
class TestQueryParameters:
    """Tests for QueryParameters model"""

    def test_create_with_minimal_required_fields(self):
        """Test creating QueryParameters with only required fields"""
        params = QueryParameters(query="test query")

        assert params.query == "test query"
        assert params.web_search is True
        assert params.retrieval_model == RetrievalModel.SIGLIP
        assert params.top_k == 5
        assert params.max_depth == 1
        assert params.web_concurrency == 8
        assert params.include_wikipedia is False

    def test_create_with_all_fields(self):
        """Test creating QueryParameters with all fields"""
        params = QueryParameters(
            query="quantum computing",
            web_search=False,
            retrieval_model=RetrievalModel.COLPALI,
            top_k=10,
            max_depth=3,
            corpus_dir="/path/to/corpus",
            attached_file_ids=["file1", "file2"],
            personality="scientific",
            rag_model="gpt-4",
            llm_provider=LLMProvider.OPENAI,
            llm_model="gpt-4-turbo",
            web_concurrency=15,
            include_wikipedia=True,
        )

        assert params.query == "quantum computing"
        assert params.web_search is False
        assert params.retrieval_model == RetrievalModel.COLPALI
        assert params.top_k == 10
        assert params.max_depth == 3
        assert params.corpus_dir == "/path/to/corpus"
        assert params.attached_file_ids == ["file1", "file2"]
        assert params.personality == "scientific"
        assert params.rag_model == "gpt-4"
        assert params.llm_provider == LLMProvider.OPENAI
        assert params.llm_model == "gpt-4-turbo"
        assert params.web_concurrency == 15
        assert params.include_wikipedia is True

    def test_query_validation_empty_string(self):
        """Test that empty query string raises ValidationError"""
        # Pydantic v2 validates min_length before custom validators
        with pytest.raises(PydanticValidationError):
            QueryParameters(query="")

    def test_query_validation_whitespace_only(self):
        """Test that whitespace-only query raises ValidationError"""
        with pytest.raises(PydanticValidationError, match="Query cannot be empty"):
            QueryParameters(query="   ")

    def test_query_validation_strips_whitespace(self):
        """Test that query is stripped of leading/trailing whitespace"""
        params = QueryParameters(query="  test query  ")
        assert params.query == "test query"

    def test_query_min_length_validation(self):
        """Test minimum length validation for query"""
        with pytest.raises(PydanticValidationError):
            QueryParameters(query="")

    def test_query_max_length_validation(self):
        """Test maximum length validation for query (500 chars)"""
        with pytest.raises(PydanticValidationError):
            QueryParameters(query="a" * 501)

    def test_top_k_range_validation(self):
        """Test top_k must be between 1 and 20"""
        with pytest.raises(PydanticValidationError):
            QueryParameters(query="test", top_k=0)

        with pytest.raises(PydanticValidationError):
            QueryParameters(query="test", top_k=21)

    def test_max_depth_range_validation(self):
        """Test max_depth must be between 1 and 3"""
        with pytest.raises(PydanticValidationError):
            QueryParameters(query="test", max_depth=0)

        with pytest.raises(PydanticValidationError):
            QueryParameters(query="test", max_depth=4)

    def test_web_concurrency_range_validation(self):
        """Test web_concurrency must be between 1 and 20"""
        with pytest.raises(PydanticValidationError):
            QueryParameters(query="test", web_concurrency=0)

        with pytest.raises(PydanticValidationError):
            QueryParameters(query="test", web_concurrency=21)


@pytest.mark.unit
@pytest.mark.models
class TestQuerySubmitModels:
    """Tests for QuerySubmit request/response models"""

    def test_query_submit_request(self, mock_query_parameters):
        """Test QuerySubmitRequest model"""
        request = QuerySubmitRequest(parameters=mock_query_parameters)
        assert request.parameters == mock_query_parameters

    def test_query_submit_response(self):
        """Test QuerySubmitResponse model"""
        response = QuerySubmitResponse(
            query_id="test-123",
            status="pending",
            message="Query submitted successfully",
        )

        assert response.query_id == "test-123"
        assert response.status == "pending"
        assert response.message == "Query submitted successfully"


@pytest.mark.unit
@pytest.mark.models
class TestTOCNodeResponse:
    """Tests for TOCNodeResponse model"""

    def test_create_simple_node(self):
        """Test creating a simple TOC node without children"""
        node = TOCNodeResponse(
            node_id="node-1",
            query_text="What is AI?",
            depth=0,
            summary="AI is artificial intelligence",
            relevance_score=0.95,
        )

        assert node.node_id == "node-1"
        assert node.query_text == "What is AI?"
        assert node.depth == 0
        assert node.summary == "AI is artificial intelligence"
        assert node.relevance_score == 0.95
        assert node.children == []
        assert node.metrics is None

    def test_create_node_with_children(self):
        """Test creating a TOC node with children"""
        child = TOCNodeResponse(
            node_id="node-2",
            query_text="How does AI work?",
            depth=1,
            summary="AI uses algorithms",
            relevance_score=0.88,
        )

        parent = TOCNodeResponse(
            node_id="node-1",
            query_text="What is AI?",
            depth=0,
            summary="AI is artificial intelligence",
            relevance_score=0.95,
            children=[child],
        )

        assert len(parent.children) == 1
        assert parent.children[0] == child
        assert parent.children[0].depth == 1

    def test_create_node_with_metrics(self):
        """Test creating a TOC node with metrics"""
        node = TOCNodeResponse(
            node_id="node-1",
            query_text="What is AI?",
            depth=0,
            summary="AI is artificial intelligence",
            relevance_score=0.95,
            metrics={"processing_time_ms": 1500, "tokens_used": 250},
        )

        assert node.metrics == {"processing_time_ms": 1500, "tokens_used": 250}

    def test_node_id_optional(self):
        """Test that node_id is optional"""
        node = TOCNodeResponse(
            node_id=None,
            query_text="What is AI?",
            depth=0,
            summary="AI summary",
            relevance_score=0.9,
        )

        assert node.node_id is None


@pytest.mark.unit
@pytest.mark.models
class TestWebResult:
    """Tests for WebResult model"""

    def test_create_web_result_with_all_fields(self):
        """Test creating WebResult with all fields"""
        result = WebResult(
            title="Test Article",
            url="https://example.com/article",
            snippet="This is a test article snippet",
            relevance=0.92,
        )

        assert result.title == "Test Article"
        assert result.url == "https://example.com/article"
        assert result.snippet == "This is a test article snippet"
        assert result.relevance == 0.92

    def test_create_web_result_without_relevance(self):
        """Test creating WebResult without relevance (optional)"""
        result = WebResult(
            title="Test Article",
            url="https://example.com/article",
            snippet="This is a test article snippet",
        )

        assert result.relevance is None


@pytest.mark.unit
@pytest.mark.models
class TestLocalResult:
    """Tests for LocalResult model"""

    def test_create_local_result_with_all_fields(self):
        """Test creating LocalResult with all fields"""
        result = LocalResult(
            source="document.pdf",
            snippet="This is a snippet from the document",
            relevance=0.85,
        )

        assert result.source == "document.pdf"
        assert result.snippet == "This is a snippet from the document"
        assert result.relevance == 0.85

    def test_create_local_result_without_relevance(self):
        """Test creating LocalResult without relevance (optional)"""
        result = LocalResult(
            source="document.pdf",
            snippet="This is a snippet from the document",
        )

        assert result.relevance is None


@pytest.mark.unit
@pytest.mark.models
class TestQueryResult:
    """Tests for QueryResult model"""

    def test_create_minimal_query_result(self, mock_query_parameters):
        """Test creating QueryResult with minimal fields"""
        result = QueryResult(
            query_id="test-123",
            status=QueryStatus.PENDING,
            query_text="What is AI?",
            parameters=mock_query_parameters,
        )

        assert result.query_id == "test-123"
        assert result.status == QueryStatus.PENDING
        assert result.query_text == "What is AI?"
        assert result.parameters == mock_query_parameters
        assert result.final_answer is None
        assert result.search_tree is None
        assert result.web_results == []
        assert result.local_results == []
        assert result.error_message is None

    def test_create_complete_query_result(self, mock_query_result):
        """Test creating QueryResult with all fields"""
        assert mock_query_result.query_id == "test-query-123"
        assert mock_query_result.status == QueryStatus.COMPLETED
        assert mock_query_result.final_answer is not None
        assert mock_query_result.search_tree is not None
        assert len(mock_query_result.web_results) == 2
        assert len(mock_query_result.local_results) == 2
        assert mock_query_result.processing_time_ms == 330000

    def test_query_result_with_error(self, mock_query_parameters):
        """Test creating QueryResult with error status"""
        result = QueryResult(
            query_id="test-123",
            status=QueryStatus.FAILED,
            query_text="What is AI?",
            parameters=mock_query_parameters,
            error_message="LLM API connection failed",
        )

        assert result.status == QueryStatus.FAILED
        assert result.error_message == "LLM API connection failed"


@pytest.mark.unit
@pytest.mark.models
class TestExportModels:
    """Tests for Export request/response models"""

    def test_export_request(self):
        """Test ExportRequest model"""
        request = ExportRequest(query_id="test-123", format=ExportFormat.MARKDOWN)

        assert request.query_id == "test-123"
        assert request.format == ExportFormat.MARKDOWN

    def test_export_response(self):
        """Test ExportResponse model"""
        response = ExportResponse(
            download_url="/exports/test-query_20250118_120000.md",
            filename="test-query_20250118_120000.md",
            format=ExportFormat.MARKDOWN,
        )

        assert response.download_url == "/exports/test-query_20250118_120000.md"
        assert response.filename == "test-query_20250118_120000.md"
        assert response.format == ExportFormat.MARKDOWN


@pytest.mark.unit
@pytest.mark.models
class TestProgressUpdate:
    """Tests for ProgressUpdate model"""

    def test_create_progress_update_with_all_fields(self):
        """Test creating ProgressUpdate with all fields"""
        update = ProgressUpdate(
            query_id="test-123",
            status=QueryStatus.PROCESSING,
            message="Building knowledge base...",
            progress_percentage=45,
            current_step="knowledge_base",
            total_steps=10,
            completed_steps=4,
            timestamp="2025-01-18T10:05:00Z",
        )

        assert update.query_id == "test-123"
        assert update.status == QueryStatus.PROCESSING
        assert update.message == "Building knowledge base..."
        assert update.progress_percentage == 45
        assert update.current_step == "knowledge_base"
        assert update.total_steps == 10
        assert update.completed_steps == 4

    def test_create_progress_update_with_minimal_fields(self):
        """Test creating ProgressUpdate with minimal fields"""
        update = ProgressUpdate(
            query_id="test-123",
            status=QueryStatus.PROCESSING,
            message="Processing query...",
            timestamp="2025-01-18T10:05:00Z",
        )

        assert update.progress_percentage is None
        assert update.current_step is None
        assert update.total_steps is None
        assert update.completed_steps is None


@pytest.mark.unit
@pytest.mark.models
class TestErrorResponse:
    """Tests for ErrorResponse model"""

    def test_create_error_response_with_detail(self):
        """Test creating ErrorResponse with detail"""
        error = ErrorResponse(
            error="Validation Error",
            detail="Query text cannot be empty",
            status_code=400,
        )

        assert error.error == "Validation Error"
        assert error.detail == "Query text cannot be empty"
        assert error.status_code == 400

    def test_create_error_response_without_detail(self):
        """Test creating ErrorResponse without detail"""
        error = ErrorResponse(error="Internal Server Error", status_code=500)

        assert error.error == "Internal Server Error"
        assert error.detail is None
        assert error.status_code == 500


@pytest.mark.unit
@pytest.mark.models
class TestFileUploadResponse:
    """Tests for FileUploadResponse model"""

    def test_create_file_upload_response(self):
        """Test creating FileUploadResponse"""
        response = FileUploadResponse(
            file_id="file-abc-123",
            filename="document.pdf",
            file_type="application/pdf",
            file_size=1024000,
            message="File uploaded successfully",
        )

        assert response.file_id == "file-abc-123"
        assert response.filename == "document.pdf"
        assert response.file_type == "application/pdf"
        assert response.file_size == 1024000
        assert response.message == "File uploaded successfully"


@pytest.mark.unit
@pytest.mark.models
class TestModelSerialization:
    """Tests for model serialization/deserialization"""

    def test_query_parameters_to_dict(self, mock_query_parameters):
        """Test serializing QueryParameters to dict"""
        data = mock_query_parameters.model_dump()

        assert data["query"] == "What is quantum computing?"
        assert data["web_search"] is True
        assert data["retrieval_model"] == "siglip"
        assert data["top_k"] == 5

    def test_query_result_to_dict(self, mock_query_result):
        """Test serializing QueryResult to dict"""
        data = mock_query_result.model_dump()

        assert data["query_id"] == "test-query-123"
        assert data["status"] == "completed"
        assert len(data["web_results"]) == 2
        assert len(data["local_results"]) == 2

    def test_query_parameters_from_dict(self):
        """Test deserializing QueryParameters from dict"""
        data = {
            "query": "test query",
            "web_search": True,
            "retrieval_model": "siglip",
            "top_k": 5,
            "max_depth": 2,
            "web_concurrency": 8,
            "include_wikipedia": False,
        }

        params = QueryParameters(**data)
        assert params.query == "test query"
        assert params.retrieval_model == RetrievalModel.SIGLIP

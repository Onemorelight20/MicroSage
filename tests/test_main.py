# tests/test_main.py
"""Unit tests for backend/api/main.py"""

import os
import json
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from backend.api.main import app
from backend.api.models import (
    QueryParameters,
    QueryResult,
    QueryStatus,
    RetrievalModel,
    LLMProvider,
    ExportFormat,
)


@pytest.fixture
def client():
    """Create a test client"""
    return TestClient(app)


@pytest.mark.unit
@pytest.mark.api
class TestRootEndpoint:
    """Tests for root endpoint"""

    def test_root_returns_api_info(self, client):
        """Test that root endpoint returns API information"""
        response = client.get("/")
        assert response.status_code == 200

        data = response.json()
        assert data["message"] == "NanoSage API"
        assert data["version"] == "1.0.0"
        assert "endpoints" in data

    def test_root_contains_endpoint_info(self, client):
        """Test that root endpoint contains endpoint information"""
        response = client.get("/")
        data = response.json()

        endpoints = data["endpoints"]
        assert "submit_query" in endpoints
        assert "get_query" in endpoints
        assert "list_queries" in endpoints
        assert "export" in endpoints
        assert "upload_file" in endpoints
        assert "websocket" in endpoints


@pytest.mark.unit
@pytest.mark.api
class TestHealthCheck:
    """Tests for health check endpoint"""

    def test_health_check_returns_healthy(self, client):
        """Test that health check returns healthy status"""
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data

    def test_health_check_timestamp_format(self, client):
        """Test that health check returns valid timestamp"""
        response = client.get("/health")
        data = response.json()

        # Should be ISO format timestamp
        timestamp = data["timestamp"]
        assert "T" in timestamp
        assert len(timestamp) > 0


@pytest.mark.unit
@pytest.mark.api
class TestUploadFile:
    """Tests for file upload endpoint"""

    @patch('backend.api.main.file_upload_service')
    def test_upload_file_success(self, mock_service, client):
        """Test successful file upload"""
        # Mock upload_file response
        mock_service.upload_file = AsyncMock(return_value={
            'file_id': 'test-file-123',
            'original_filename': 'test.pdf',
            'file_type': 'pdf',
            'file_size': 1024
        })

        # Create test file
        test_file = ("test.pdf", b"fake pdf content", "application/pdf")

        response = client.post("/api/files/upload", files={"file": test_file})
        assert response.status_code == 200

        data = response.json()
        assert data["file_id"] == "test-file-123"
        assert data["filename"] == "test.pdf"
        assert data["file_type"] == "pdf"
        assert data["file_size"] == 1024
        assert "uploaded successfully" in data["message"]

    @patch('backend.api.main.file_upload_service')
    def test_upload_file_invalid_type(self, mock_service, client):
        """Test upload with invalid file type"""
        # Mock to raise ValueError
        mock_service.upload_file = AsyncMock(side_effect=ValueError("Invalid file type"))

        test_file = ("test.exe", b"fake exe content", "application/x-msdownload")

        response = client.post("/api/files/upload", files={"file": test_file})
        assert response.status_code == 400
        assert "Invalid file type" in response.json()["error"]

    @patch('backend.api.main.file_upload_service')
    def test_upload_file_server_error(self, mock_service, client):
        """Test upload with server error"""
        mock_service.upload_file = AsyncMock(side_effect=Exception("Server error"))

        test_file = ("test.pdf", b"fake pdf content", "application/pdf")

        response = client.post("/api/files/upload", files={"file": test_file})
        assert response.status_code == 500
        assert "File upload failed" in response.json()["error"]


@pytest.mark.unit
@pytest.mark.api
class TestSubmitQuery:
    """Tests for submit query endpoint"""

    @patch('backend.api.main.query_service')
    def test_submit_query_success(self, mock_service, client):
        """Test successful query submission"""
        mock_service.submit_query = AsyncMock(return_value="query-123")

        request_data = {
            "parameters": {
                "query": "What is quantum computing?",
                "web_search": True,
                "retrieval_model": "siglip",
                "top_k": 5,
                "max_depth": 2,
                "web_concurrency": 8,
                "include_wikipedia": False,
                "personality": "Researcher",
                "rag_model": "gemma",
                "llm_provider": "ollama",
                "llm_model": "gemma2:2b"
            }
        }

        response = client.post("/api/query/submit", json=request_data)
        assert response.status_code == 200

        data = response.json()
        assert data["query_id"] == "query-123"
        assert data["status"] == "accepted"
        assert "submitted successfully" in data["message"]

    def test_submit_query_invalid_parameters(self, client):
        """Test submit with invalid parameters"""
        request_data = {
            "parameters": {
                "query": "",  # Empty query
                "web_search": True,
                "retrieval_model": "siglip",
                "top_k": 5,
                "max_depth": 2
            }
        }

        response = client.post("/api/query/submit", json=request_data)
        assert response.status_code == 422  # Pydantic validation error

    @patch('backend.api.main.query_service')
    @patch('backend.api.main.validate_query_parameters')
    def test_submit_query_validation_error(self, mock_validate, mock_service, client):
        """Test submit with validation error"""
        from backend.utils.validators import ValidationError
        mock_validate.side_effect = ValidationError("Invalid corpus directory")

        request_data = {
            "parameters": {
                "query": "Test query",
                "web_search": True,
                "retrieval_model": "siglip",
                "top_k": 5,
                "max_depth": 2,
                "corpus_dir": "/invalid/path"
            }
        }

        response = client.post("/api/query/submit", json=request_data)
        assert response.status_code == 400
        assert "Invalid corpus directory" in response.json()["error"]


@pytest.mark.unit
@pytest.mark.api
class TestGetQuery:
    """Tests for get query endpoint"""

    @patch('backend.api.main.query_service')
    def test_get_query_success(self, mock_service, client, mock_query_result):
        """Test successful query retrieval"""
        mock_service.get_query_status = Mock(return_value=mock_query_result)

        response = client.get("/api/query/test-query-123")
        assert response.status_code == 200

        data = response.json()
        assert data["query_id"] == "test-query-123"
        assert data["status"] == "completed"

    @patch('backend.api.main.query_service')
    def test_get_query_not_found(self, mock_service, client):
        """Test get query that doesn't exist"""
        mock_service.get_query_status = Mock(return_value=None)

        response = client.get("/api/query/nonexistent-id")
        assert response.status_code == 404
        assert "Query not found" in response.json()["error"]


@pytest.mark.unit
@pytest.mark.api
class TestListQueries:
    """Tests for list queries endpoint"""

    @patch('backend.api.main.query_service')
    def test_list_queries_default_limit(self, mock_service, client):
        """Test list queries with default limit"""
        mock_service.list_queries = Mock(return_value=[])

        response = client.get("/api/queries")
        assert response.status_code == 200
        assert response.json() == []

        # Check called with default limit
        mock_service.list_queries.assert_called_once_with(limit=50)

    @patch('backend.api.main.query_service')
    def test_list_queries_custom_limit(self, mock_service, client):
        """Test list queries with custom limit"""
        mock_service.list_queries = Mock(return_value=[])

        response = client.get("/api/queries?limit=10")
        assert response.status_code == 200

        mock_service.list_queries.assert_called_once_with(limit=10)

    def test_list_queries_invalid_limit_too_low(self, client):
        """Test list queries with limit too low"""
        response = client.get("/api/queries?limit=0")
        assert response.status_code == 400
        assert "between 1 and 100" in response.json()["error"]

    def test_list_queries_invalid_limit_too_high(self, client):
        """Test list queries with limit too high"""
        response = client.get("/api/queries?limit=101")
        assert response.status_code == 400
        assert "between 1 and 100" in response.json()["error"]


@pytest.mark.unit
@pytest.mark.api
class TestExportQuery:
    """Tests for export query endpoint"""

    @patch('backend.api.main.export_service')
    @patch('backend.api.main.history_service')
    @patch('backend.api.main.query_service')
    def test_export_query_success(self, mock_query_service, mock_history_service, mock_export_service, client, mock_query_result):
        """Test successful query export"""
        mock_query_service.get_query_status = Mock(return_value=mock_query_result)
        mock_export_service.export_result = Mock(return_value="exports/test-query-123.md")
        mock_history_service.add_query = Mock()

        request_data = {
            "query_id": "test-query-123",
            "format": "markdown"
        }

        response = client.post("/api/query/export", json=request_data)
        assert response.status_code == 200

        data = response.json()
        assert data["filename"] == "test-query-123.md"
        assert data["format"] == "markdown"
        assert "/exports/" in data["download_url"]

    @patch('backend.api.main.query_service')
    def test_export_query_not_found(self, mock_query_service, client):
        """Test export query that doesn't exist"""
        mock_query_service.get_query_status = Mock(return_value=None)

        request_data = {
            "query_id": "nonexistent-id",
            "format": "markdown"
        }

        response = client.post("/api/query/export", json=request_data)
        assert response.status_code == 404
        assert "Query not found" in response.json()["error"]

    @patch('backend.api.main.query_service')
    def test_export_query_not_completed(self, mock_query_service, client, mock_query_result):
        """Test export query that is not completed"""
        mock_query_result.status = QueryStatus.PROCESSING
        mock_query_service.get_query_status = Mock(return_value=mock_query_result)

        request_data = {
            "query_id": "test-query-123",
            "format": "markdown"
        }

        response = client.post("/api/query/export", json=request_data)
        assert response.status_code == 400
        assert "must be completed" in response.json()["error"]


@pytest.mark.unit
@pytest.mark.api
class TestDownloadExport:
    """Tests for download export endpoint"""

    def test_download_export_success(self, client, temp_dir):
        """Test successful file download"""
        # Create a test export file
        exports_dir = "exports"
        os.makedirs(exports_dir, exist_ok=True)

        test_file = os.path.join(exports_dir, "test-export.md")
        with open(test_file, "w") as f:
            f.write("# Test Export\n\nThis is a test export.")

        try:
            response = client.get("/api/query/export/download/test-export.md")
            assert response.status_code == 200
            assert response.headers["content-type"] == "application/octet-stream"
        finally:
            # Cleanup
            if os.path.exists(test_file):
                os.remove(test_file)

    def test_download_export_not_found(self, client):
        """Test download non-existent file"""
        response = client.get("/api/query/export/download/nonexistent.md")
        assert response.status_code == 404
        assert "File not found" in response.json()["error"]


@pytest.mark.unit
@pytest.mark.api
class TestHistoryEndpoints:
    """Tests for history endpoints"""

    @patch('backend.api.main.history_service')
    def test_get_history(self, mock_service, client):
        """Test get history endpoint"""
        mock_service.list_queries = Mock(return_value=[])

        response = client.get("/api/history")
        assert response.status_code == 200
        assert response.json() == []

        mock_service.list_queries.assert_called_once_with(limit=10)

    @patch('backend.api.main.history_service')
    def test_get_history_custom_limit(self, mock_service, client):
        """Test get history with custom limit"""
        mock_service.list_queries = Mock(return_value=[])

        response = client.get("/api/history?limit=5")
        assert response.status_code == 200

        mock_service.list_queries.assert_called_once_with(limit=5)

    def test_get_history_invalid_limit(self, client):
        """Test get history with invalid limit"""
        response = client.get("/api/history?limit=100")
        assert response.status_code == 400
        assert "between 1 and 50" in response.json()["error"]

    @patch('backend.api.main.history_service')
    def test_get_history_stats(self, mock_service, client):
        """Test get history stats endpoint"""
        mock_service.get_stats = Mock(return_value={
            "total_queries": 10,
            "completed": 8,
            "failed": 2
        })

        response = client.get("/api/history/stats")
        assert response.status_code == 200

        data = response.json()
        assert data["total_queries"] == 10
        assert data["completed"] == 8
        assert data["failed"] == 2

    @patch('backend.api.main.history_service')
    def test_sync_history(self, mock_service, client):
        """Test sync history endpoint"""
        mock_service.sync_from_results_folder = Mock()
        mock_service.get_stats = Mock(return_value={"total_queries": 5})

        response = client.post("/api/history/sync")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "synced successfully" in data["message"]
        assert "stats" in data

    @patch('backend.api.main.history_service')
    def test_get_history_query(self, mock_service, client, mock_query_result):
        """Test get specific query from history"""
        mock_service.get_query = Mock(return_value=mock_query_result)

        response = client.get("/api/history/test-query-123")
        assert response.status_code == 200

        data = response.json()
        assert data["query_id"] == "test-query-123"

    @patch('backend.api.main.history_service')
    def test_get_history_query_not_found(self, mock_service, client):
        """Test get non-existent query from history"""
        mock_service.get_query = Mock(return_value=None)

        response = client.get("/api/history/nonexistent-id")
        assert response.status_code == 404
        assert "not found in history" in response.json()["error"]

    @patch('backend.api.main.history_service')
    def test_delete_history_query(self, mock_service, client):
        """Test delete query from history"""
        mock_service.delete_query = Mock(return_value=True)

        response = client.delete("/api/history/test-query-123")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "deleted successfully" in data["message"]

    @patch('backend.api.main.history_service')
    def test_delete_history_query_not_found(self, mock_service, client):
        """Test delete non-existent query from history"""
        mock_service.delete_query = Mock(return_value=False)

        response = client.delete("/api/history/nonexistent-id")
        assert response.status_code == 404
        assert "not found in history" in response.json()["error"]

    @patch('backend.api.main.history_service')
    def test_clear_history(self, mock_service, client):
        """Test clear all history"""
        mock_service.clear_all = Mock()

        response = client.delete("/api/history")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "cleared successfully" in data["message"]


@pytest.mark.unit
@pytest.mark.api
class TestHTTPExceptionHandler:
    """Tests for HTTP exception handler"""

    def test_http_exception_handler_format(self, client):
        """Test that HTTP exceptions are properly formatted"""
        # Trigger a 404 error
        response = client.get("/api/query/nonexistent-id")

        assert response.status_code == 404
        data = response.json()
        assert "error" in data
        assert "status_code" in data
        assert data["status_code"] == 404

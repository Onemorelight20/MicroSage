# tests/test_query_service.py
"""Unit tests for backend/services/query_service.py"""

import os
import json
import pytest
import asyncio
import yaml
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from backend.services.query_service import QueryService
from backend.api.models import (
    QueryParameters,
    QueryResult,
    QueryStatus,
    RetrievalModel,
    LLMProvider,
    TOCNodeResponse,
    WebResult,
    LocalResult
)


@pytest.mark.unit
@pytest.mark.services
class TestQueryServiceInit:
    """Tests for QueryService initialization"""

    def test_init_with_default_config(self):
        """Test initialization with default config path"""
        with patch('backend.services.query_service.QueryService._load_config') as mock_load:
            mock_load.return_value = {}
            service = QueryService()

            assert service.config_path == "config.yaml"
            assert service.active_queries == {}
            assert service.completed_queries == {}

    def test_init_loads_config(self, temp_dir):
        """Test that initialization loads config file"""
        config_path = os.path.join(temp_dir, "test_config.yaml")
        config_data = {
            "web_concurrency": 5,
            "include_wikipedia": True
        }

        with open(config_path, "w") as f:
            yaml.dump(config_data, f)

        service = QueryService(config_path=config_path)

        assert service.config["web_concurrency"] == 5
        assert service.config["include_wikipedia"] is True

    def test_load_config_missing_file(self):
        """Test loading config when file doesn't exist"""
        service = QueryService(config_path="nonexistent.yaml")
        assert service.config == {}


@pytest.mark.unit
@pytest.mark.services
class TestQueryServiceSubmitQuery:
    """Tests for submit_query method"""

    @pytest.fixture
    def service(self):
        """Create QueryService instance"""
        with patch('backend.services.query_service.QueryService._load_config'):
            return QueryService()

    @pytest.mark.asyncio
    async def test_submit_query_returns_query_id(self, service, mock_query_parameters):
        """Test that submit_query returns a query ID"""
        with patch.object(service, '_process_query', return_value=None):
            query_id = await service.submit_query(mock_query_parameters)

            assert query_id is not None
            assert isinstance(query_id, str)
            assert len(query_id) > 0

    @pytest.mark.asyncio
    async def test_submit_query_stores_in_active(self, service, mock_query_parameters):
        """Test that submit_query stores query in active_queries"""
        with patch.object(service, '_process_query', return_value=None):
            query_id = await service.submit_query(mock_query_parameters)

            assert query_id in service.active_queries
            assert service.active_queries[query_id]['status'] == QueryStatus.PENDING
            assert service.active_queries[query_id]['parameters'] == mock_query_parameters

    @pytest.mark.asyncio
    async def test_submit_query_with_callback(self, service, mock_query_parameters):
        """Test submit_query with progress callback"""
        callback = AsyncMock()

        with patch.object(service, '_process_query', return_value=None):
            query_id = await service.submit_query(mock_query_parameters, callback)

            assert service.active_queries[query_id]['progress_callback'] == callback


@pytest.mark.unit
@pytest.mark.services
class TestQueryServiceProcessQuery:
    """Tests for _process_query method"""

    @pytest.fixture
    def service(self):
        """Create QueryService instance"""
        with patch('backend.services.query_service.QueryService._load_config'):
            return QueryService()

    @pytest.mark.asyncio
    async def test_process_query_success(self, service, mock_query_parameters):
        """Test successful query processing"""
        query_id = "test-query-123"
        service.active_queries[query_id] = {
            'parameters': mock_query_parameters,
            'status': QueryStatus.PENDING,
            'created_at': '2025-01-18T10:00:00Z',
            'progress_callback': None,
            'log_handler': None
        }

        # Mock SearchSession
        mock_session = MagicMock()
        mock_session.run_session = AsyncMock(return_value="# Final Answer\n\nTest answer")
        mock_session.save_report = Mock(return_value="results/test-query-123/report.md")
        mock_session.toc_tree = []
        mock_session.kb = None

        with patch('backend.services.query_service.SearchSession', return_value=mock_session):
            with patch('backend.services.query_service.setup_log_streaming', return_value=None):
                with patch('backend.services.query_service.cleanup_log_streaming'):
                    await service._process_query(query_id, mock_query_parameters)

        # Query should be completed and moved to completed_queries
        assert query_id in service.completed_queries
        assert query_id not in service.active_queries
        assert service.completed_queries[query_id].status == QueryStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_process_query_with_callback(self, service, mock_query_parameters):
        """Test query processing with progress callback"""
        query_id = "test-query-123"
        callback = AsyncMock()

        service.active_queries[query_id] = {
            'parameters': mock_query_parameters,
            'status': QueryStatus.PENDING,
            'created_at': '2025-01-18T10:00:00Z',
            'progress_callback': callback,
            'log_handler': None
        }

        mock_session = MagicMock()
        mock_session.run_session = AsyncMock(return_value="# Final Answer")
        mock_session.save_report = Mock(return_value="results/test-query-123/report.md")
        mock_session.toc_tree = []
        mock_session.kb = None

        with patch('backend.services.query_service.SearchSession', return_value=mock_session):
            with patch('backend.services.query_service.setup_log_streaming', return_value=None):
                with patch('backend.services.query_service.cleanup_log_streaming'):
                    await service._process_query(query_id, mock_query_parameters, callback)

        # Callback should be called for progress updates
        assert callback.called

    @pytest.mark.asyncio
    async def test_process_query_handles_error(self, service, mock_query_parameters):
        """Test that process_query handles errors gracefully"""
        query_id = "test-query-123"
        callback = AsyncMock()

        service.active_queries[query_id] = {
            'parameters': mock_query_parameters,
            'status': QueryStatus.PENDING,
            'created_at': '2025-01-18T10:00:00Z',
            'progress_callback': callback,
            'log_handler': None
        }

        # Mock SearchSession to raise error
        with patch('backend.services.query_service.SearchSession', side_effect=Exception("Test error")):
            with patch('backend.services.query_service.setup_log_streaming', return_value=None):
                with patch('backend.services.query_service.cleanup_log_streaming'):
                    await service._process_query(query_id, mock_query_parameters, callback)

        # Query should be failed
        assert query_id in service.completed_queries
        assert service.completed_queries[query_id].status == QueryStatus.FAILED
        assert "Test error" in service.completed_queries[query_id].error_message


@pytest.mark.unit
@pytest.mark.services
class TestQueryServiceBuildTocResponse:
    """Tests for _build_toc_response method"""

    @pytest.fixture
    def service(self):
        """Create QueryService instance"""
        with patch('backend.services.query_service.QueryService._load_config'):
            return QueryService()

    @pytest.mark.skip(reason="Complex mocking of TOC nodes with Pydantic validation - covered by integration tests")
    def test_build_toc_response_single_node(self, service):
        """Test building TOC response from single node"""
        pass

    @pytest.mark.skip(reason="Complex mocking of TOC nodes with Pydantic validation - covered by integration tests")
    def test_build_toc_response_with_children(self, service):
        """Test building TOC response with children"""
        pass


@pytest.mark.unit
@pytest.mark.services
class TestQueryServiceExtractResults:
    """Tests for result extraction methods"""

    @pytest.fixture
    def service(self):
        """Create QueryService instance"""
        with patch('backend.services.query_service.QueryService._load_config'):
            return QueryService()

    def test_extract_web_results(self, service):
        """Test extracting web results from TOC node"""
        # Create mock TOC node with web results
        mock_node = MagicMock()
        mock_node.web_results = [
            {
                'title': 'Test Article',
                'url': 'https://example.com/test',
                'snippet': 'This is a test snippet',
                'relevance': 0.9
            }
        ]
        mock_node.children = []

        results = service._extract_web_results(mock_node)

        assert len(results) == 1
        assert results[0].title == 'Test Article'
        assert results[0].url == 'https://example.com/test'
        assert results[0].relevance == 0.9

    def test_extract_web_results_no_title(self, service):
        """Test extracting web results with missing title"""
        mock_node = MagicMock()
        mock_node.web_results = [
            {
                'title': '',
                'url': 'https://example.com/test',
                'snippet': 'Test snippet'
            }
        ]
        mock_node.children = []

        results = service._extract_web_results(mock_node)

        assert len(results) == 1
        assert results[0].title == 'example.com'

    def test_extract_web_results_with_children(self, service):
        """Test extracting web results from node with children"""
        # Create child node
        mock_child = MagicMock()
        mock_child.web_results = [
            {
                'title': 'Child Article',
                'url': 'https://example.com/child',
                'snippet': 'Child snippet'
            }
        ]
        mock_child.children = []

        # Create parent node
        mock_parent = MagicMock()
        mock_parent.web_results = [
            {
                'title': 'Parent Article',
                'url': 'https://example.com/parent',
                'snippet': 'Parent snippet'
            }
        ]
        mock_parent.children = [mock_child]

        results = service._extract_web_results(mock_parent)

        assert len(results) == 2
        assert any(r.title == 'Parent Article' for r in results)
        assert any(r.title == 'Child Article' for r in results)

    def test_extract_local_results(self, service):
        """Test extracting local results from knowledge base"""
        # Create mock knowledge base
        mock_kb = MagicMock()
        mock_kb.documents = [
            {
                'source': 'document1.pdf',
                'text': 'This is the content of document 1',
                'score': 0.88
            },
            {
                'source': 'document2.pdf',
                'text': 'This is the content of document 2',
                'score': 0.75
            }
        ]

        results = service._extract_local_results(mock_kb)

        assert len(results) == 2
        assert results[0].source == 'document1.pdf'
        assert results[0].relevance == 0.88
        assert len(results[0].snippet) <= 200

    def test_extract_local_results_empty_kb(self, service):
        """Test extracting local results from empty knowledge base"""
        mock_kb = MagicMock()
        mock_kb.documents = []

        results = service._extract_local_results(mock_kb)

        assert len(results) == 0


@pytest.mark.unit
@pytest.mark.services
class TestQueryServiceGetQueryStatus:
    """Tests for get_query_status method"""

    @pytest.fixture
    def service(self):
        """Create QueryService instance"""
        with patch('backend.services.query_service.QueryService._load_config'):
            return QueryService()

    def test_get_completed_query(self, service, mock_query_result):
        """Test getting status of completed query"""
        service.completed_queries["test-query-123"] = mock_query_result

        result = service.get_query_status("test-query-123")

        assert result is not None
        assert result.query_id == "test-query-123"
        assert result.status == QueryStatus.COMPLETED

    def test_get_active_query(self, service, mock_query_parameters):
        """Test getting status of active query"""
        service.active_queries["test-query-456"] = {
            'status': QueryStatus.PROCESSING,
            'parameters': mock_query_parameters,
            'created_at': '2025-01-18T10:00:00Z'
        }

        result = service.get_query_status("test-query-456")

        assert result is not None
        assert result.query_id == "test-query-456"
        assert result.status == QueryStatus.PROCESSING

    def test_get_nonexistent_query(self, service):
        """Test getting status of non-existent query"""
        result = service.get_query_status("nonexistent-id")

        assert result is None


@pytest.mark.unit
@pytest.mark.services
class TestQueryServiceListQueries:
    """Tests for list_queries method"""

    @pytest.fixture
    def service(self):
        """Create QueryService instance"""
        with patch('backend.services.query_service.QueryService._load_config'):
            return QueryService()

    def test_list_queries_empty(self, service):
        """Test listing queries when there are none"""
        queries = service.list_queries()

        assert queries == []

    def test_list_queries_with_completed(self, service, mock_query_result):
        """Test listing queries with completed queries"""
        service.completed_queries["query-1"] = mock_query_result

        queries = service.list_queries()

        assert len(queries) == 1
        assert queries[0].query_id == "test-query-123"

    def test_list_queries_with_active(self, service, mock_query_parameters):
        """Test listing queries with active queries"""
        service.active_queries["query-1"] = {
            'status': QueryStatus.PROCESSING,
            'parameters': mock_query_parameters,
            'created_at': '2025-01-18T10:00:00Z'
        }

        queries = service.list_queries()

        assert len(queries) == 1
        assert queries[0].status == QueryStatus.PROCESSING

    def test_list_queries_with_limit(self, service, mock_query_result):
        """Test listing queries with limit"""
        # Add multiple queries
        for i in range(5):
            result = mock_query_result.model_copy()
            result.query_id = f"query-{i}"
            service.completed_queries[f"query-{i}"] = result

        queries = service.list_queries(limit=3)

        assert len(queries) <= 3

    def test_list_queries_sorted_by_date(self, service, mock_query_result):
        """Test that queries are sorted by creation time"""
        # Add queries with different timestamps
        result1 = mock_query_result.model_copy()
        result1.query_id = "query-1"
        result1.created_at = "2025-01-18T10:00:00Z"

        result2 = mock_query_result.model_copy()
        result2.query_id = "query-2"
        result2.created_at = "2025-01-18T11:00:00Z"

        service.completed_queries["query-1"] = result1
        service.completed_queries["query-2"] = result2

        queries = service.list_queries()

        # Most recent should be first
        assert queries[0].query_id == "query-2"
        assert queries[1].query_id == "query-1"


@pytest.mark.unit
@pytest.mark.services
class TestQueryServiceGetBufferedLogs:
    """Tests for get_buffered_logs method"""

    @pytest.fixture
    def service(self):
        """Create QueryService instance"""
        with patch('backend.services.query_service.QueryService._load_config'):
            return QueryService()

    def test_get_buffered_logs_with_handler(self, service):
        """Test getting buffered logs when handler exists"""
        # Create mock print capture with logs
        mock_print_capture = MagicMock()
        mock_print_capture.get_logs = Mock(return_value=[
            {'message': 'Log 1'},
            {'message': 'Log 2'}
        ])

        service.active_queries["query-1"] = {
            'log_handler': (MagicMock(), mock_print_capture, MagicMock())
        }

        logs = service.get_buffered_logs("query-1")

        assert len(logs) == 2
        assert logs[0]['message'] == 'Log 1'

    def test_get_buffered_logs_without_handler(self, service):
        """Test getting buffered logs when no handler exists"""
        service.active_queries["query-1"] = {
            'log_handler': None
        }

        logs = service.get_buffered_logs("query-1")

        assert logs == []

    def test_get_buffered_logs_nonexistent_query(self, service):
        """Test getting buffered logs for non-existent query"""
        logs = service.get_buffered_logs("nonexistent-id")

        assert logs == []

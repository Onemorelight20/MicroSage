# tests/conftest.py
"""Shared pytest fixtures for NanoSage tests"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from typing import Generator

import pytest

# Add parent directory to path to import backend modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.api.models import (
    QueryParameters,
    QueryResult,
    QueryStatus,
    RetrievalModel,
    LLMProvider,
    ExportFormat,
    WebResult,
    LocalResult,
    TOCNodeResponse,
)


@pytest.fixture
def temp_dir() -> Generator[str, None, None]:
    """Create a temporary directory for test files"""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    # Cleanup
    if os.path.exists(temp_path):
        shutil.rmtree(temp_path)


@pytest.fixture
def mock_query_parameters() -> QueryParameters:
    """Create mock query parameters for testing"""
    return QueryParameters(
        query="What is quantum computing?",
        web_search=True,
        retrieval_model=RetrievalModel.SIGLIP,
        top_k=5,
        max_depth=2,
        corpus_dir=None,
        personality="scientific",
        rag_model="gemma",
        llm_provider=LLMProvider.OLLAMA,
        llm_model="gemma2:2b",
        web_concurrency=8,
        include_wikipedia=False,
    )


@pytest.fixture
def mock_toc_node() -> TOCNodeResponse:
    """Create a mock TOC node for testing"""
    return TOCNodeResponse(
        node_id="node-1",
        query_text="What is quantum computing?",
        depth=0,
        summary="Quantum computing uses quantum mechanics for computation",
        relevance_score=0.95,
        children=[
            TOCNodeResponse(
                node_id="node-1-1",
                query_text="How do qubits work?",
                depth=1,
                summary="Qubits are quantum bits that can be in superposition",
                relevance_score=0.87,
                children=[],
            )
        ],
    )


@pytest.fixture
def mock_web_results() -> list[WebResult]:
    """Create mock web results for testing"""
    return [
        WebResult(
            title="Introduction to Quantum Computing",
            url="https://example.com/quantum-intro",
            snippet="Quantum computing is a revolutionary technology...",
            relevance=0.92,
        ),
        WebResult(
            title="Quantum Mechanics Basics",
            url="https://example.com/quantum-basics",
            snippet="Understanding the fundamentals of quantum mechanics...",
            relevance=0.85,
        ),
    ]


@pytest.fixture
def mock_local_results() -> list[LocalResult]:
    """Create mock local results for testing"""
    return [
        LocalResult(
            source="quantum_paper.pdf",
            snippet="This paper discusses quantum algorithms...",
            relevance=0.88,
        ),
        LocalResult(
            source="quantum_textbook.pdf",
            snippet="Chapter 3: Quantum gates and circuits...",
            relevance=0.81,
        ),
    ]


@pytest.fixture
def mock_query_result(
    mock_query_parameters,
    mock_toc_node,
    mock_web_results,
    mock_local_results,
) -> QueryResult:
    """Create a complete mock query result for testing"""
    return QueryResult(
        query_id="test-query-123",
        status=QueryStatus.COMPLETED,
        query_text="What is quantum computing?",
        parameters=mock_query_parameters,
        final_answer="# Quantum Computing\n\nQuantum computing is a revolutionary field that leverages quantum mechanics...",
        search_tree=mock_toc_node,
        web_results=mock_web_results,
        local_results=mock_local_results,
        created_at="2025-01-18T10:00:00Z",
        completed_at="2025-01-18T10:05:30Z",
        processing_time_ms=330000,
    )


@pytest.fixture
def mock_results_directory(temp_dir: str) -> str:
    """Create a mock results directory structure"""
    results_dir = os.path.join(temp_dir, "results")
    os.makedirs(results_dir, exist_ok=True)

    # Create a sample query result directory
    query_id = "test-query-123"
    query_dir = os.path.join(results_dir, query_id)
    os.makedirs(query_dir, exist_ok=True)

    # Create mock toc_analysis.json
    toc_data = {
        "toc_tree": [
            {
                "query_text": "What is quantum computing?",
                "timestamps": {
                    "created": "2025-01-18T10:00:00Z",
                    "completed": "2025-01-18T10:05:30Z",
                },
                "metrics": {"processing_time_ms": 330000},
            }
        ]
    }

    import json
    with open(os.path.join(query_dir, "toc_analysis.json"), "w") as f:
        json.dump(toc_data, f)

    # Create mock final_report.md
    with open(os.path.join(query_dir, "final_report.md"), "w") as f:
        f.write("# Test Report\n\nThis is a test report.")

    return results_dir


@pytest.fixture
def mock_corpus_directory(temp_dir: str) -> str:
    """Create a mock corpus directory with test files"""
    corpus_dir = os.path.join(temp_dir, "corpus")
    os.makedirs(corpus_dir, exist_ok=True)

    # Create sample files
    with open(os.path.join(corpus_dir, "document1.txt"), "w") as f:
        f.write("Sample document content")

    return corpus_dir

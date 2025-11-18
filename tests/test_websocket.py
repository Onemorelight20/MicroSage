# tests/test_websocket.py
"""Unit tests for backend/api/websocket.py"""

import json
import pytest
from unittest.mock import AsyncMock, Mock, patch
from backend.api.websocket import ConnectionManager


class MockWebSocket:
    """Mock WebSocket for testing"""

    def __init__(self):
        self.accepted = False
        self.sent_messages = []
        self.closed = False

    async def accept(self):
        """Mock accept method"""
        self.accepted = True

    async def send_text(self, data: str):
        """Mock send_text method"""
        self.sent_messages.append(data)

    async def close(self):
        """Mock close method"""
        self.closed = True


@pytest.mark.unit
@pytest.mark.websocket
class TestConnectionManagerInit:
    """Tests for ConnectionManager initialization"""

    def test_init_creates_empty_connections(self):
        """Test that ConnectionManager initializes with empty connections"""
        manager = ConnectionManager()

        assert manager.active_connections == {}
        assert manager.connection_queries == {}
        assert manager.debug is False

    def test_init_with_debug_enabled(self):
        """Test initializing ConnectionManager with debug mode"""
        manager = ConnectionManager(debug=True)

        assert manager.debug is True


@pytest.mark.unit
@pytest.mark.websocket
class TestConnectionManagerConnect:
    """Tests for connect method"""

    @pytest.fixture
    def manager(self):
        """Create ConnectionManager instance"""
        return ConnectionManager()

    @pytest.mark.asyncio
    async def test_connect_new_websocket(self, manager):
        """Test connecting a new WebSocket"""
        websocket = MockWebSocket()
        query_id = "query-123"

        await manager.connect(websocket, query_id)

        # Check WebSocket was accepted
        assert websocket.accepted is True

        # Check connection is stored
        assert query_id in manager.active_connections
        assert websocket in manager.active_connections[query_id]

        # Check reverse mapping
        assert websocket in manager.connection_queries
        assert manager.connection_queries[websocket] == query_id

    @pytest.mark.asyncio
    async def test_connect_multiple_websockets_same_query(self, manager):
        """Test connecting multiple WebSockets to the same query"""
        websocket1 = MockWebSocket()
        websocket2 = MockWebSocket()
        query_id = "query-123"

        await manager.connect(websocket1, query_id)
        await manager.connect(websocket2, query_id)

        # Both should be connected to same query
        assert len(manager.active_connections[query_id]) == 2
        assert websocket1 in manager.active_connections[query_id]
        assert websocket2 in manager.active_connections[query_id]

    @pytest.mark.asyncio
    async def test_connect_multiple_queries(self, manager):
        """Test connecting WebSockets to different queries"""
        websocket1 = MockWebSocket()
        websocket2 = MockWebSocket()
        query_id1 = "query-123"
        query_id2 = "query-456"

        await manager.connect(websocket1, query_id1)
        await manager.connect(websocket2, query_id2)

        # Each query should have its own connection
        assert len(manager.active_connections) == 2
        assert query_id1 in manager.active_connections
        assert query_id2 in manager.active_connections
        assert len(manager.active_connections[query_id1]) == 1
        assert len(manager.active_connections[query_id2]) == 1

    @pytest.mark.asyncio
    async def test_connect_with_debug_enabled(self, capsys):
        """Test connect with debug mode enabled prints message"""
        manager = ConnectionManager(debug=True)
        websocket = MockWebSocket()
        query_id = "query-123"

        await manager.connect(websocket, query_id)

        # Check debug output (would be printed in real scenario)
        # In tests, we just verify the connection works
        assert websocket.accepted is True


@pytest.mark.unit
@pytest.mark.websocket
class TestConnectionManagerDisconnect:
    """Tests for disconnect method"""

    @pytest.fixture
    def manager(self):
        """Create ConnectionManager instance"""
        return ConnectionManager()

    @pytest.mark.asyncio
    async def test_disconnect_existing_websocket(self, manager):
        """Test disconnecting an existing WebSocket"""
        websocket = MockWebSocket()
        query_id = "query-123"

        await manager.connect(websocket, query_id)
        manager.disconnect(websocket)

        # Connection should be removed
        assert websocket not in manager.connection_queries
        assert query_id not in manager.active_connections

    @pytest.mark.asyncio
    async def test_disconnect_one_of_multiple_websockets(self, manager):
        """Test disconnecting one WebSocket when multiple are connected"""
        websocket1 = MockWebSocket()
        websocket2 = MockWebSocket()
        query_id = "query-123"

        await manager.connect(websocket1, query_id)
        await manager.connect(websocket2, query_id)

        manager.disconnect(websocket1)

        # websocket1 should be removed, websocket2 should remain
        assert websocket1 not in manager.active_connections[query_id]
        assert websocket2 in manager.active_connections[query_id]
        assert len(manager.active_connections[query_id]) == 1

    @pytest.mark.asyncio
    async def test_disconnect_last_websocket_removes_query(self, manager):
        """Test that disconnecting last WebSocket removes query from active_connections"""
        websocket = MockWebSocket()
        query_id = "query-123"

        await manager.connect(websocket, query_id)
        manager.disconnect(websocket)

        # Query should be removed from active_connections when no clients remain
        assert query_id not in manager.active_connections

    def test_disconnect_nonexistent_websocket(self, manager):
        """Test disconnecting a WebSocket that was never connected"""
        websocket = MockWebSocket()

        # Should not raise error
        manager.disconnect(websocket)

        assert websocket not in manager.connection_queries


@pytest.mark.unit
@pytest.mark.websocket
class TestConnectionManagerSendProgressUpdate:
    """Tests for send_progress_update method"""

    @pytest.fixture
    def manager(self):
        """Create ConnectionManager instance"""
        return ConnectionManager()

    @pytest.mark.asyncio
    async def test_send_progress_update_to_connected_client(self, manager):
        """Test sending progress update to connected client"""
        websocket = MockWebSocket()
        query_id = "query-123"

        await manager.connect(websocket, query_id)

        message = {
            "query_id": query_id,
            "status": "processing",
            "message": "Processing query...",
            "progress_percentage": 50,
        }

        await manager.send_progress_update(query_id, message)

        # Check message was sent
        assert len(websocket.sent_messages) == 1
        sent_data = json.loads(websocket.sent_messages[0])
        assert sent_data == message

    @pytest.mark.asyncio
    async def test_send_progress_update_to_multiple_clients(self, manager):
        """Test sending progress update to multiple clients for same query"""
        websocket1 = MockWebSocket()
        websocket2 = MockWebSocket()
        query_id = "query-123"

        await manager.connect(websocket1, query_id)
        await manager.connect(websocket2, query_id)

        message = {"status": "completed", "message": "Query completed"}

        await manager.send_progress_update(query_id, message)

        # Both clients should receive the message
        assert len(websocket1.sent_messages) == 1
        assert len(websocket2.sent_messages) == 1

        # Messages should be identical
        assert websocket1.sent_messages[0] == websocket2.sent_messages[0]

    @pytest.mark.asyncio
    async def test_send_progress_update_to_nonexistent_query(self, manager):
        """Test sending progress update when no clients are connected"""
        message = {"status": "processing", "message": "Test"}

        # Should not raise error
        await manager.send_progress_update("nonexistent-query", message)

    @pytest.mark.asyncio
    async def test_send_progress_update_handles_send_error(self, manager):
        """Test that send_progress_update handles WebSocket send errors"""
        websocket = MockWebSocket()
        query_id = "query-123"

        await manager.connect(websocket, query_id)

        # Mock send_text to raise error
        async def raise_error(data):
            raise Exception("Connection lost")

        websocket.send_text = raise_error

        message = {"status": "processing", "message": "Test"}

        # Should not raise error, but should disconnect the client
        await manager.send_progress_update(query_id, message)

        # WebSocket should be disconnected
        assert websocket not in manager.connection_queries

    @pytest.mark.asyncio
    async def test_send_progress_update_json_serialization(self, manager):
        """Test that message is properly JSON serialized"""
        websocket = MockWebSocket()
        query_id = "query-123"

        await manager.connect(websocket, query_id)

        message = {
            "status": "processing",
            "message": "Test message",
            "nested": {"key": "value"},
            "array": [1, 2, 3],
        }

        await manager.send_progress_update(query_id, message)

        # Verify JSON is valid
        sent_message = websocket.sent_messages[0]
        parsed = json.loads(sent_message)
        assert parsed == message


@pytest.mark.unit
@pytest.mark.websocket
class TestConnectionManagerSendLog:
    """Tests for send_log method"""

    @pytest.fixture
    def manager(self):
        """Create ConnectionManager instance"""
        return ConnectionManager()

    @pytest.mark.asyncio
    async def test_send_log_delegates_to_send_progress_update(self, manager):
        """Test that send_log delegates to send_progress_update"""
        websocket = MockWebSocket()
        query_id = "query-123"

        await manager.connect(websocket, query_id)

        log_message = {
            "type": "log",
            "message": "Building knowledge base...",
            "timestamp": "2025-01-18T10:05:00Z",
        }

        await manager.send_log(query_id, log_message)

        # Should receive the log message
        assert len(websocket.sent_messages) == 1
        sent_data = json.loads(websocket.sent_messages[0])
        assert sent_data == log_message


@pytest.mark.unit
@pytest.mark.websocket
class TestConnectionManagerBroadcast:
    """Tests for broadcast method"""

    @pytest.fixture
    def manager(self):
        """Create ConnectionManager instance"""
        return ConnectionManager()

    @pytest.mark.asyncio
    async def test_broadcast_to_all_clients(self, manager):
        """Test broadcasting message to all connected clients"""
        websocket1 = MockWebSocket()
        websocket2 = MockWebSocket()
        websocket3 = MockWebSocket()

        await manager.connect(websocket1, "query-1")
        await manager.connect(websocket2, "query-2")
        await manager.connect(websocket3, "query-3")

        message = {"type": "system", "message": "System maintenance in 5 minutes"}

        await manager.broadcast(message)

        # All clients should receive the message
        assert len(websocket1.sent_messages) == 1
        assert len(websocket2.sent_messages) == 1
        assert len(websocket3.sent_messages) == 1

        # All messages should be identical
        expected_json = json.dumps(message)
        assert websocket1.sent_messages[0] == expected_json
        assert websocket2.sent_messages[0] == expected_json
        assert websocket3.sent_messages[0] == expected_json

    @pytest.mark.asyncio
    async def test_broadcast_to_multiple_clients_same_query(self, manager):
        """Test broadcasting to multiple clients on same query"""
        websocket1 = MockWebSocket()
        websocket2 = MockWebSocket()
        query_id = "query-123"

        await manager.connect(websocket1, query_id)
        await manager.connect(websocket2, query_id)

        message = {"type": "broadcast", "message": "Broadcast message"}

        await manager.broadcast(message)

        # Both clients should receive the message
        assert len(websocket1.sent_messages) == 1
        assert len(websocket2.sent_messages) == 1

    @pytest.mark.asyncio
    async def test_broadcast_with_no_connections(self, manager):
        """Test broadcasting when no clients are connected"""
        message = {"type": "system", "message": "Test"}

        # Should not raise error
        await manager.broadcast(message)

    @pytest.mark.asyncio
    async def test_broadcast_handles_send_error(self, manager):
        """Test that broadcast handles WebSocket send errors gracefully"""
        websocket1 = MockWebSocket()
        websocket2 = MockWebSocket()

        await manager.connect(websocket1, "query-1")
        await manager.connect(websocket2, "query-2")

        # Make websocket1 fail
        async def raise_error(data):
            raise Exception("Connection lost")

        websocket1.send_text = raise_error

        message = {"type": "system", "message": "Test"}

        # Should not raise error
        await manager.broadcast(message)

        # websocket1 should be disconnected
        assert websocket1 not in manager.connection_queries
        # websocket2 should still receive the message
        assert len(websocket2.sent_messages) == 1


@pytest.mark.unit
@pytest.mark.websocket
class TestConnectionManagerIntegration:
    """Integration tests for ConnectionManager"""

    @pytest.fixture
    def manager(self):
        """Create ConnectionManager instance"""
        return ConnectionManager()

    @pytest.mark.asyncio
    async def test_complete_connection_lifecycle(self, manager):
        """Test complete connection lifecycle: connect, send, disconnect"""
        websocket = MockWebSocket()
        query_id = "query-123"

        # Connect
        await manager.connect(websocket, query_id)
        assert websocket.accepted is True

        # Send progress update
        message1 = {"status": "processing", "message": "Step 1"}
        await manager.send_progress_update(query_id, message1)
        assert len(websocket.sent_messages) == 1

        # Send another update
        message2 = {"status": "processing", "message": "Step 2"}
        await manager.send_progress_update(query_id, message2)
        assert len(websocket.sent_messages) == 2

        # Disconnect
        manager.disconnect(websocket)
        assert websocket not in manager.connection_queries
        assert query_id not in manager.active_connections

    @pytest.mark.asyncio
    async def test_multiple_queries_simultaneous(self, manager):
        """Test managing multiple queries simultaneously"""
        # Create connections for 3 different queries
        ws1 = MockWebSocket()
        ws2 = MockWebSocket()
        ws3 = MockWebSocket()

        await manager.connect(ws1, "query-1")
        await manager.connect(ws2, "query-2")
        await manager.connect(ws3, "query-3")

        # Send individual updates
        await manager.send_progress_update("query-1", {"message": "Update 1"})
        await manager.send_progress_update("query-2", {"message": "Update 2"})
        await manager.send_progress_update("query-3", {"message": "Update 3"})

        # Each should only receive their own update
        assert len(ws1.sent_messages) == 1
        assert "Update 1" in ws1.sent_messages[0]

        assert len(ws2.sent_messages) == 1
        assert "Update 2" in ws2.sent_messages[0]

        assert len(ws3.sent_messages) == 1
        assert "Update 3" in ws3.sent_messages[0]

    @pytest.mark.asyncio
    async def test_reconnection_scenario(self, manager):
        """Test disconnecting and reconnecting WebSocket"""
        websocket1 = MockWebSocket()
        websocket2 = MockWebSocket()
        query_id = "query-123"

        # First connection
        await manager.connect(websocket1, query_id)

        # Send message
        await manager.send_progress_update(query_id, {"message": "First connection"})
        assert len(websocket1.sent_messages) == 1

        # Disconnect
        manager.disconnect(websocket1)

        # Reconnect with new WebSocket
        await manager.connect(websocket2, query_id)

        # Send message to reconnected client
        await manager.send_progress_update(query_id, {"message": "After reconnect"})

        # Old connection should not receive message
        assert len(websocket1.sent_messages) == 1

        # New connection should receive message
        assert len(websocket2.sent_messages) == 1
        assert "After reconnect" in websocket2.sent_messages[0]

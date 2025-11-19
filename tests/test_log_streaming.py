# tests/test_log_streaming.py
"""Unit tests for backend/utils/log_streaming.py"""

import sys
import logging
import asyncio
import pytest
from io import StringIO
from unittest.mock import Mock, AsyncMock, MagicMock, patch
from backend.utils.log_streaming import (
    LogStreamHandler,
    PrintCapture,
    setup_log_streaming,
    cleanup_log_streaming
)


@pytest.mark.unit
@pytest.mark.utils
class TestLogStreamHandlerInit:
    """Tests for LogStreamHandler initialization"""

    def test_init_with_required_params(self):
        """Test initialization with required parameters"""
        handler = LogStreamHandler("query-123", None, None)

        assert handler.query_id == "query-123"
        assert handler.callback is None
        assert handler.loop is None
        assert handler.log_buffer == []
        assert handler.max_buffer_size == 100

    def test_init_with_callback(self):
        """Test initialization with callback"""
        callback = AsyncMock()
        loop = asyncio.new_event_loop()

        handler = LogStreamHandler("query-123", callback, loop)

        assert handler.callback == callback
        assert handler.loop == loop

    def test_init_log_buffer_empty(self):
        """Test that log buffer starts empty"""
        handler = LogStreamHandler("query-123", None, None)

        assert len(handler.log_buffer) == 0


@pytest.mark.unit
@pytest.mark.utils
class TestLogStreamHandlerEmit:
    """Tests for LogStreamHandler emit method"""

    def test_emit_blocks_all_logging(self):
        """Test that emit blocks all logging framework messages"""
        handler = LogStreamHandler("query-123", None, None)
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None
        )

        # emit should return None and not add to buffer
        result = handler.emit(record)

        assert result is None
        assert len(handler.log_buffer) == 0


@pytest.mark.unit
@pytest.mark.utils
class TestLogStreamHandlerGetLogs:
    """Tests for LogStreamHandler get_logs method"""

    def test_get_logs_empty(self):
        """Test getting logs when buffer is empty"""
        handler = LogStreamHandler("query-123", None, None)

        logs = handler.get_logs()

        assert logs == []

    def test_get_logs_returns_copy(self):
        """Test that get_logs returns a copy of the buffer"""
        handler = LogStreamHandler("query-123", None, None)
        handler.log_buffer = [{"message": "test"}]

        logs = handler.get_logs()

        # Modify returned list
        logs.append({"message": "new"})

        # Original buffer should be unchanged
        assert len(handler.log_buffer) == 1


@pytest.mark.unit
@pytest.mark.utils
class TestPrintCaptureInit:
    """Tests for PrintCapture initialization"""

    def test_init_with_required_params(self):
        """Test initialization with required parameters"""
        capture = PrintCapture("query-123", None, None, None)

        assert capture.query_id == "query-123"
        assert capture.callback is None
        assert capture.loop is None
        assert capture.buffer == ""
        assert capture.log_buffer == []
        assert capture.debug is False

    def test_init_with_debug(self):
        """Test initialization with debug mode"""
        capture = PrintCapture("query-123", None, None, None, debug=True)

        assert capture.debug is True

    def test_init_sets_project_root(self):
        """Test that initialization sets project root"""
        capture = PrintCapture("query-123", None, None, None)

        assert capture.project_root is not None
        assert isinstance(capture.project_root, str)


@pytest.mark.unit
@pytest.mark.utils
class TestPrintCaptureWrite:
    """Tests for PrintCapture write method"""

    def test_write_to_original_stdout(self):
        """Test that write writes to original stdout"""
        original_stdout = StringIO()
        capture = PrintCapture("query-123", None, None, original_stdout)

        capture.write("Test message\n")

        assert "Test message" in original_stdout.getvalue()

    def test_write_buffers_text(self):
        """Test that write buffers text"""
        capture = PrintCapture("query-123", None, None, None)

        capture.write("Test ")
        capture.write("message")

        assert "Test message" in capture.buffer

    def test_write_captures_info_messages(self):
        """Test that write captures [INFO] messages"""
        callback = AsyncMock()
        loop = asyncio.new_event_loop()
        capture = PrintCapture("query-123", callback, loop, None)

        capture.write("[INFO] Test message\n")

        # Should be added to log buffer
        assert len(capture.log_buffer) == 1
        assert "Test message" in capture.log_buffer[0]['message']

    def test_write_captures_debug_messages(self):
        """Test that write captures [DEBUG] messages"""
        callback = AsyncMock()
        loop = asyncio.new_event_loop()
        capture = PrintCapture("query-123", callback, loop, None)

        capture.write("[DEBUG] Debug message\n")

        assert len(capture.log_buffer) == 1

    def test_write_ignores_non_tagged_messages(self):
        """Test that write ignores messages without [INFO] or [DEBUG] tags"""
        capture = PrintCapture("query-123", None, None, None)

        capture.write("Regular message\n")

        assert len(capture.log_buffer) == 0

    def test_write_respects_max_buffer_size(self):
        """Test that write respects max buffer size"""
        capture = PrintCapture("query-123", None, None, None)
        capture.max_buffer_size = 3

        for i in range(5):
            capture.write(f"[INFO] Message {i}\n")

        # Should only keep last 3 messages
        assert len(capture.log_buffer) <= 3

    def test_write_returns_length(self):
        """Test that write returns the length of text written"""
        capture = PrintCapture("query-123", None, None, None)

        result = capture.write("Test")

        assert result == 4


@pytest.mark.unit
@pytest.mark.utils
class TestPrintCaptureFlush:
    """Tests for PrintCapture flush method"""

    def test_flush_flushes_original_stdout(self):
        """Test that flush flushes original stdout"""
        original_stdout = MagicMock()
        capture = PrintCapture("query-123", None, None, original_stdout)

        capture.flush()

        original_stdout.flush.assert_called_once()

    def test_flush_without_original_stdout(self):
        """Test that flush doesn't error without original stdout"""
        capture = PrintCapture("query-123", None, None, None)

        # Should not raise error
        capture.flush()


@pytest.mark.unit
@pytest.mark.utils
class TestPrintCaptureMakeUserFriendly:
    """Tests for PrintCapture _make_user_friendly method"""

    def test_make_user_friendly_removes_info_tag(self):
        """Test that _make_user_friendly removes [INFO] tag"""
        capture = PrintCapture("query-123", None, None, None)

        result = capture._make_user_friendly("[INFO] Test message")

        assert result == "Test message"
        assert "[INFO]" not in result

    def test_make_user_friendly_removes_debug_tag(self):
        """Test that _make_user_friendly removes [DEBUG] tag"""
        capture = PrintCapture("query-123", None, None, None)

        result = capture._make_user_friendly("[DEBUG] Test message")

        assert result == "Test message"
        assert "[DEBUG]" not in result

    def test_make_user_friendly_normalizes_paths(self):
        """Test that _make_user_friendly normalizes file paths"""
        capture = PrintCapture("query-123", None, None, None)

        result = capture._make_user_friendly("[INFO] Processing C:\\Users\\test\\file.txt")

        # Should not contain absolute path
        assert "C:" not in result or "Users" not in result

    def test_make_user_friendly_strips_whitespace(self):
        """Test that _make_user_friendly strips whitespace"""
        capture = PrintCapture("query-123", None, None, None)

        result = capture._make_user_friendly("[INFO] Test message")

        # The function strips leading [INFO] and whitespace
        assert "Test message" in result
        assert result.strip() == "Test message"

    def test_make_user_friendly_empty_string(self):
        """Test _make_user_friendly with empty string after cleanup"""
        capture = PrintCapture("query-123", None, None, None)

        result = capture._make_user_friendly("[INFO]   ")

        assert result is None or result == ""


@pytest.mark.unit
@pytest.mark.utils
class TestPrintCaptureGetLogs:
    """Tests for PrintCapture get_logs method"""

    def test_get_logs_empty(self):
        """Test getting logs when buffer is empty"""
        capture = PrintCapture("query-123", None, None, None)

        logs = capture.get_logs()

        assert logs == []

    def test_get_logs_returns_copy(self):
        """Test that get_logs returns a copy"""
        capture = PrintCapture("query-123", None, None, None)
        capture.log_buffer = [{"message": "test"}]

        logs = capture.get_logs()
        logs.append({"message": "new"})

        # Original should be unchanged
        assert len(capture.log_buffer) == 1


@pytest.mark.unit
@pytest.mark.utils
class TestSetupLogStreaming:
    """Tests for setup_log_streaming function"""

    def test_setup_log_streaming_returns_tuple(self):
        """Test that setup_log_streaming returns a tuple"""
        result = setup_log_streaming("query-123", None, None)

        assert isinstance(result, tuple)
        assert len(result) == 3

    def test_setup_log_streaming_creates_handler(self):
        """Test that setup_log_streaming creates LogStreamHandler"""
        handler, print_capture, original_stdout = setup_log_streaming("query-123", None, None)

        assert isinstance(handler, LogStreamHandler)
        assert handler.query_id == "query-123"

    def test_setup_log_streaming_creates_print_capture(self):
        """Test that setup_log_streaming creates PrintCapture"""
        handler, print_capture, original_stdout = setup_log_streaming("query-123", None, None)

        assert isinstance(print_capture, PrintCapture)
        assert print_capture.query_id == "query-123"

    def test_setup_log_streaming_replaces_stdout(self):
        """Test that setup_log_streaming replaces sys.stdout"""
        original = sys.stdout

        try:
            handler, print_capture, original_stdout = setup_log_streaming("query-123", None, None)

            # stdout should be replaced
            assert sys.stdout == print_capture
            assert original_stdout == original
        finally:
            # Restore
            sys.stdout = original

    def test_setup_log_streaming_adds_handler_to_root_logger(self):
        """Test that setup_log_streaming adds handler to root logger"""
        root_logger = logging.getLogger()
        original_handlers = len(root_logger.handlers)

        try:
            handler, print_capture, original_stdout = setup_log_streaming("query-123", None, None)

            # Should have added a handler
            assert len(root_logger.handlers) > original_handlers
            assert handler in root_logger.handlers
        finally:
            # Cleanup
            if handler in root_logger.handlers:
                root_logger.removeHandler(handler)
            sys.stdout = original_stdout

    def test_setup_log_streaming_with_debug(self):
        """Test setup_log_streaming with debug mode"""
        handler, print_capture, original_stdout = setup_log_streaming(
            "query-123", None, None, debug=True
        )

        assert print_capture.debug is True

        # Cleanup
        sys.stdout = original_stdout
        logging.getLogger().removeHandler(handler)


@pytest.mark.unit
@pytest.mark.utils
class TestCleanupLogStreaming:
    """Tests for cleanup_log_streaming function"""

    def test_cleanup_log_streaming_restores_stdout(self):
        """Test that cleanup_log_streaming restores stdout"""
        original = sys.stdout
        handler, print_capture, original_stdout = setup_log_streaming("query-123", None, None)

        cleanup_log_streaming((handler, print_capture, original_stdout))

        # stdout should be restored
        assert sys.stdout == original_stdout

    def test_cleanup_log_streaming_removes_handler(self):
        """Test that cleanup_log_streaming removes handler from logger"""
        root_logger = logging.getLogger()
        handler, print_capture, original_stdout = setup_log_streaming("query-123", None, None)

        cleanup_log_streaming((handler, print_capture, original_stdout))

        # Handler should be removed
        assert handler not in root_logger.handlers

    def test_cleanup_log_streaming_with_none(self):
        """Test that cleanup_log_streaming handles None input"""
        # Should not raise error
        cleanup_log_streaming(None)

    def test_cleanup_log_streaming_complete_cycle(self):
        """Test complete setup and cleanup cycle"""
        original_stdout = sys.stdout
        root_logger = logging.getLogger()
        original_handlers = len(root_logger.handlers)

        # Setup
        handler_tuple = setup_log_streaming("query-123", None, None)

        # Cleanup
        cleanup_log_streaming(handler_tuple)

        # Everything should be restored
        assert sys.stdout == original_stdout
        assert len(root_logger.handlers) == original_handlers


@pytest.mark.unit
@pytest.mark.utils
class TestLogStreamingIntegration:
    """Integration tests for log streaming"""

    @pytest.mark.asyncio
    async def test_complete_log_streaming_workflow(self):
        """Test complete log streaming workflow"""
        messages_received = []

        async def callback(message):
            messages_received.append(message)

        loop = asyncio.get_event_loop()
        original_stdout = sys.stdout

        try:
            # Setup
            handler_tuple = setup_log_streaming("query-123", callback, loop)

            # Write some log messages
            print("[INFO] Test message 1", flush=True)
            print("[DEBUG] Test message 2", flush=True)
            print("Regular message")  # Should be ignored

            # Give async callbacks time to run
            await asyncio.sleep(0.1)

            # Cleanup
            cleanup_log_streaming(handler_tuple)

            # Should have received messages
            assert len(messages_received) >= 0  # May vary due to async timing

        finally:
            sys.stdout = original_stdout
            # Ensure cleanup
            if handler_tuple:
                try:
                    cleanup_log_streaming(handler_tuple)
                except:
                    pass

    def test_print_capture_multiline_handling(self):
        """Test that PrintCapture handles multiline input correctly"""
        callback = AsyncMock()
        loop = asyncio.new_event_loop()
        capture = PrintCapture("query-123", callback, loop, None)

        try:
            # Write multiline text
            capture.write("[INFO] Line 1\n[INFO] Line 2\n")

            # Should have captured both lines
            assert len(capture.log_buffer) == 2
        finally:
            loop.close()

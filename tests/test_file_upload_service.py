# tests/test_file_upload_service.py
"""Unit tests for backend/services/file_upload_service.py"""

import os
import io
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock
from backend.services.file_upload_service import FileUploadService


class MockUploadFile:
    """Mock UploadFile for testing"""

    def __init__(self, filename: str, content: bytes = b"test content"):
        self.filename = filename
        self.file = io.BytesIO(content)

    def close(self):
        self.file.close()


@pytest.mark.unit
@pytest.mark.services
class TestFileUploadServiceInit:
    """Tests for FileUploadService initialization"""

    def test_init_creates_upload_directory(self, temp_dir):
        """Test that FileUploadService creates upload directory"""
        upload_dir = os.path.join(temp_dir, "uploads")
        assert not os.path.exists(upload_dir)

        service = FileUploadService(upload_dir=upload_dir)

        assert os.path.exists(upload_dir)
        assert os.path.isdir(upload_dir)

    def test_init_sets_upload_dir(self, temp_dir):
        """Test that upload directory is set correctly"""
        upload_dir = os.path.join(temp_dir, "uploads")
        service = FileUploadService(upload_dir=upload_dir)

        assert service.upload_dir == upload_dir

    def test_init_creates_empty_metadata_dict(self, temp_dir):
        """Test that file_metadata is initialized as empty dict"""
        service = FileUploadService(upload_dir=temp_dir)
        assert service.file_metadata == {}


@pytest.mark.unit
@pytest.mark.services
class TestFileUploadServiceHelpers:
    """Tests for helper methods"""

    @pytest.fixture
    def upload_service(self, temp_dir):
        """Create FileUploadService instance"""
        return FileUploadService(upload_dir=temp_dir)

    @pytest.mark.parametrize(
        "filename,expected_ext",
        [
            ("document.pdf", ".pdf"),
            ("image.PNG", ".png"),
            ("file.TXT", ".txt"),
            ("photo.JPG", ".jpg"),
            ("picture.JPEG", ".jpeg"),
            ("no_extension", ""),
            ("multiple.dots.pdf", ".pdf"),
        ],
    )
    def test_get_file_extension(self, upload_service, filename, expected_ext):
        """Test _get_file_extension extracts extension correctly"""
        result = upload_service._get_file_extension(filename)
        assert result == expected_ext

    @pytest.mark.parametrize(
        "filename,expected_allowed,expected_type",
        [
            ("document.pdf", True, "application/pdf"),
            ("file.txt", True, "text/plain"),
            ("image.png", True, "image/png"),
            ("photo.jpg", True, "image/jpeg"),
            ("picture.jpeg", True, "image/jpeg"),
            ("document.PDF", True, "application/pdf"),
            ("IMAGE.PNG", True, "image/png"),
        ],
    )
    def test_is_allowed_file_valid_types(
        self, upload_service, filename, expected_allowed, expected_type
    ):
        """Test _is_allowed_file accepts valid file types"""
        is_allowed, file_type = upload_service._is_allowed_file(filename)

        assert is_allowed == expected_allowed
        assert file_type == expected_type

    @pytest.mark.parametrize(
        "filename",
        [
            "script.js",
            "executable.exe",
            "archive.zip",
            "document.docx",
            "spreadsheet.xlsx",
            "no_extension",
        ],
    )
    def test_is_allowed_file_invalid_types(self, upload_service, filename):
        """Test _is_allowed_file rejects invalid file types"""
        is_allowed, file_type = upload_service._is_allowed_file(filename)

        assert is_allowed is False
        assert file_type == ""


@pytest.mark.unit
@pytest.mark.services
class TestFileUploadServiceUpload:
    """Tests for upload_file method"""

    @pytest.fixture
    def upload_service(self, temp_dir):
        """Create FileUploadService instance"""
        return FileUploadService(upload_dir=temp_dir)

    @pytest.mark.asyncio
    async def test_upload_pdf_file(self, upload_service, temp_dir):
        """Test uploading a PDF file"""
        mock_file = MockUploadFile("document.pdf", b"PDF content")

        metadata = await upload_service.upload_file(mock_file)

        # Check metadata
        assert "file_id" in metadata
        assert metadata["original_filename"] == "document.pdf"
        assert metadata["file_type"] == "application/pdf"
        assert metadata["file_size"] > 0
        assert metadata["extension"] == ".pdf"

        # Check file was saved
        file_path = metadata["file_path"]
        assert os.path.exists(file_path)

        # Check file content
        with open(file_path, "rb") as f:
            content = f.read()
        assert content == b"PDF content"

    @pytest.mark.asyncio
    async def test_upload_txt_file(self, upload_service):
        """Test uploading a TXT file"""
        mock_file = MockUploadFile("notes.txt", b"Text content")

        metadata = await upload_service.upload_file(mock_file)

        assert metadata["file_type"] == "text/plain"
        assert metadata["extension"] == ".txt"

    @pytest.mark.asyncio
    async def test_upload_png_image(self, upload_service):
        """Test uploading a PNG image"""
        mock_file = MockUploadFile("image.png", b"PNG image data")

        metadata = await upload_service.upload_file(mock_file)

        assert metadata["file_type"] == "image/png"
        assert metadata["extension"] == ".png"

    @pytest.mark.asyncio
    async def test_upload_jpg_image(self, upload_service):
        """Test uploading a JPG image"""
        mock_file = MockUploadFile("photo.jpg", b"JPG image data")

        metadata = await upload_service.upload_file(mock_file)

        assert metadata["file_type"] == "image/jpeg"
        assert metadata["extension"] == ".jpg"

    @pytest.mark.asyncio
    async def test_upload_invalid_file_type_raises_error(self, upload_service):
        """Test uploading invalid file type raises ValueError"""
        mock_file = MockUploadFile("script.js", b"JavaScript code")

        with pytest.raises(ValueError, match="File type not allowed"):
            await upload_service.upload_file(mock_file)

    @pytest.mark.asyncio
    async def test_upload_generates_unique_file_id(self, upload_service):
        """Test that each upload generates a unique file ID"""
        mock_file1 = MockUploadFile("file1.pdf", b"Content 1")
        mock_file2 = MockUploadFile("file2.pdf", b"Content 2")

        metadata1 = await upload_service.upload_file(mock_file1)
        metadata2 = await upload_service.upload_file(mock_file2)

        assert metadata1["file_id"] != metadata2["file_id"]

    @pytest.mark.asyncio
    async def test_upload_stores_metadata(self, upload_service):
        """Test that upload stores metadata in service"""
        mock_file = MockUploadFile("test.pdf", b"Test content")

        metadata = await upload_service.upload_file(mock_file)
        file_id = metadata["file_id"]

        # Check metadata is stored
        assert file_id in upload_service.file_metadata
        assert upload_service.file_metadata[file_id] == metadata

    @pytest.mark.asyncio
    async def test_upload_preserves_file_extension(self, upload_service):
        """Test that uploaded file preserves extension"""
        mock_file = MockUploadFile("document.pdf", b"PDF content")

        metadata = await upload_service.upload_file(mock_file)

        stored_filename = metadata["stored_filename"]
        assert stored_filename.endswith(".pdf")

    @pytest.mark.asyncio
    async def test_upload_includes_timestamp(self, upload_service):
        """Test that metadata includes upload timestamp"""
        mock_file = MockUploadFile("test.pdf", b"Test content")

        metadata = await upload_service.upload_file(mock_file)

        assert "uploaded_at" in metadata
        # Verify timestamp is valid ISO format
        datetime.fromisoformat(metadata["uploaded_at"])

    @pytest.mark.asyncio
    async def test_upload_calculates_file_size(self, upload_service):
        """Test that upload calculates correct file size"""
        content = b"X" * 1000  # 1000 bytes
        mock_file = MockUploadFile("test.txt", content)

        metadata = await upload_service.upload_file(mock_file)

        assert metadata["file_size"] == 1000


@pytest.mark.unit
@pytest.mark.services
class TestFileUploadServiceGetFilePath:
    """Tests for get_file_path method"""

    @pytest.fixture
    def upload_service(self, temp_dir):
        """Create FileUploadService instance"""
        return FileUploadService(upload_dir=temp_dir)

    @pytest.mark.asyncio
    async def test_get_file_path_existing_file(self, upload_service):
        """Test getting file path for existing file"""
        mock_file = MockUploadFile("test.pdf", b"Content")
        metadata = await upload_service.upload_file(mock_file)
        file_id = metadata["file_id"]

        file_path = upload_service.get_file_path(file_id)

        assert file_path == metadata["file_path"]
        assert os.path.exists(file_path)

    def test_get_file_path_nonexistent_file(self, upload_service):
        """Test getting file path for non-existent file returns None"""
        file_path = upload_service.get_file_path("nonexistent-id")
        assert file_path is None


@pytest.mark.unit
@pytest.mark.services
class TestFileUploadServiceGetMetadata:
    """Tests for get_file_metadata method"""

    @pytest.fixture
    def upload_service(self, temp_dir):
        """Create FileUploadService instance"""
        return FileUploadService(upload_dir=temp_dir)

    @pytest.mark.asyncio
    async def test_get_metadata_existing_file(self, upload_service):
        """Test getting metadata for existing file"""
        mock_file = MockUploadFile("test.pdf", b"Content")
        uploaded_metadata = await upload_service.upload_file(mock_file)
        file_id = uploaded_metadata["file_id"]

        metadata = upload_service.get_file_metadata(file_id)

        assert metadata == uploaded_metadata
        assert metadata["file_id"] == file_id

    def test_get_metadata_nonexistent_file(self, upload_service):
        """Test getting metadata for non-existent file returns None"""
        metadata = upload_service.get_file_metadata("nonexistent-id")
        assert metadata is None


@pytest.mark.unit
@pytest.mark.services
class TestFileUploadServiceDeleteFile:
    """Tests for delete_file method"""

    @pytest.fixture
    def upload_service(self, temp_dir):
        """Create FileUploadService instance"""
        return FileUploadService(upload_dir=temp_dir)

    @pytest.mark.asyncio
    async def test_delete_existing_file(self, upload_service):
        """Test deleting an existing file"""
        mock_file = MockUploadFile("test.pdf", b"Content")
        metadata = await upload_service.upload_file(mock_file)
        file_id = metadata["file_id"]
        file_path = metadata["file_path"]

        # Verify file exists
        assert os.path.exists(file_path)

        # Delete file
        result = upload_service.delete_file(file_id)

        assert result is True
        # Check file is deleted
        assert not os.path.exists(file_path)
        # Check metadata is removed
        assert file_id not in upload_service.file_metadata

    def test_delete_nonexistent_file(self, upload_service):
        """Test deleting non-existent file returns False"""
        result = upload_service.delete_file("nonexistent-id")
        assert result is False

    @pytest.mark.asyncio
    async def test_delete_removes_metadata(self, upload_service):
        """Test that delete removes file metadata"""
        mock_file = MockUploadFile("test.pdf", b"Content")
        metadata = await upload_service.upload_file(mock_file)
        file_id = metadata["file_id"]

        upload_service.delete_file(file_id)

        # Metadata should be removed
        assert upload_service.get_file_metadata(file_id) is None


@pytest.mark.unit
@pytest.mark.services
class TestFileUploadServiceGetUploadDirectory:
    """Tests for get_upload_directory method"""

    def test_get_upload_directory(self, temp_dir):
        """Test getting upload directory path"""
        upload_dir = os.path.join(temp_dir, "uploads")
        service = FileUploadService(upload_dir=upload_dir)

        result = service.get_upload_directory()

        assert result == os.path.abspath(upload_dir)


@pytest.mark.unit
@pytest.mark.services
class TestFileUploadServiceCleanupOldFiles:
    """Tests for cleanup_old_files method"""

    @pytest.fixture
    def upload_service(self, temp_dir):
        """Create FileUploadService instance"""
        return FileUploadService(upload_dir=temp_dir)

    @pytest.mark.asyncio
    async def test_cleanup_old_files(self, upload_service):
        """Test cleaning up old files"""
        # Upload a file
        mock_file = MockUploadFile("old.pdf", b"Old content")
        metadata = await upload_service.upload_file(mock_file)
        file_id = metadata["file_id"]

        # Manually set upload time to 25 hours ago
        old_time = datetime.utcnow() - timedelta(hours=25)
        upload_service.file_metadata[file_id]["uploaded_at"] = old_time.isoformat()

        # Run cleanup (default 24 hours)
        upload_service.cleanup_old_files(max_age_hours=24)

        # File should be deleted
        assert file_id not in upload_service.file_metadata

    @pytest.mark.asyncio
    async def test_cleanup_keeps_recent_files(self, upload_service):
        """Test that cleanup keeps recent files"""
        # Upload a file
        mock_file = MockUploadFile("recent.pdf", b"Recent content")
        metadata = await upload_service.upload_file(mock_file)
        file_id = metadata["file_id"]

        # Run cleanup
        upload_service.cleanup_old_files(max_age_hours=24)

        # File should still exist
        assert file_id in upload_service.file_metadata

    @pytest.mark.asyncio
    async def test_cleanup_with_custom_max_age(self, upload_service):
        """Test cleanup with custom max age"""
        # Upload a file
        mock_file = MockUploadFile("test.pdf", b"Content")
        metadata = await upload_service.upload_file(mock_file)
        file_id = metadata["file_id"]

        # Set upload time to 2 hours ago
        old_time = datetime.utcnow() - timedelta(hours=2)
        upload_service.file_metadata[file_id]["uploaded_at"] = old_time.isoformat()

        # Run cleanup with 1 hour max age
        upload_service.cleanup_old_files(max_age_hours=1)

        # File should be deleted
        assert file_id not in upload_service.file_metadata

    @pytest.mark.asyncio
    async def test_cleanup_multiple_files(self, upload_service):
        """Test cleanup with multiple files of different ages"""
        # Upload old file
        old_file = MockUploadFile("old.pdf", b"Old")
        old_metadata = await upload_service.upload_file(old_file)
        old_id = old_metadata["file_id"]

        # Upload recent file
        recent_file = MockUploadFile("recent.pdf", b"Recent")
        recent_metadata = await upload_service.upload_file(recent_file)
        recent_id = recent_metadata["file_id"]

        # Set old file time
        old_time = datetime.utcnow() - timedelta(hours=25)
        upload_service.file_metadata[old_id]["uploaded_at"] = old_time.isoformat()

        # Run cleanup
        upload_service.cleanup_old_files(max_age_hours=24)

        # Old file deleted, recent file kept
        assert old_id not in upload_service.file_metadata
        assert recent_id in upload_service.file_metadata

    def test_cleanup_on_empty_service(self, upload_service):
        """Test cleanup on service with no files"""
        # Should not raise any error
        upload_service.cleanup_old_files(max_age_hours=24)

        assert len(upload_service.file_metadata) == 0


@pytest.mark.unit
@pytest.mark.services
class TestFileUploadServiceIntegration:
    """Integration tests for FileUploadService"""

    @pytest.fixture
    def upload_service(self, temp_dir):
        """Create FileUploadService instance"""
        return FileUploadService(upload_dir=temp_dir)

    @pytest.mark.asyncio
    async def test_complete_upload_workflow(self, upload_service):
        """Test complete upload, retrieve, and delete workflow"""
        # Upload file
        mock_file = MockUploadFile("workflow.pdf", b"Workflow content")
        metadata = await upload_service.upload_file(mock_file)
        file_id = metadata["file_id"]

        # Verify file exists
        file_path = upload_service.get_file_path(file_id)
        assert file_path is not None
        assert os.path.exists(file_path)

        # Get metadata
        retrieved_metadata = upload_service.get_file_metadata(file_id)
        assert retrieved_metadata == metadata

        # Delete file
        delete_result = upload_service.delete_file(file_id)
        assert delete_result is True

        # Verify file is gone
        assert not os.path.exists(file_path)
        assert upload_service.get_file_path(file_id) is None
        assert upload_service.get_file_metadata(file_id) is None

    @pytest.mark.asyncio
    async def test_upload_multiple_files(self, upload_service):
        """Test uploading multiple files"""
        files = [
            MockUploadFile("file1.pdf", b"Content 1"),
            MockUploadFile("file2.txt", b"Content 2"),
            MockUploadFile("file3.png", b"Content 3"),
        ]

        file_ids = []
        for mock_file in files:
            metadata = await upload_service.upload_file(mock_file)
            file_ids.append(metadata["file_id"])

        # All files should be in metadata
        assert len(upload_service.file_metadata) == 3
        for file_id in file_ids:
            assert file_id in upload_service.file_metadata

import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock, call
import time
import sys

# Mock modules
sys.modules['custom_modules'] = Mock()

from zip_processor import (
    run_once_scan,
    FileProcessor,
    ProcessingResult,
    ProcessingStatus,
    ProcessingMode,
    ScanSummary,
    _process_sequential,
    _process_parallel,
    _update_summary_with_result,
    _log_scan_summary
)


# COMMENT: Test Fixtures
@pytest.fixture
def temp_dirs():
    """Tạo thư mục tạm cho test với cấu trúc đầy đủ"""
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        incoming = base / "incoming"
        saved = base / "saved"
        failed = base / "incoming" / "failed"
        processing = base / "incoming" / "processing"
        
        incoming.mkdir(parents=True)
        saved.mkdir()
        failed.mkdir(parents=True)
        processing.mkdir(parents=True)
        
        yield {
            "base": base,
            "incoming": incoming,
            "saved": saved,
            "failed": failed,
            "processing": processing
        }


@pytest.fixture
def mock_zip_files(temp_dirs):
    """Tạo nhiều mock ZIP files với các kịch bản khác nhau"""
    files = []
    
    # File mới chưa xử lý
    new_file = temp_dirs["incoming"] / "new_file_202401.zip"
    new_file.write_bytes(b"new content")
    files.append(new_file)
    
    # File đã xử lý thành công
    processed_file = temp_dirs["incoming"] / "processed_202402.zip"
    processed_file.write_bytes(b"processed content")
    files.append(processed_file)
    
    # File bị lỗi
    error_file = temp_dirs["incoming"] / "error_file_202403.zip"
    error_file.write_bytes(b"error content")
    files.append(error_file)
    
    # File snapshot
    snapshot_file = temp_dirs["incoming"] / "snapshot_202404.zip"
    snapshot_file.write_bytes(b"snapshot content")
    files.append(snapshot_file)
    
    return files


@pytest.fixture
def mock_fs_config(temp_dirs):
    """Tạo mock FSConfig"""
    config = Mock()
    config.incoming_dir = temp_dirs["incoming"]
    config.saved_dir = temp_dirs["saved"]
    return config


@pytest.fixture
def mock_pg_config():
    """Tạo mock PostgresConfig"""
    config = Mock()
    return config


@pytest.fixture
def file_processor(mock_fs_config, mock_pg_config):
    """Tạo FileProcessor instance cho test"""
    return FileProcessor(
        fs_cfg=mock_fs_config,
        pg_cfg=mock_pg_config,
        staging_schema="test_staging",
        prod_schema="test_public",
        ingest_schema="test_ingest",
        dedupe=True
    )


# COMMENT: Test ProcessingResult và ScanSummary
class TestDataClasses:
    """Test các data classes"""
    
    def test_processing_result_creation(self):
        """Test tạo ProcessingResult"""
        result = ProcessingResult(
            filename="test.zip",
            status=ProcessingStatus.SUCCESS,
            mode=ProcessingMode.MONTHLY,
            staging_rows=100,
            prod_rows=90,
            processing_time=1.5
        )
        
        assert result.filename == "test.zip"
        assert result.status == ProcessingStatus.SUCCESS
        assert result.mode == ProcessingMode.MONTHLY
        assert result.staging_rows == 100
        assert result.prod_rows == 90
        assert result.processing_time == 1.5
    
    def test_scan_summary_duration(self):
        """Test tính duration của ScanSummary"""
        import time
        from datetime import datetime
        
        start = datetime(2024, 1, 1, 0, 0, 0)
        end = datetime(2024, 1, 1, 0, 1, 30)  # 90 giây sau
        
        summary = ScanSummary(start_time=start)
        summary.end_time = end
        
        assert summary.duration == 90.0
    
    def test_scan_summary_to_dict(self):
        """Test chuyển ScanSummary sang dict"""
        summary = ScanSummary(
            total_scanned=10,
            total_to_process=5,
            processed=3,
            skipped=1,
            failed=1
        )
        
        summary.results.append(
            ProcessingResult(
                filename="test.zip",
                status=ProcessingStatus.SUCCESS,
                mode=ProcessingMode.MONTHLY,
                staging_rows=100,
                prod_rows=90
            )
        )
        
        result_dict = summary.to_dict()
        
        assert result_dict["total_scanned"] == 10
        assert result_dict["total_to_process"] == 5
        assert result_dict["processed"] == 3
        assert result_dict["skipped"] == 1
        assert result_dict["failed"] == 1
        assert len(result_dict["results"]) == 1


# COMMENT: Test FileProcessor
class TestFileProcessor:
    """Test class FileProcessor"""
    
    def test_ensure_directories(self, file_processor, temp_dirs):
        """Test tạo thư mục"""
        # Xóa thư mục để test tạo mới
        shutil.rmtree(temp_dirs["failed"])
        shutil.rmtree(temp_dirs["processing"])
        
        file_processor._ensure_directories()
        
        assert temp_dirs["failed"].exists()
        assert temp_dirs["processing"].exists()
    
    @patch('zip_processor.parse_zip_and_decide_names')
    @patch('zip_processor.has_success_log')
    def test_should_process_file_new(self, mock_has_log, mock_parse, file_processor, mock_zip_files):
        """Test kiểm tra file mới"""
        zip_path = mock_zip_files[0]
        
        mock_parse.return_value = {"mode": "monthly"}
        mock_has_log.return_value = (False, None)
        
        should_process, reason, _ = file_processor._should_process_file(zip_path)
        
        assert should_process is True
        assert reason == "new_file"
        mock_parse.assert_called_once_with(zip_path)
    
    @patch('zip_processor.parse_zip_and_decide_names')
    @patch('zip_processor.has_success_log')
    def test_should_process_file_updated(self, mock_has_log, mock_parse, file_processor, mock_zip_files):
        """Test kiểm tra file đã cập nhật"""
        zip_path = mock_zip_files[0]
        
        mock_parse.return_value = {"mode": "monthly"}
        mock_has_log.return_value = (True, 1234567890.0)  # Old mtime
        
        should_process, reason, logged_mtime = file_processor._should_process_file(zip_path)
        
        assert should_process is True
        assert reason == "file_updated"
        assert logged_mtime == 1234567890.0
    
    @patch('zip_processor.parse_zip_and_decide_names')
    @patch('zip_processor.has_success_log')
    def test_should_process_file_already_processed(self, mock_has_log, mock_parse, file_processor, mock_zip_files):
        """Test kiểm tra file đã xử lý"""
        zip_path = mock_zip_files[0]
        current_mtime = zip_path.stat().st_mtime
        
        mock_parse.return_value = {"mode": "monthly"}
        mock_has_log.return_value = (True, current_mtime)
        
        should_process, reason, _ = file_processor._should_process_file(zip_path)
        
        assert should_process is False
        assert reason == "already_processed"
    
    def test_move_to_processing(self, file_processor, mock_zip_files):
        """Test di chuyển file sang processing"""
        zip_path = mock_zip_files[0]
        
        processing_path = file_processor._move_to_processing(zip_path)
        
        assert not zip_path.exists()  # File gốc không còn
        assert processing_path.exists()  # File mới tồn tại
        assert processing_path.parent == file_processor.fs_cfg.incoming_dir / "processing"
    
    def test_move_to_processing_existing(self, file_processor, mock_zip_files, temp_dirs):
        """Test di chuyển file khi file đã tồn tại trong processing"""
        zip_path = mock_zip_files[0]
        
        # Tạo file trùng tên trong processing
        existing_file = temp_dirs["processing"] / zip_path.name
        existing_file.write_bytes(b"existing")
        
        processing_path = file_processor._move_to_processing(zip_path)
        
        # File mới phải có tên khác
        assert processing_path.name != zip_path.name
        assert "_" in processing_path.name  # Có timestamp
    
    def test_archive_file_success(self, file_processor, mock_zip_files):
        """Test archive file thành công"""
        zip_path = mock_zip_files[0]
        
        file_processor._archive_file(zip_path, success=True)
        
        saved_path = file_processor.fs_cfg.saved_dir / zip_path.name
        assert saved_path.exists()
        assert not zip_path.exists()  # File gốc bị xóa
    
    def test_archive_file_failed(self, file_processor, mock_zip_files, temp_dirs):
        """Test archive file thất bại"""
        zip_path = mock_zip_files[0]
        
        file_processor._archive_file(zip_path, success=False)
        
        failed_path = temp_dirs["failed"] / zip_path.name
        assert failed_path.exists()
    
    @patch('zip_processor.ingest_zip_job')
    def test_process_with_retry_success(self, mock_ingest, file_processor, mock_zip_files):
        """Test retry thành công ngay lần đầu"""
        zip_path = mock_zip_files[0]
        mock_ingest.return_value = {"success": True}
        
        result = file_processor._process_with_retry(zip_path, max_retries=2)
        
        assert result["success"] is True
        mock_ingest.assert_called_once()  # Chỉ gọi một lần
    
    @patch('zip_processor.ingest_zip_job')
    def test_process_with_retry_failure(self, mock_ingest, file_processor, mock_zip_files):
        """Test retry thất bại tất cả lần"""
        zip_path = mock_zip_files[0]
        mock_ingest.side_effect = Exception("Ingest failed")
        
        with pytest.raises(Exception, match="Ingest failed"):
            file_processor._process_with_retry(zip_path, max_retries=2)
        
        assert mock_ingest.call_count == 3  # 1 lần đầu + 2 retries
    
    @patch('zip_processor.parse_zip_and_decide_names')
    @patch('zip_processor.has_success_log')
    @patch('zip_processor.ingest_zip_job')
    def test_process_single_file_success(self, mock_ingest, mock_has_log, mock_parse, 
                                         file_processor, mock_zip_files):
        """Test xử lý file thành công"""
        zip_path = mock_zip_files[0]
        
        mock_parse.return_value = {"mode": "monthly"}
        mock_has_log.return_value = (False, None)
        mock_ingest.return_value = {"success": True, "staging_rows": 100, "prod_rows": 90}
        
        result = file_processor.process_single_file(zip_path, dry_run=False)
        
        assert result.status == ProcessingStatus.SUCCESS
        assert result.staging_rows == 100
        assert result.prod_rows == 90
        assert result.mode == ProcessingMode.MONTHLY
        assert result.processing_time > 0
    
    @patch('zip_processor.parse_zip_and_decide_names')
    @patch('zip_processor.has_success_log')
    def test_process_single_file_dry_run(self, mock_has_log, mock_parse, 
                                         file_processor, mock_zip_files):
        """Test dry run mode"""
        zip_path = mock_zip_files[0]
        
        mock_parse.return_value = {"mode": "snapshot"}
        mock_has_log.return_value = (False, None)
        
        result = file_processor.process_single_file(zip_path, dry_run=True)
        
        assert result.status == ProcessingStatus.SUCCESS
        assert result.mode == ProcessingMode.SNAPSHOT
        # Không gọi ingest_zip_job trong dry run


# COMMENT: Test helper functions
class TestHelperFunctions:
    """Test các helper functions"""
    
    def test_update_summary_with_result(self):
        """Test cập nhật summary"""
        summary = ScanSummary(total_to_process=5)
        
        # Test success
        result1 = ProcessingResult("file1.zip", ProcessingStatus.SUCCESS)
        _update_summary_with_result(summary, result1)
        assert summary.processed == 1
        
        # Test skipped
        result2 = ProcessingResult("file2.zip", ProcessingStatus.SKIPPED)
        _update_summary_with_result(summary, result2)
        assert summary.skipped == 1
        
        # Test failed
        result3 = ProcessingResult("file3.zip", ProcessingStatus.FAILED)
        _update_summary_with_result(summary, result3)
        assert summary.failed == 1
        
        assert len(summary.results) == 3
    
    @patch('zip_processor.logger')
    def test_log_scan_summary_no_files(self, mock_logger):
        """Test log summary khi không có file"""
        summary = ScanSummary()
        summary.end_time = datetime.now()
        
        _log_scan_summary(summary)
        
        # Kiểm tra log được gọi
        mock_logger.info.assert_called()
    
    @patch('zip_processor.logger')
    def test_log_scan_summary_with_failed(self, mock_logger):
        """Test log summary với file failed"""
        summary = ScanSummary(total_to_process=3, processed=1, skipped=1, failed=1)
        summary.end_time = datetime.now()
        
        failed_result = ProcessingResult(
            filename="failed.zip",
            status=ProcessingStatus.FAILED,
            error="Test error"
        )
        summary.results.append(failed_result)
        
        _log_scan_summary(summary)
        
        # Kiểm tra log warning cho failed files
        mock_logger.warning.assert_called()


# COMMENT: Test main function run_once_scan
class TestRunOnceScan:
    """Test hàm run_once_scan"""
    
    @patch('zip_processor.list_zip_files')
    @patch('zip_processor.filter_files_to_process')
    def test_run_once_scan_no_files(self, mock_filter, mock_list, 
                                    mock_fs_config, mock_pg_config):
        """Test khi không có file"""
        mock_list.return_value = []
        
        summary = run_once_scan(
            fs_cfg=mock_fs_config,
            pg_cfg=mock_pg_config
        )
        
        assert summary.total_scanned == 0
        assert summary.total_to_process == 0
        assert summary.end_time is not None
    
    @patch('zip_processor.list_zip_files')
    @patch('zip_processor.filter_files_to_process')
    @patch('zip_processor.FileProcessor')
    def test_run_once_scan_with_files(self, mock_processor_class, mock_filter, 
                                      mock_list, mock_fs_config, mock_pg_config, 
                                      mock_zip_files):
        """Test khi có file"""
        mock_list.return_value = mock_zip_files
        mock_filter.return_value = mock_zip_files[:2]  # Chỉ 2 file cần xử lý
        
        # Mock processor
        mock_processor = Mock()
        mock_processor_class.return_value = mock_processor
        
        # Mock process_single_file
        def side_effect(zip_path, dry_run):
            return ProcessingResult(
                filename=zip_path.name,
                status=ProcessingStatus.SUCCESS,
                processing_time=0.1
            )
        
        mock_processor.process_single_file.side_effect = side_effect
        
        summary = run_once_scan(
            fs_cfg=mock_fs_config,
            pg_cfg=mock_pg_config,
            max_workers=1
        )
        
        assert summary.total_scanned == 4
        assert summary.total_to_process == 2
        assert summary.processed == 2
        assert summary.end_time is not None
    
    @patch('zip_processor.list_zip_files')
    @patch('zip_processor.filter_files_to_process')
    @patch('zip_processor.FileProcessor')
    def test_run_once_scan_batch_size(self, mock_processor_class, mock_filter,
                                      mock_list, mock_fs_config, mock_pg_config,
                                      mock_zip_files):
        """Test với batch size limit"""
        mock_list.return_value = mock_zip_files
        mock_filter.return_value = mock_zip_files
        
        mock_processor = Mock()
        mock_processor_class.return_value = mock_processor
        
        def side_effect(zip_path, dry_run):
            return ProcessingResult(
                filename=zip_path.name,
                status=ProcessingStatus.SUCCESS
            )
        
        mock_processor.process_single_file.side_effect = side_effect
        
        summary = run_once_scan(
            fs_cfg=mock_fs_config,
            pg_cfg=mock_pg_config,
            batch_size=2
        )
        
        # Chỉ xử lý 2 file do batch size
        assert mock_processor.process_single_file.call_count == 2
    
    @patch('zip_processor.list_zip_files')
    def test_run_once_scan_exception(self, mock_list, mock_fs_config, mock_pg_config):
        """Test xử lý exception"""
        mock_list.side_effect = Exception("Scan failed")
        
        summary = run_once_scan(
            fs_cfg=mock_fs_config,
            pg_cfg=mock_pg_config
        )
        
        assert summary.failed > 0  # Đánh dấu failed khi có exception


# COMMENT: Integration tests
@pytest.mark.integration
class TestIntegration:
    """Integration tests"""
    
    @patch('zip_processor.FSConfig.from_env')
    @patch('zip_processor.PostgresConfig.from_env')
    @patch('zip_processor.list_zip_files')
    @patch('zip_processor.filter_files_to_process')
    def test_full_integration_dry_run(self, mock_filter, mock_list, 
                                      mock_pg_from_env, mock_fs_from_env,
                                      temp_dirs):
        """Test toàn bộ pipeline với dry run"""
        # Setup mocks
        mock_fs_config = Mock()
        mock_fs_config.incoming_dir = temp_dirs["incoming"]
        mock_fs_config.saved_dir = temp_dirs["saved"]
        mock_fs_from_env.return_value = mock_fs_config
        
        mock_pg_config = Mock()
        mock_pg_from_env.return_value = mock_pg_config
        
        # Tạo test files
        test_files = [
            temp_dirs["incoming"] / "file1.zip",
            temp_dirs["incoming"] / "file2.zip"
        ]
        
        for f in test_files:
            f.write_bytes(b"test")
        
        mock_list.return_value = test_files
        mock_filter.return_value = test_files
        
        # Chạy với dry run
        with patch('zip_processor.FileProcessor') as mock_processor_class:
            mock_processor = Mock()
            mock_processor_class.return_value = mock_processor
            
            mock_processor.process_single_file.return_value = ProcessingResult(
                filename="test.zip",
                status=ProcessingStatus.SUCCESS
            )
            
            summary = run_once_scan(dry_run=True)
            
            # Verify
            assert summary.total_scanned == 2
            mock_processor_class.assert_called_once()
    
    def test_processing_lifecycle(self, file_processor, mock_zip_files, temp_dirs):
        """Test toàn bộ vòng đời xử lý file"""
        zip_path = mock_zip_files[0]
        
        # Test move to processing
        with patch('zip_processor.parse_zip_and_decide_names') as mock_parse:
            with patch('zip_processor.has_success_log') as mock_has_log:
                with patch('zip_processor.ingest_zip_job') as mock_ingest:
                    # Setup
                    mock_parse.return_value = {"mode": "monthly"}
                    mock_has_log.return_value = (False, None)
                    mock_ingest.return_value = {"success": True}
                    
                    # Process file
                    result = file_processor.process_single_file(zip_path)
                    
                    # Verify
                    assert result.status == ProcessingStatus.SUCCESS
                    
                    # File nên được di chuyển và archive
                    processing_files = list(temp_dirs["processing"].iterdir())
                    saved_files = list(temp_dirs["saved"].iterdir())
                    
                    assert len(processing_files) == 0  # Đã được xóa sau khi archive
                    assert len(saved_files) == 1  # Đã được lưu


# COMMENT: Performance tests
@pytest.mark.performance
class TestPerformance:
    """Performance tests"""
    
    @patch('zip_processor.FileProcessor.process_single_file')
    def test_sequential_vs_parallel(self, mock_process, mock_fs_config, mock_pg_config):
        """Test so sánh tốc độ tuần tự vs song song"""
        import time
        from unittest.mock import patch
        
        # Tạo mock files
        num_files = 10
        mock_files = [Path(f"file{i}.zip") for i in range(num_files)]
        
        # Mock process mỗi file mất 0.1s
        def mock_processing(zip_path, dry_run):
            time.sleep(0.1)
            return ProcessingResult(
                filename=zip_path.name,
                status=ProcessingStatus.SUCCESS,
                processing_time=0.1
            )
        
        mock_process.side_effect = mock_processing
        
        # Test sequential
        start = time.time()
        
        processor = FileProcessor(
            fs_cfg=mock_fs_config,
            pg_cfg=mock_pg_config
        )
        
        for file_path in mock_files:
            processor.process_single_file(file_path)
        
        sequential_time = time.time() - start
        
        # Test parallel (simulated)
        # Note: Thực tế cần test với ThreadPoolExecutor thật
        
        logger.info(f"Sequential time for {num_files} files: {sequential_time:.2f}s")
        
        # Kiểm tra cơ bản
        assert mock_process.call_count == num_files


# COMMENT: Run all tests
if __name__ == "__main__":
    # Chạy tests với coverage
    import os
    import coverage
    
    cov = coverage.Coverage()
    cov.start()
    
    # Chạy pytest
    pytest.main([
        '-v',
        '--tb=short',
        '--cov=zip_processor',
        '--cov-report=term-missing',
        '--cov-report=html',
        '--cov-report=xml',
        '--junitxml=test-results.xml'
    ])
    
    cov.stop()
    cov.save()
    
    # Generate report
    cov.report()
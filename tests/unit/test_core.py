"""Unit tests for the core module.

This module contains tests for the core functionality of the CPU affinity manager.

"""

import sys

import psutil
import pytest
import win32api
import win32event
import win32ui
import winerror

from bas_set_cpu_affinity.core import (
    check_single_instance,
    handle_main_process,
    handle_worker_process,
    move_processes_from_main_cores,
    parse_core_string,
    set_affinities,
    validate_cores,
)


class TestParseCorString:
    """Tests for the parse_core_string function."""

    def test_valid_core_string(self):
        """Test parsing a valid core string."""
        result = parse_core_string("0-2-4")
        assert result == [0, 2, 4]

    def test_duplicate_cores(self):
        """Test parsing a core string with duplicate cores."""
        result = parse_core_string("0-0-1-2-1")
        assert result == [0, 1, 2]  # Should deduplicate and sort

    def test_empty_string(self):
        """Test parsing an empty string."""
        with pytest.raises(ValueError):
            parse_core_string("")

    def test_invalid_core_string(self):
        """Test parsing an invalid core string."""
        with pytest.raises(ValueError):
            parse_core_string("a-b-c")


class TestValidateCores:
    """Tests for the validate_cores function."""

    def test_valid_cores(self, monkeypatch):
        """Test validating cores within the system CPU count."""

        # Setup
        def mock_cpu_count():
            return 8

        monkeypatch.setattr(psutil, "cpu_count", mock_cpu_count)

        # Execute
        cores = [0, 2, 4, 7]
        result = validate_cores(cores)

        # Verify
        assert result == cores

    def test_cores_exceeding_count(self, monkeypatch):
        """Test validating cores that exceed the system CPU count."""

        # Setup
        def mock_cpu_count():
            return 4

        monkeypatch.setattr(psutil, "cpu_count", mock_cpu_count)

        # Execute and verify
        cores = [0, 2, 4, 7]
        with pytest.raises(ValueError):
            validate_cores(cores)

    def test_negative_cores(self, monkeypatch):
        """Test validating negative core numbers."""

        # Setup
        def mock_cpu_count():
            return 8

        monkeypatch.setattr(psutil, "cpu_count", mock_cpu_count)

        # Execute and verify
        cores = [0, -1, 2]
        with pytest.raises(ValueError):
            validate_cores(cores)


class TestHandleProcesses:
    """Tests for handle_main_process and handle_worker_process functions."""

    def test_handle_main_process_update_needed(self, mock_process):
        """Test handling a main process when affinity update is needed."""

        # Setup
        # Set initial affinity
        mock_process._affinity = [0, 1]  # pylint:disable=protected-access
        target_cores = [0, 2, 3]

        # Execute
        handle_main_process(mock_process, target_cores)

        # Verify
        assert len(mock_process.affinity_calls) == 2
        assert mock_process.affinity_calls[0] is None  # First call to get current affinity
        assert mock_process.affinity_calls[1] == target_cores  # Second call to set new affinity

    def test_handle_main_process_no_update(self, mock_process):
        """Test handling a main process when affinity is already correct."""

        # Setup
        # Set initial affinity
        target_cores = [0, 1]
        mock_process._affinity = target_cores  # pylint:disable=protected-access

        # Execute
        handle_main_process(mock_process, target_cores)

        # Verify
        assert len(mock_process.affinity_calls) == 1
        assert mock_process.affinity_calls[0] is None  # Only called to get current affinity

    def test_handle_worker_process_update_needed(self, mock_process):
        """Test handling a worker process when affinity update is needed."""

        # Setup

        # Set initial affinity
        mock_process._affinity = [0, 1]  # pylint:disable=protected-access
        target_cores = [2, 3]

        # Execute
        handle_worker_process(mock_process, target_cores)

        # Verify
        assert len(mock_process.affinity_calls) == 2
        assert mock_process.affinity_calls[0] is None  # First call to get current affinity
        assert mock_process.affinity_calls[1] == target_cores  # Second call to set new affinity

    def test_handle_worker_process_no_update(self, mock_process):
        """Test handling a worker process when affinity is already correct."""

        # Setup
        # Set initial affinity
        target_cores = [0, 1]
        mock_process._affinity = target_cores  # pylint:disable=protected-access

        # Execute
        handle_worker_process(mock_process, target_cores)

        # Verify
        assert len(mock_process.affinity_calls) == 1
        assert mock_process.affinity_calls[0] is None  # Only called to get current affinity


class TestMoveProcesses:
    """Tests for the move_processes_from_main_cores function."""

    def test_move_processes(self, monkeypatch):
        """Test moving processes from main cores to worker cores."""
        # Setup
        main_cores = [0, 1]
        worker_cores = [2, 3]
        main_names = ["main.exe"]

        # Create mock processes
        class MockProcess:
            def __init__(self, name, pid, initial_affinity=None):
                self.info = {"name": name, "pid": pid}
                self.pid = pid  # Add pid attribute for handle_main_process and handle_worker_process
                self._affinity = initial_affinity
                self.affinity_calls = []

            def cpu_affinity(self, new_affinity=None):
                self.affinity_calls.append(new_affinity)
                if new_affinity is not None:
                    self._affinity = new_affinity
                return self._affinity

        # Create mock processes
        main_process = MockProcess("main.exe", 1000, [0, 1])
        other_process = MockProcess("other.exe", 1001, [0, 1])
        system_process = MockProcess("System", 4)

        def mock_process_iter(*args, **kwargs):  # pylint:disable=unused-argument
            return [main_process, other_process, system_process]

        monkeypatch.setattr(psutil, "process_iter", mock_process_iter)

        # Execute
        move_processes_from_main_cores(main_cores, worker_cores, main_names)

        # Verify
        #  the Main process should be skipped without calling cpu_affinity
        assert len(main_process.affinity_calls) == 0

        # Another process should be moved
        assert len(other_process.affinity_calls) == 2
        assert other_process.affinity_calls[0] is None  # First call to get current affinity
        assert other_process.affinity_calls[1] == worker_cores  # Second call to set new affinity

        # System process should be skipped
        assert len(system_process.affinity_calls) == 0

    def test_no_worker_cores(self, monkeypatch):
        """Test when no worker cores are available."""
        # Setup
        main_cores = [0, 1, 2, 3]
        worker_cores = []

        process_iter_called = False

        def mock_process_iter(*args, **kwargs):  # pylint:disable=unused-argument
            nonlocal process_iter_called
            process_iter_called = True
            return []

        monkeypatch.setattr(psutil, "process_iter", mock_process_iter)

        # Execute
        move_processes_from_main_cores(main_cores, worker_cores)

        # Verify
        assert not process_iter_called  # Should exit early


class TestSetAffinities:
    """Tests for the set_affinities function."""

    def test_set_affinities(self, monkeypatch):
        """Test setting affinities for main and worker processes."""
        # Setup
        main_names = ["main.exe"]
        worker_names = ["worker.exe"]
        main_cores = [0, 1]
        worker_cores = [2, 3]

        # Create mock processes
        class MockProcess:
            def __init__(self, name, pid):
                self.info = {"name": name, "pid": pid}

        # Create mock processes
        main_process = MockProcess("main.exe", 1000)
        worker_process = MockProcess("worker.exe", 1001)
        other_process = MockProcess("other.exe", 1002)

        def mock_process_iter(*args, **kwargs):  # pylint:disable=unused-argument
            return [main_process, worker_process, other_process]

        # Track calls to handle_main_process and handle_worker_process
        handle_main_calls = []
        handle_worker_calls = []

        def mock_handle_main_process(proc, cores):
            handle_main_calls.append((proc, cores))

        def mock_handle_worker_process(proc, cores):
            handle_worker_calls.append((proc, cores))

        monkeypatch.setattr(psutil, "process_iter", mock_process_iter)
        monkeypatch.setattr("bas_set_cpu_affinity.core.handle_main_process", mock_handle_main_process)
        monkeypatch.setattr("bas_set_cpu_affinity.core.handle_worker_process", mock_handle_worker_process)

        # Execute
        main_found, worker_found = set_affinities(main_names, worker_names, main_cores, worker_cores)

        # Verify
        assert main_found is True
        assert worker_found is True
        assert len(handle_main_calls) == 1
        assert handle_main_calls[0][0] == main_process
        assert handle_main_calls[0][1] == main_cores
        assert len(handle_worker_calls) == 1
        assert handle_worker_calls[0][0] == worker_process
        assert handle_worker_calls[0][1] == worker_cores

    def test_no_processes_found(self, monkeypatch):
        """Test when no matching processes are found."""
        # Setup
        main_names = ["nonexistent.exe"]
        worker_names = ["alsonotfound.exe"]
        main_cores = [0, 1]
        worker_cores = [2, 3]

        # Create mock processes with non-matching names
        class MockProcess:
            def __init__(self, name, pid):
                self.info = {"name": name, "pid": pid}

        process = MockProcess("other.exe", 1000)

        def mock_process_iter(*args, **kwargs):  # pylint:disable=unused-argument
            return [process]

        # Track calls to handle_main_process and handle_worker_process
        handle_main_called = False
        handle_worker_called = False

        def mock_handle_main_process(proc, cores):  # pylint:disable=unused-argument
            nonlocal handle_main_called
            handle_main_called = True

        def mock_handle_worker_process(proc, cores):  # pylint:disable=unused-argument
            nonlocal handle_worker_called
            handle_worker_called = True

        monkeypatch.setattr(psutil, "process_iter", mock_process_iter)
        monkeypatch.setattr("bas_set_cpu_affinity.core.handle_main_process", mock_handle_main_process)
        monkeypatch.setattr("bas_set_cpu_affinity.core.handle_worker_process", mock_handle_worker_process)

        # Execute
        main_found, worker_found = set_affinities(main_names, worker_names, main_cores, worker_cores)

        # Verify
        assert main_found is False
        assert worker_found is False
        assert not handle_main_called
        assert not handle_worker_called


class TestCheckSingleInstance:
    """Tests for the check_single_instance function."""

    def test_no_other_instance(self, monkeypatch):
        """Test when no other instance is running."""
        # Setup
        create_mutex_called = False
        get_last_error_called = False

        def mock_create_mutex(*args, **kwargs):  # pylint:disable=unused-argument
            nonlocal create_mutex_called
            create_mutex_called = True
            return "mock_mutex"

        def mock_get_last_error():
            nonlocal get_last_error_called
            get_last_error_called = True
            return 0  # No error

        monkeypatch.setattr(win32event, "CreateMutex", mock_create_mutex)
        monkeypatch.setattr(win32api, "GetLastError", mock_get_last_error)

        # Execute
        result = check_single_instance()

        # Verify
        assert result == "mock_mutex"
        assert create_mutex_called
        assert get_last_error_called

    def test_other_instance_running(self, monkeypatch):
        """Test when another instance is already running."""
        # Setup
        create_mutex_called = False
        get_last_error_called = False
        message_box_called = False
        exit_called = False

        def mock_create_mutex(*args, **kwargs):  # pylint:disable=unused-argument
            nonlocal create_mutex_called
            create_mutex_called = True
            return "mock_mutex"

        def mock_get_last_error():
            nonlocal get_last_error_called
            get_last_error_called = True
            return winerror.ERROR_ALREADY_EXISTS

        def mock_message_box(*args, **kwargs):  # pylint:disable=unused-argument
            nonlocal message_box_called
            message_box_called = True

        def mock_exit(code):
            nonlocal exit_called
            exit_called = True
            assert code == 1
            # Raise an exception to prevent actual exit
            raise RuntimeError("Exit called")

        monkeypatch.setattr(win32event, "CreateMutex", mock_create_mutex)
        monkeypatch.setattr(win32api, "GetLastError", mock_get_last_error)
        monkeypatch.setattr(win32ui, "MessageBox", mock_message_box)
        monkeypatch.setattr(sys, "exit", mock_exit)

        # Execute
        # The RuntimeError might be caught by the try-except block in check_single_instance
        # So we'll check if exit was called instead
        check_single_instance()

        # Verify
        assert create_mutex_called
        assert get_last_error_called
        assert message_box_called
        assert exit_called  # This is the key assertion - sys.exit should have been called

    def test_exception_handling(self, monkeypatch):
        """Test handling of exceptions during mutex creation."""
        # Setup
        message_box_called = False

        def mock_create_mutex(*args, **kwargs):  # pylint:disable=unused-argument
            raise Exception("Test exception")  # # pylint:disable=broad-exception-raised

        def mock_message_box(*args, **kwargs):  # pylint:disable=unused-argument
            nonlocal message_box_called
            message_box_called = True

        monkeypatch.setattr(win32event, "CreateMutex", mock_create_mutex)
        monkeypatch.setattr(win32ui, "MessageBox", mock_message_box)

        # Execute
        result = check_single_instance()

        # Verify
        assert result is None
        assert message_box_called

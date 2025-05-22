"""Functional tests for the CPU affinity management application.

This module contains tests that verify the application works correctly as a whole.

"""

import sys

import psutil
import pytest

from bas_set_cpu_affinity.cli import main
from bas_set_cpu_affinity.core import set_affinities


class TestCLIEntryPoint:
    """Tests for the CLI entry point."""

    def test_cli_entry_point(self, monkeypatch):
        """Test that the CLI entry point correctly calls the main function."""
        # Setup
        check_single_instance_called = False
        manage_affinity_called = False

        def mock_check_single_instance():
            nonlocal check_single_instance_called
            check_single_instance_called = True
            return "mock_mutex"

        def mock_manage_affinity():
            nonlocal manage_affinity_called
            manage_affinity_called = True

        monkeypatch.setattr("bas_set_cpu_affinity.cli.check_single_instance", mock_check_single_instance)
        monkeypatch.setattr("bas_set_cpu_affinity.cli.manage_affinity", mock_manage_affinity)
        monkeypatch.setattr(sys, "argv", ["set-cpu-affinity"])

        # Execute
        main()

        # Verify
        assert check_single_instance_called
        assert manage_affinity_called


class TestProcessAffinitySetting:
    """Tests for process affinity setting."""

    def test_process_affinity_setting(self, monkeypatch):
        """Test that process affinities are correctly set."""
        # Setup
        main_names = ["main.exe"]
        worker_names = ["worker.exe"]
        main_cores = [0, 1]
        worker_cores = [2, 3]

        # Create mock processes
        class MockProcess:
            def __init__(self, name, pid, initial_affinity):
                self.info = {"name": name, "pid": pid}
                self._affinity = initial_affinity
                self.affinity_calls = []

            def cpu_affinity(self, new_affinity=None):
                if new_affinity is not None:
                    self._affinity = new_affinity
                    self.affinity_calls.append(new_affinity)
                return self._affinity

        # Create mock processes
        main_process = MockProcess("main.exe", 1000, [0, 2])
        worker_process = MockProcess("worker.exe", 1001, [1, 3])

        # Track process_iter calls
        process_iter_called = False

        def mock_process_iter(*args, **kwargs):
            nonlocal process_iter_called
            process_iter_called = True
            print(f"process_iter called with args: {args}, kwargs: {kwargs}")
            print(f"Returning processes: {[p.info['name'] for p in [main_process, worker_process]]}")
            return [main_process, worker_process]

        # Track handle_main_process and handle_worker_process calls
        handle_main_called = False
        handle_worker_called = False

        def mock_handle_main_process(proc, cores):
            nonlocal handle_main_called
            handle_main_called = True
            print(f"handle_main_process called with proc: {proc.info['name']}, cores: {cores}")
            # Call the real implementation
            current = proc.cpu_affinity()
            if sorted(current) != cores:
                proc.cpu_affinity(cores)

        def mock_handle_worker_process(proc, cores):
            nonlocal handle_worker_called
            handle_worker_called = True
            print(f"handle_worker_process called with proc: {proc.info['name']}, cores: {cores}")
            # Call the real implementation
            current = proc.cpu_affinity()
            if sorted(current) != cores:
                proc.cpu_affinity(cores)

        monkeypatch.setattr(psutil, "process_iter", mock_process_iter)
        monkeypatch.setattr("bas_set_cpu_affinity.core.handle_main_process", mock_handle_main_process)
        monkeypatch.setattr("bas_set_cpu_affinity.core.handle_worker_process", mock_handle_worker_process)

        # Execute
        main_found, worker_found = set_affinities(main_names, worker_names, main_cores, worker_cores)

        # Verify
        print(f"process_iter_called: {process_iter_called}")
        print(f"handle_main_called: {handle_main_called}")
        print(f"handle_worker_called: {handle_worker_called}")
        print(f"main_found: {main_found}, worker_found: {worker_found}")

        assert process_iter_called
        assert handle_main_called
        assert handle_worker_called
        assert main_found is True
        assert worker_found is True

        # Check that affinities were set correctly
        assert main_cores in main_process.affinity_calls
        assert worker_cores in worker_process.affinity_calls


class TestContinuousMonitoring:
    """Tests for continuous monitoring functionality."""

    def test_continuous_monitoring(self, monkeypatch):
        """Test that the application continuously monitors and adjusts process affinities."""
        # Setup
        import time  # pylint:disable=import-outside-toplevel

        from click.testing import CliRunner  # pylint:disable=import-outside-toplevel

        from bas_set_cpu_affinity.cli import manage_affinity  # pylint:disable=import-outside-toplevel

        runner = CliRunner()

        # Create counters to track calls
        move_processes_call_count = 0
        set_affinities_call_count = 0
        sleep_call_count = 0

        # Create mock functions with side effects
        def mock_move_processes_from_main_cores(*args, **kwargs):  # pylint:disable=unused-argument
            nonlocal move_processes_call_count
            move_processes_call_count += 1

        def mock_set_affinities(*args, **kwargs):  # pylint:disable=unused-argument
            nonlocal set_affinities_call_count
            set_affinities_call_count += 1

            # Simulate different return values based on call count
            if set_affinities_call_count == 1:
                return (True, True)  # First check: both main and worker processes found
            if set_affinities_call_count == 2:
                return (False, False)  # Second check: no processes found
            if set_affinities_call_count == 3:
                return (True, False)  # Third check: only the main process found
            if set_affinities_call_count == 4:
                return (False, True)  # Fourth check: only worker process found

            raise KeyboardInterrupt  # Exit the loop

        def mock_sleep(seconds):  # pylint:disable=unused-argument
            nonlocal sleep_call_count
            sleep_call_count += 1

        # Apply the monkeypatches
        monkeypatch.setattr(
            "bas_set_cpu_affinity.cli.move_processes_from_main_cores", mock_move_processes_from_main_cores
        )
        monkeypatch.setattr("bas_set_cpu_affinity.cli.set_affinities", mock_set_affinities)
        monkeypatch.setattr(time, "sleep", mock_sleep)

        # Execute
        result = runner.invoke(manage_affinity, ["0-1"])

        # Verify
        assert result.exit_code == 0
        assert set_affinities_call_count == 5
        assert sleep_call_count == 4  # Should sleep after each check except the last one

        # Should have called move_processes_from_main_cores once at startup
        assert move_processes_call_count == 1


@pytest.mark.skipif(sys.platform != "win32", reason="Windows-specific test")
class TestRealProcesses:
    """Tests that interact with real processes (Windows only)."""

    def test_current_process_affinity(self):
        """Test that we can get and set the affinity of the current process."""
        # This test only runs on Windows and interacts with real processes

        # Get the current process
        current_process = psutil.Process()

        # Get the current affinity
        original_affinity = current_process.cpu_affinity()

        try:
            # Set a new affinity (using only the first CPU)
            new_affinity = [0]
            current_process.cpu_affinity(new_affinity)

            # Verify the affinity was set
            assert current_process.cpu_affinity() == new_affinity

        finally:
            # Restore the original affinity
            current_process.cpu_affinity(original_affinity)

            # Verify it was restored
            assert current_process.cpu_affinity() == original_affinity

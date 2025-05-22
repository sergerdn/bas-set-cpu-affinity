"""Unit tests for the CLI module.

This module contains tests for the command-line interface functionality.

"""

import time

import click
import psutil
import pytest
from click.testing import CliRunner

from bas_set_cpu_affinity.cli import (
    calculate_default_main_cores,
    main,
    manage_affinity,
    validate_cores_callback,
)


class TestCalculateDefaultMainCores:
    """Tests for the calculate_default_main_cores function."""

    def test_small_cpu_count(self, monkeypatch):
        """Test with a small CPU count (4 or fewer cores)."""

        # Setup
        def mock_cpu_count():
            return 4

        monkeypatch.setattr(psutil, "cpu_count", mock_cpu_count)

        # Execute
        result = calculate_default_main_cores()

        # Verify
        assert result == [0]

    def test_medium_cpu_count(self, monkeypatch):
        """Test with a medium CPU count (5-8 cores)."""

        # Setup
        def mock_cpu_count():
            return 8

        monkeypatch.setattr(psutil, "cpu_count", mock_cpu_count)

        # Execute
        result = calculate_default_main_cores()

        # Verify
        assert result == [0, 1]

    def test_large_cpu_count(self, monkeypatch):
        """Test with a large CPU count (more than 8 cores)."""

        # Setup
        def mock_cpu_count():
            return 16

        monkeypatch.setattr(psutil, "cpu_count", mock_cpu_count)

        # Execute
        result = calculate_default_main_cores()

        # Verify
        assert result == [0, 1, 2, 3]  # 25% of 16 = 4 cores

    def test_very_large_cpu_count(self, monkeypatch):
        """Test with a very large CPU count (should cap at 4 cores)."""

        # Setup
        def mock_cpu_count():
            return 24

        monkeypatch.setattr(psutil, "cpu_count", mock_cpu_count)

        # Execute
        result = calculate_default_main_cores()

        # Verify
        assert result == [0, 1, 2, 3]  # Should cap at 4 cores


class TestValidateCoresCallback:
    """Tests for the validate_cores_callback function."""

    def test_valid_core_string(self, monkeypatch):
        """Test with a valid core string."""
        # Setup

        parse_core_string_called = False
        validate_cores_called = False

        def mock_parse_core_string(value):
            nonlocal parse_core_string_called
            parse_core_string_called = True
            assert value == "0-2-4"
            return [0, 2, 4]

        def mock_validate_cores(cores):
            nonlocal validate_cores_called
            validate_cores_called = True
            assert cores == [0, 2, 4]
            return cores

        monkeypatch.setattr("bas_set_cpu_affinity.cli.parse_core_string", mock_parse_core_string)
        monkeypatch.setattr("bas_set_cpu_affinity.cli.validate_cores", mock_validate_cores)

        # Execute
        result = validate_cores_callback(None, None, "0-2-4")

        # Verify
        assert result == [0, 2, 4]
        assert parse_core_string_called
        assert validate_cores_called

    def test_invalid_core_string(self, monkeypatch):
        """Test with an invalid core string."""

        # Setup
        def mock_parse_core_string(value):
            assert value == "invalid"
            raise ValueError("Invalid core format")

        monkeypatch.setattr("bas_set_cpu_affinity.cli.parse_core_string", mock_parse_core_string)

        # Execute and verify
        with pytest.raises(click.BadParameter):
            validate_cores_callback(None, None, "invalid")

    def test_none_value(self, monkeypatch):
        """Test with None value (should use default cores)."""
        # Setup
        calculate_default_main_cores_called = False

        def mock_calculate_default_main_cores():
            nonlocal calculate_default_main_cores_called
            calculate_default_main_cores_called = True
            return [0, 1]

        monkeypatch.setattr("bas_set_cpu_affinity.cli.calculate_default_main_cores", mock_calculate_default_main_cores)

        # Execute
        result = validate_cores_callback(None, None, None)

        # Verify
        assert result == [0, 1]
        assert calculate_default_main_cores_called


class TestManageAffinity:
    """Tests for the manage_affinity function."""

    def test_basic_functionality(self, monkeypatch):
        """Test basic functionality with default arguments."""
        # Setup
        runner = CliRunner()

        # Create counters to track calls
        move_processes_call_count = 0
        set_affinities_call_count = 0
        sleep_call_count = 0

        # Create mock functions with side effects
        def mock_move_processes_from_main_cores(*args, **kwargs):  # pylint:disable=unused-argument
            nonlocal move_processes_call_count
            move_processes_call_count += 1
            return args[1]  # Return worker_cores for later assertions

        def mock_set_affinities(*args, **kwargs):  # pylint:disable=unused-argument
            nonlocal set_affinities_call_count
            set_affinities_call_count += 1

            if set_affinities_call_count == 1:
                return (True, True)  # The first call returns processes found

            raise KeyboardInterrupt  # The second call raises KeyboardInterrupt to exit loop

        def mock_sleep(seconds):  # pylint:disable=unused-argument
            nonlocal sleep_call_count
            sleep_call_count += 1

        # Apply the monkey patches
        monkeypatch.setattr(
            "bas_set_cpu_affinity.cli.move_processes_from_main_cores", mock_move_processes_from_main_cores
        )
        monkeypatch.setattr("bas_set_cpu_affinity.cli.set_affinities", mock_set_affinities)
        monkeypatch.setattr(time, "sleep", mock_sleep)

        # Execute
        result = runner.invoke(manage_affinity, ["0-1"])

        # Verify
        assert result.exit_code == 0
        assert move_processes_call_count == 1
        assert set_affinities_call_count > 0
        assert sleep_call_count > 0

    def test_with_custom_options(self, monkeypatch):
        """Test with custom interval and process names."""
        # Setup
        runner = CliRunner()

        # Create variables to track calls and arguments
        move_processes_args = None
        set_affinities_args = ([], [], [])  # Initialize with empty lists
        sleep_seconds = None

        # Create mock functions with side effects
        def mock_move_processes_from_main_cores(*args, **kwargs):  # pylint:disable=unused-argument
            nonlocal move_processes_args
            move_processes_args = args
            return args[1]  # Return worker_cores for later assertions

        def mock_set_affinities(*args, **kwargs):  # pylint:disable=unused-argument
            nonlocal set_affinities_args
            # Store args as a tuple of lists to ensure it's subscriptable
            set_affinities_args = (
                args[0] if isinstance(args[0], list) else [args[0]],
                args[1] if isinstance(args[1], list) else [args[1]],
                args[2] if isinstance(args[2], list) else [args[2]],
            )

            if not hasattr(mock_set_affinities, "called"):
                mock_set_affinities.called = True
                return (True, True)  # The first call returns processes found

            raise KeyboardInterrupt  # The second call raises KeyboardInterrupt to exit loop

        def mock_sleep(seconds):
            nonlocal sleep_seconds
            sleep_seconds = seconds

        # Apply the monkeypatches
        monkeypatch.setattr(
            "bas_set_cpu_affinity.cli.move_processes_from_main_cores", mock_move_processes_from_main_cores
        )
        monkeypatch.setattr("bas_set_cpu_affinity.cli.set_affinities", mock_set_affinities)
        monkeypatch.setattr(time, "sleep", mock_sleep)

        # Execute
        result = runner.invoke(
            manage_affinity,
            [
                "0-1",
                "--interval",
                "5",
                "--main-name",
                "custom.exe",
                "--workers",
                "worker1.exe,worker2.exe",
                "--verbose",
            ],
        )

        # Verify
        assert result.exit_code == 0
        assert move_processes_args is not None
        assert set_affinities_args is not None
        assert set_affinities_args[0] == ["custom.exe"]  # main_names
        assert set_affinities_args[1] == ["worker1.exe", "worker2.exe"]  # worker_names
        assert set_affinities_args[2] == [0, 1]  # main_cores
        assert sleep_seconds == 5.0

    def test_no_worker_cores(self, monkeypatch):
        """Test when no cores are available for worker processes."""
        # Setup
        runner = CliRunner()

        def mock_cpu_count():
            return 4

        monkeypatch.setattr(psutil, "cpu_count", mock_cpu_count)

        # Execute
        result = runner.invoke(manage_affinity, ["0-1-2-3"])

        # Verify
        assert result.exit_code != 0  # Should exit with an error
        assert "Aborted!" in result.output  # Click.Abort() results in "Aborted!" output

    def test_no_processes_found(self, monkeypatch):
        """Test when no matching processes are found."""
        # Setup
        runner = CliRunner()

        # Create counters to track calls
        set_affinities_call_count = 0
        sleep_call_count = 0

        # Create mock functions with side effects
        def mock_move_processes_from_main_cores(*args, **kwargs):  # pylint:disable=unused-argument
            return args[1]  # Return worker_cores for later assertions

        def mock_set_affinities(*args, **kwargs):  # pylint:disable=unused-argument
            nonlocal set_affinities_call_count
            set_affinities_call_count += 1

            if set_affinities_call_count >= 6:
                raise KeyboardInterrupt  # Exit loop after 6 calls
            return (False, False)  # No processes found

        def mock_sleep(seconds):  # pylint:disable=unused-argument
            nonlocal sleep_call_count
            sleep_call_count += 1

        # Apply the monkey patches
        monkeypatch.setattr(
            "bas_set_cpu_affinity.cli.move_processes_from_main_cores", mock_move_processes_from_main_cores
        )
        monkeypatch.setattr("bas_set_cpu_affinity.cli.set_affinities", mock_set_affinities)
        monkeypatch.setattr(time, "sleep", mock_sleep)

        # Execute
        result = runner.invoke(manage_affinity, ["0-1"])

        # Verify
        assert result.exit_code == 0
        assert set_affinities_call_count >= 5
        assert sleep_call_count >= 5  # Should sleep after each check


class TestMain:
    """Tests for the main function."""

    def test_main_function(self, monkeypatch):
        """Test that the main function calls check_single_instance and manage_affinity."""
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

        # Execute
        main()

        # Verify
        assert check_single_instance_called
        assert manage_affinity_called

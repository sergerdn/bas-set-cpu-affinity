"""Pytest configuration and shared fixtures.

This module contains fixtures that can be shared across multiple test files.

"""

import pytest


@pytest.fixture
def mock_process():
    """Create a mock psutil.Process object.

    Returns:
        MockProcess: A mock Process object with customizable attributes.

    """

    class MockProcess:
        def __init__(self):
            self.info = {"name": "test_process.exe", "pid": 1000}
            self._affinity = [0, 1]
            self.affinity_calls = []
            self.pid = 1000  # Add pid attribute for handle_main_process and handle_worker_process

        def cpu_affinity(self, new_affinity=None):
            self.affinity_calls.append(new_affinity)
            if new_affinity is not None:
                self._affinity = new_affinity
            return self._affinity

    return MockProcess()


@pytest.fixture
def mock_process_iter():
    """Create a mock for psutil.process_iter.

    Returns:
        function: A mock process_iter function that returns a list of mock processes.

    """

    class MockProcess:
        def __init__(self, name, pid):
            self.info = {"name": name, "pid": pid}
            self._affinity = [0, 1]
            self.affinity_calls = []

        def cpu_affinity(self, new_affinity=None):
            self.affinity_calls.append(new_affinity)
            if new_affinity is not None:
                self._affinity = new_affinity
            return self._affinity

    # Create some default test processes
    processes = [
        MockProcess("System", 1),
        MockProcess("BrowserAutomationStudio.exe", 1000),
        MockProcess("worker.exe", 1001),
        MockProcess("chrome.exe", 1002),
    ]

    def mock_iter(*args, **kwargs):  # pylint:disable=unused-argument
        return processes

    return mock_iter


@pytest.fixture
def mock_cpu_count():
    """Create a mock for psutil.cpu_count.

    Returns:
        function: A mock cpu_count function that returns a configurable number of CPUs.

    """

    def mock_cpu_count():  # pylint:disable=redefined-outer-name
        return 8

    return mock_cpu_count


@pytest.fixture
def mock_win32_api():
    """Create mocks for Windows API functions.

    Returns:
        dict: A dictionary containing mock functions for various Windows API functions.

    """
    create_mutex_called = False
    get_last_error_called = False
    message_box_called = False

    def create_mutex(*args, **kwargs):  # pylint:disable=unused-argument
        nonlocal create_mutex_called
        create_mutex_called = True
        return "mock_mutex"

    def get_last_error():
        nonlocal get_last_error_called
        get_last_error_called = True
        return 0  # No error by default

    def message_box(*args, **kwargs):  # pylint:disable=unused-argument
        nonlocal message_box_called
        message_box_called = True

    return {
        "CreateMutex": create_mutex,
        "GetLastError": get_last_error,
        "MessageBox": message_box,
        "create_mutex_called": lambda: create_mutex_called,
        "get_last_error_called": lambda: get_last_error_called,
        "message_box_called": lambda: message_box_called,
    }

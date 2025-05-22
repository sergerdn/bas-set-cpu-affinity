# BAS CPU Affinity Manager

A tool for managing CPU affinity for processes, allowing specific core assignments for main and worker processes.

## Description

**This tool only works on Windows systems** as it relies on Windows-specific CPU affinity functionality.

### Why This Tool Exists

This tool was specifically created to solve performance issues with BAS (Browser Automation Studio):

- The BAS main process runs on a single core
    - For compiled programs, the main process is named `FastExecuteScript.exe`
    - For non-compiled programs, the main process is named `BrowserAutomationStudio.exe`
- BAS main process spawns multiple worker (`Worker.exe`) processes that:
    - Communicate with the main process
    - Spawn Chromium browser processes named `worker.exe` (lowercase)
- On servers with old processors, when the main process and multiple workers run on the same core simultaneously,
  various issues can occur:
    - Timing errors in workers
    - Performance degradation
    - Task execution failures
    - Resource contention between the main process and workers
- At startup, the tool automatically moves existing processes from main cores to worker cores:
    - This frees up resources on the main cores for the BAS main process
    - Ensures the main process has dedicated CPU resources
    - Prevents resource contention with other processes

#### BAS Process Architecture

```
Main Process (FastExecuteScript.exe or BrowserAutomationStudio.exe)
├── Worker.exe (Worker Process)
│   └── worker.exe (Chromium Browser)
└── Worker.exe (Worker Process)
    └── worker.exe (Chromium Browser)
```

By assigning the main `BAS` process to specific cores and workers to different cores, this tool prevents these issues
and
ensures smooth operation even on servers with limited CPU resources.

### Key Benefits

- Dedicating specific cores to your main application for better performance
- Assigning worker processes to different cores to prevent resource contention
- Optimizing multiprocess applications by controlling CPU resource allocation
- Automatically moving existing processes from main cores to worker cores at startup to free up resources
- Preventing multiple instances from running simultaneously to avoid conflicts
- Especially helpful for servers without `GPUs`, where all processing loads (including browser processes that would
  normally use `GPU`) fall on the `CPU` and cores can easily become overloaded

The tool continuously monitors processes and ensures they maintain the specified CPU affinity settings.

## Installation

> **Note:** This tool is designed to work only on Windows operating systems.

### Download Pre-built Release (Recommended)

1. Download the latest release from [GitHub Releases](https://github.com/sergerdn/bas-set-cpu-affinity/releases)
2. Unpack the ZIP archive
3. Run the executable (`set_cpu_affinity.exe`) by double-clicking it

```txt
2025-05-22 08:23:50 - [cpu_affinity] - DEBUG - Starting CPU affinity manager
2025-05-22 08:23:50 - [cpu_affinity] - DEBUG - Python version: 3.12.3 (tags/v3.12.3:f6650f9, Apr  9 2024, 14:05:25) [MSC v.1938 64 bit (AMD64)]
2025-05-22 08:23:50 - [cpu_affinity] - DEBUG - System platform: win32
2025-05-22 08:23:50 - [cpu_affinity] - DEBUG - CPU count: 16
2025-05-22 08:23:50 - [cpu_affinity] - DEBUG - Main process names: ['FastExecuteScript.exe', 'BrowserAutomationStudio.exe']
2025-05-22 08:23:50 - [cpu_affinity] - DEBUG - Worker process names: ['worker.exe']
2025-05-22 08:23:50 - [cpu_affinity] - DEBUG - Main cores: [0, 1, 2, 3]
2025-05-22 08:23:50 - [cpu_affinity] - INFO - System CPU cores: 16
2025-05-22 08:23:50 - [cpu_affinity] - INFO - Main processes ['FastExecuteScript.exe', 'BrowserAutomationStudio.exe'] should assign to cores: [0, 1, 2, 3]
2025-05-22 08:23:50 - [cpu_affinity] - INFO - Worker processes ['worker.exe'] should assign to cores: [4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
2025-05-22 08:23:50 - [cpu_affinity] - DEBUG - Checking processes...
2025-05-22 08:23:50 - [cpu_affinity] - DEBUG - Looking for main processes: ['FastExecuteScript.exe', 'BrowserAutomationStudio.exe']
2025-05-22 08:23:50 - [cpu_affinity] - DEBUG - Looking for worker processes: ['worker.exe']
2025-05-22 08:23:50 - [cpu_affinity] - WARNING - No main processes found matching: ['FastExecuteScript.exe', 'BrowserAutomationStudio.exe']
2025-05-22 08:23:50 - [cpu_affinity] - WARNING - No worker processes found matching: ['worker.exe']
2025-05-22 08:23:50 - [cpu_affinity] - DEBUG - Sleeping for 10.0 seconds...
2025-05-22 08:24:00 - [cpu_affinity] - DEBUG - Checking processes...
2025-05-22 08:24:00 - [cpu_affinity] - DEBUG - Looking for main processes: ['FastExecuteScript.exe', 'BrowserAutomationStudio.exe']
2025-05-22 08:24:00 - [cpu_affinity] - DEBUG - Looking for worker processes: ['worker.exe']
2025-05-22 08:24:00 - [cpu_affinity] - WARNING - No main processes found matching: ['FastExecuteScript.exe', 'BrowserAutomationStudio.exe']
2025-05-22 08:24:00 - [cpu_affinity] - WARNING - No worker processes found matching: ['worker.exe']
2025-05-22 08:24:00 - [cpu_affinity] - DEBUG - Sleeping for 10.0 seconds...
```

### From Source

```bash
git clone git@github.com:sergerdn/bas-set-cpu-affinity.git
cd bas-set-cpu-affinity
poetry install
```

## Usage

When you start the tool, it is automatically:

1. Checks if another instance is already running and prevents multiple instances
2. Identifies the available CPU cores and assigns them to main and worker processes
3. Moves existing processes from main cores to worker cores to free up resources
4. Begins monitoring and managing CPU affinity for all matching processes

If you attempt to start the tool when another instance is already running, you'll see an error message in a dialog box
and the new
instance will exit. This ensures that error messages are visible even when launching the application by double-clicking
the executable file.

### Command Line

```bash
# Basic usage with automatic core assignment based on CPU count
set-cpu-affinity

# Manually assign main process to cores 0, 2, and 4
set-cpu-affinity 0-2-4

# Change the polling interval
set-cpu-affinity --interval 5

# Enable verbose logging
set-cpu-affinity -v
```

### Options

- `main_cores` (optional): Hyphen-separated core numbers for the main process (e.g., '0-2-4'). If not provided, cores
  will be automatically assigned based on the system CPU count:
    - For systems with 4 or fewer cores: 1 core (core 0)
    - For systems with 5–8 cores: 2 cores (cores 0 and 1)
    - For systems with more than 8 cores: 25% of cores (rounded down), with a minimum of 2 cores and a maximum of 4
      cores
- `--interval`: Polling interval in seconds (default: 10)
- `--main-name`: Comma-separated main process names (case-insensitive, default:
  `FastExecuteScript.exe,BrowserAutomationStudio.exe`)
- `--workers`: Comma-separated worker process names (case-insensitive, default: `worker.exe`)
- `-v, --verbose`: Enable verbose logging (includes debug information to help identify issues)

### Building an Executable

You can build a standalone executable using:

```bash
make build_executable
```

The executable will be created in the `dist` directory.

### Troubleshooting

If you're experiencing issues with the tool not working as expected:

1. Run with verbose logging enabled:
   ```bash
   set-cpu-affinity -v
   ```

2. Check if the correct process names are being monitored:
    - For compiled BAS programs, the main process is named `FastExecuteScript.exe`
    - For non-compiled BAS programs, the main process is named `BrowserAutomationStudio.exe`
    - Worker processes are typically named `worker.exe` (lowercase)

3. Verify that the processes are actually running:
    - Use Task Manager to check if the processes exist
    - If the processes have different names, specify them with the `--main-name` and `--workers` options

4. If you still encounter issues, run the tool from the command line to see all debug messages:
   ```bash
   cd path\to\extracted\folder
   set_cpu_affinity.exe -v
   ```

### GitHub Releases

To prepare files for a GitHub release that includes the executable:

1. Run the prepare_release command:
   ```bash
   make prepare_release
   ```

2. When creating a GitHub release, upload the executable file from the `dist` directory:
    - `dist/set_cpu_affinity.exe`

This ensures users can download and run the tool without needing to install Python or any dependencies.

## Development

For detailed information about development, building, and releasing, please see the [Development Guide](DEVELOPMENT.md).

### Planned Features

We maintain a [TODO list](TODO.md) of planned enhancements and features for future development, including:

- Special logic for multiple BAS programs runs on a server with different CPU assignments
- A list of typical errors that the software can solve

If you're interested in contributing or want to know what's coming next, check out the [TODO.md](TODO.md) file.

### Quick Start

```bash
# Clone the repository
git clone git@github.com:sergerdn/bas-set-cpu-affinity.git
cd bas-set-cpu-affinity

# Install dependencies
poetry install

# Run the tool
poetry run set-cpu-affinity -v
```

## License

This project is licensed under the MIT License. See the LICENSE file for details.

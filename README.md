# BAS CPU Affinity Manager

A tool for managing CPU affinity for processes, allowing specific core assignments for main and worker processes.

## Description

BAS CPU Affinity Manager is a Python package that helps you control which CPU cores your processes run on.

**This tool only works on Windows systems** as it relies on Windows-specific CPU affinity functionality.

### Why This Tool Exists

This tool was specifically created to solve performance issues with BAS (Browser Automation Studio):

- The BAS main process (`FastExecuteScript.exe`) runs on a single core
- BAS main process spawns multiple worker (`Worker.exe`) processes that:
    - Communicate with the main process
    - Spawn Chromium browser processes named `worker.exe` (lowercase)
- On servers with older processors, when the main process and multiple workers run on the same core simultaneously,
  various issues can occur:
    - Timing errors in workers
    - Performance degradation
    - Task execution failures
    - Resource contention between the main process and workers

#### BAS Process Architecture

```
FastExecuteScript.exe (Main Process)
├── Worker.exe (Worker Process)
│   └── worker.exe (Chromium Browser)
└── Worker.exe (Worker Process)
    └── worke.exe (Chromium Browser)
```

By assigning the main BAS process to specific cores and workers to different cores, this tool prevents these issues and
ensures smooth operation even on servers with limited CPU resources.

### Key Benefits

- Dedicating specific cores to your main application for better performance
- Assigning worker processes to different cores to prevent resource contention
- Optimizing multiprocess applications by controlling CPU resource allocation

The tool continuously monitors processes and ensures they maintain the specified CPU affinity settings.

## Installation

> **Note:** This tool is designed to work only on Windows operating systems.

```bash
git clone git@github.com:sergerdn/bas-set-cpu-affinity.git
cd bas-set-cpu-affinity
poetry install
```

## Usage

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
- `--main-name`: Main process name (case-insensitive, default: `FastExecuteScript.exe`)
- `--workers`: Comma-separated worker process names (case-insensitive, default: `Worker.exe`)
- `-v, --verbose`: Enable verbose logging

### Building an Executable

You can build a standalone executable using:

```bash
make build_executable
```

The executable will be created in the `dist` directory.

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

### Setup

```bash
# Clone the repository
git clone git@github.com:sergerdn/bas-set-cpu-affinity.git
cd bas-set-cpu-affinity

# Install dependencies
poetry install

# Run the tool
poetry run set-cpu-affinity 0-1-2-3-4 -v
```

### Makefile Commands

- `make build`: Build the package
- `make install`: Install the package
- `make run`: Run the tool with default parameters
- `make build_executable`: Build a standalone executable
- `make clean`: Clean build artifacts
- `make lint`: Check code for style issues without fixing them
- `make lint_fix`: Automatically fix code style issues
- `make prepare_release`: Prepare files for GitHub release (cleans, lints, and builds executable)

## License

This project is licensed under the MIT License. See the LICENSE file for details.

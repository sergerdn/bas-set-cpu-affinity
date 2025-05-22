"""Command-line interface for CPU affinity management.

This module provides the CLI functionality for the CPU affinity manager.

"""

import logging
import sys
import time

import click
import psutil

from .core import move_processes_from_main_cores, parse_core_string, set_affinities, validate_cores

# Configure logging only if it hasn't been configured already
# This allows the entry point script to set its own configuration
if not logging.getLogger().handlers:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
logger = logging.getLogger("[cpu_affinity]")


def calculate_default_main_cores():
    """Calculate default main cores based on CPU count."""
    cpu_count = psutil.cpu_count()

    # Determine how many cores to allocate to the main process based on total cores
    if cpu_count <= 4:
        # For systems with 4 or fewer cores, allocate 1 core
        return [0]
    if cpu_count <= 8:
        # For systems with 5-8 cores, allocate 2 cores
        return [0, 1]
    # For systems with more than 8 cores, allocate 25% of cores (rounded down)
    # but limit to maximum 4 cores
    num_cores = min(4, max(2, cpu_count // 4))
    return list(range(num_cores))


def validate_cores_callback(_ctx, _param, value):
    """Click callback for core validation."""
    if value is None:
        # Use default cores if not specified
        return calculate_default_main_cores()
    try:
        cores = parse_core_string(value)
        return validate_cores(cores)
    except ValueError as e:
        raise click.BadParameter(str(e))


@click.command()
@click.argument("main_cores", callback=validate_cores_callback, required=False)
@click.option(
    "--interval",
    type=float,
    default=10.0,
    help="Polling interval in seconds (default: 10)",
    show_default=True,
)
@click.option(
    "--main-name",
    default="FastExecuteScript.exe,BrowserAutomationStudio.exe",
    help="Comma-separated main process names (case-insensitive)",
    show_default=True,
)
@click.option(
    "--workers",
    default="worker.exe",
    help="Comma-separated worker process names (case-insensitive)",
    show_default=True,
)
@click.option("-v", "--verbose", is_flag=True, help="Enable verbose logging")
def manage_affinity(main_cores, interval, main_name, workers, verbose):
    """Set CPU affinity for processes with specified core allocations.

    main_cores: Hyphen-separated core numbers for the main process (e.g. '0-2-4')
                If not provided, cores will be automatically assigned based on system CPU count.

    """
    # Configure logging
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)

    logger.debug("Starting CPU affinity manager")
    logger.debug("Python version: %s", sys.version)
    logger.debug("System platform: %s", sys.platform)

    # Process configuration
    main_names = [name.strip() for name in main_name.split(",")]
    worker_names = [w.strip() for w in workers.split(",")]
    cpu_count = psutil.cpu_count()

    logger.debug("CPU count: %s", cpu_count)
    logger.debug("Main process names: %s", main_names)
    logger.debug("Worker process names: %s", worker_names)
    logger.debug("Main cores: %s", main_cores)

    # Calculate worker cores
    worker_cores = [c for c in range(cpu_count) if c not in main_cores]
    if not worker_cores:
        logger.error("No cores available for worker processes!")
        raise click.Abort()

    logger.info("System CPU cores: %s", cpu_count)
    logger.info("Main processes %s should assign to cores: %s", main_names, main_cores)
    logger.info("Worker processes %s should assign to cores: %s", worker_names, worker_cores)

    # Move all processes from main cores to worker cores at startup, except main processes
    move_processes_from_main_cores(main_cores, worker_cores, main_names)

    # Main monitoring loop
    consecutive_failures = 0
    while True:
        try:
            logger.debug("Checking processes...")
            main_found, worker_found = set_affinities(main_names, worker_names, main_cores, worker_cores)

            if main_found or worker_found:
                consecutive_failures = 0
            else:
                consecutive_failures += 1
                if consecutive_failures >= 5:
                    logger.warning("No target processes found for 5 consecutive checks")
                    consecutive_failures = 0

            logger.debug("Sleeping for %s seconds...", interval)
        except KeyboardInterrupt:
            logger.info("Exiting...")
            break
        except (psutil.Error, OSError) as e:
            logger.error("Error in main loop: %s", str(e))
        # pylint: disable=broad-exception-caught
        except Exception as e:
            # Catch any unexpected exceptions to prevent the monitoring loop from crashing
            logger.error("Unexpected error in main loop: %s", str(e))
        time.sleep(interval)


def main():
    """Entry point for the CLI."""
    # pylint: disable=no-value-for-parameter
    manage_affinity()


if __name__ == "__main__":
    main()

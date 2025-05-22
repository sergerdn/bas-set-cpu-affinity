"""Command-line interface for CPU affinity management.

This module provides the CLI functionality for the CPU affinity manager.

"""

import logging
import time

import click
import psutil

from .core import parse_core_string, set_affinities, validate_cores

# Configure logging
logging.basicConfig(level=logging.INFO)
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
    default="FastExecuteScript.exe",
    help="Main process name (case-insensitive)",
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

    # Process configuration
    worker_names = [w.strip() for w in workers.split(",")]
    cpu_count = psutil.cpu_count()

    # Calculate worker cores
    worker_cores = [c for c in range(cpu_count) if c not in main_cores]
    if not worker_cores:
        logger.error("No cores available for worker processes!")
        raise click.Abort()

    logger.info("System CPU cores: %s", cpu_count)
    logger.info("Main process '%s' should assign to cores: %s", main_name, main_cores)
    logger.info("Worker processes %s should assign to cores: %s", worker_names, worker_cores)

    # Main monitoring loop
    while True:
        try:
            set_affinities(main_name, worker_names, main_cores, worker_cores)
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

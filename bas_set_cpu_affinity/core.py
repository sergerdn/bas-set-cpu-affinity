"""Core functionality for CPU affinity management.

This module provides the core functions for parsing CPU core specifications and setting process affinities.

"""

import logging

import psutil

logger = logging.getLogger("[cpu_affinity]")


def parse_core_string(core_str):
    """Parse a core specification string into a sorted list of unique integers."""
    try:
        cores = list({int(c) for c in core_str.split("-")})
        return sorted(cores)
    except ValueError as exc:
        raise ValueError("Invalid core format. Use hyphen-separated numbers (e.g. '0-2-4')") from exc


def set_affinities(main_name, worker_names, main_cores, worker_cores):
    """Update CPU affinities for all matching processes."""
    for proc in psutil.process_iter(["name", "pid"]):
        try:
            proc_name = proc.info["name"]

            if proc_name.lower() == main_name.lower():
                handle_main_process(proc, main_cores)
            elif any(proc_name.lower() == worker.lower() for worker in worker_names):
                handle_worker_process(proc, worker_cores)

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass  # Process disappeared or we don't have permissions
        except (AttributeError, OSError) as e:
            logger.debug("Error accessing process: %s", e)


def handle_main_process(proc, target_cores):
    """Handle affinity setting for the main process."""
    current = proc.cpu_affinity()
    if sorted(current) != target_cores:
        logger.debug("Updating main %s from %s to %s", proc.pid, current, target_cores)
        proc.cpu_affinity(target_cores)


def handle_worker_process(proc, target_cores):
    """Handle affinity setting for a worker process."""
    current = proc.cpu_affinity()
    if sorted(current) != target_cores:
        logger.debug("Updating worker %s from %s to %s", proc.pid, current, target_cores)
        proc.cpu_affinity(target_cores)


def validate_cores(cores):
    """Validate core numbers against system CPU count."""
    cpu_count = psutil.cpu_count()

    if any(c >= cpu_count or c < 0 for c in cores):
        raise ValueError(f"Invalid core numbers. System has only {cpu_count} cores")
    return cores

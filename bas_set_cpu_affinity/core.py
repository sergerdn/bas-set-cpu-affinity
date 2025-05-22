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


def set_affinities(main_names, worker_names, main_cores, worker_cores):
    """Update CPU affinities for all matching processes."""
    # Convert main_names to a list if it's a string
    if isinstance(main_names, str):
        main_names = [name.strip() for name in main_names.split(",")]

    logger.debug("Looking for main processes: %s", main_names)
    logger.debug("Looking for worker processes: %s", worker_names)

    main_processes_found = False
    worker_processes_found = False

    for proc in psutil.process_iter(["name", "pid"]):
        try:
            proc_name = proc.info["name"]
            # logger.debug("Checking process: %s (PID: %s)", proc_name, proc.info["pid"])

            if any(proc_name.lower() == main.lower() for main in main_names):
                logger.debug("Found main process: %s (PID: %s)", proc_name, proc.info["pid"])
                handle_main_process(proc, main_cores)
                main_processes_found = True
            elif any(proc_name.lower() == worker.lower() for worker in worker_names):
                logger.debug("Found worker process: %s (PID: %s)", proc_name, proc.info["pid"])
                handle_worker_process(proc, worker_cores)
                worker_processes_found = True

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass  # Process disappeared or we don't have permissions
        except (AttributeError, OSError) as e:
            logger.debug("Error accessing process: %s", e)

    # Log if no processes were found
    if not main_processes_found:
        logger.warning("No main processes found matching: %s", main_names)
    if not worker_processes_found:
        logger.warning("No worker processes found matching: %s", worker_names)

    return main_processes_found, worker_processes_found


def handle_main_process(proc, target_cores):
    """Handle affinity setting for the main process."""
    logger.debug("Handling main process: %s (PID: %s)", proc.info["name"], proc.pid)
    current = proc.cpu_affinity()
    logger.debug("Current affinity for main process %s: %s", proc.pid, current)

    if sorted(current) != target_cores:
        logger.debug("Updating main %s from %s to %s", proc.pid, current, target_cores)
        proc.cpu_affinity(target_cores)
        logger.debug("Affinity updated successfully for main process %s", proc.pid)
    else:
        logger.debug("No affinity update needed for main process %s (already set to %s)", proc.pid, current)


def handle_worker_process(proc, target_cores):
    """Handle affinity setting for a worker process."""
    logger.debug("Handling worker process: %s (PID: %s)", proc.info["name"], proc.pid)
    current = proc.cpu_affinity()
    logger.debug("Current affinity for worker process %s: %s", proc.pid, current)

    if sorted(current) != target_cores:
        logger.debug("Updating worker %s from %s to %s", proc.pid, current, target_cores)
        proc.cpu_affinity(target_cores)
        logger.debug("Affinity updated successfully for worker process %s", proc.pid)
    else:
        logger.debug("No affinity update needed for worker process %s (already set to %s)", proc.pid, current)


def validate_cores(cores):
    """Validate core numbers against system CPU count."""
    cpu_count = psutil.cpu_count()

    if any(c >= cpu_count or c < 0 for c in cores):
        raise ValueError(f"Invalid core numbers. System has only {cpu_count} cores")
    return cores

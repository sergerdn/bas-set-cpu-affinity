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


def move_processes_from_main_cores(main_cores, worker_cores, main_names=None):
    """Move all processes from main cores to worker cores, except main processes.

    This function identifies all processes currently running on the main CPU cores and moves them to the worker cores to
    free up resources for the main process. Main processes (specified by main_names) are not moved.

    """
    if not worker_cores:
        logger.warning("No worker cores available to move processes to")
        return

    logger.info("Moving processes from main cores %s to worker cores %s", main_cores, worker_cores)

    # Convert main_names to a list if it's a string
    if isinstance(main_names, str):
        main_names = [name.strip() for name in main_names.split(",")]

    # If main_names is None, use an empty list
    if main_names is None:
        main_names = []

    moved_count = 0
    for proc in psutil.process_iter(["pid", "name"]):
        try:
            # Skip system processes that might cause issues if moved
            if proc.pid <= 4:  # System processes on Windows
                continue

            proc_name = proc.info["name"]

            # Skip main processes - don't move them from main cores
            if any(proc_name.lower() == main.lower() for main in main_names):
                logger.debug("Skipping main process %s (PID: %s) - keeping on main cores", proc_name, proc.pid)
                continue

            current_affinity = proc.cpu_affinity()

            # Check if the process is running exclusively on main cores
            if all(core in main_cores for core in current_affinity):
                logger.debug(
                    "Found process %s (PID: %s) running on main cores: %s", proc_name, proc.pid, current_affinity
                )

                # Set new affinity to worker cores
                proc.cpu_affinity(worker_cores)
                logger.debug("Moved process %s (PID: %s) to worker cores: %s", proc_name, proc.pid, worker_cores)
                moved_count += 1

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass  # Process disappeared or we don't have permissions
        except (AttributeError, OSError) as e:
            logger.debug("Error accessing process: %s", e)

    logger.info("Moved %d processes from main cores to worker cores", moved_count)


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

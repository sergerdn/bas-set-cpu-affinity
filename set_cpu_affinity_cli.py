#!/usr/bin/env python
"""Command-line entry point for the CPU affinity manager."""
import logging
import sys

from bas_set_cpu_affinity.cli import main

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger("[cpu_affinity_cli]")

    # Add -v flag to sys.argv if not already present
    if "-v" not in sys.argv and "--verbose" not in sys.argv:
        sys.argv.append("-v")

    # Always log debug information as if -v flag was provided
    logger.debug("Starting CPU affinity manager from CLI entry point")
    logger.debug("Python version: %s", sys.version)
    logger.debug("System platform: %s", sys.platform)
    logger.debug("Command line arguments (after modification): %s", sys.argv)

    # Run the main function
    main()

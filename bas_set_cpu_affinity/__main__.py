"""The main entry point for the package when run as a module.

This allows running the package with `python -m bas_set_cpu_affinity`.

"""

from .cli import main

if __name__ == "__main__":
    main()

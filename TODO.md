# TODO List for BAS CPU Affinity Manager

This document outlines planned enhancements and features for future development.

## Planned Features

- [ ] Add special logic for multiple BAS program runs on a server, ensuring each program instance is assigned to
  different
  CPU cores to prevent resource contention
- [ ] Add a list of typical errors that the software can solve, including:
    - Timing errors in worker processes
        - Performance degradation due to CPU contention
        - Task execution failures caused by resource limitations
        - Communication issues between main and worker processes
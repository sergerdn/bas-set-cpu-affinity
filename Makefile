# Define all targets as phony (not representing files)
.PHONY: build run install clean lint lint_fix prepare_release bump_version bump_version_major bump_version_minor bump_version_patch
# Set the default goal when running make without arguments
.DEFAULT_GOAL := build

# Run the application with default settings and verbose logging
run:
	poetry run set_cpu_affinity_cli --interval 10 -v

# Build the Python package (creates wheel and source distribution)
build:
	poetry build

# Install the package and its dependencies
install:
	poetry install

# Build a standalone executable using PyInstaller
build_executable:
	poetry run pyinstaller --onefile set_cpu_affinity_cli.py -n set_cpu_affinity

# Remove build artifacts and temporary files
clean:
	rm -rf dist build *.egg-info

# Check code for style issues without fixing them
lint:
	docformatter --config pyproject.toml --black --check --recursive set_cpu_affinity_cli.py bas_set_cpu_affinity/ || echo ""
	poetry run black --check set_cpu_affinity_cli.py bas_set_cpu_affinity/
	poetry run isort --check set_cpu_affinity_cli.py bas_set_cpu_affinity/
	poetry run flake8 set_cpu_affinity_cli.py bas_set_cpu_affinity/
	poetry run pylint set_cpu_affinity_cli.py bas_set_cpu_affinity/
	poetry run mypy set_cpu_affinity_cli.py bas_set_cpu_affinity/

# Automatically fix code style issues
lint_fix:
	docformatter --config pyproject.toml --black --in-place --recursive set_cpu_affinity_cli.py bas_set_cpu_affinity/ || echo ""
	poetry run black set_cpu_affinity_cli.py bas_set_cpu_affinity/
	poetry run isort set_cpu_affinity_cli.py bas_set_cpu_affinity/

# Prepare files for GitHub release (builds executable and cleans up unnecessary files)
prepare_release:
	make clean
	make lint
	make build_executable

# Bump version automatically based on commit messages
bump_version:
	poetry run cz bump --changelog

# Bump major version (x.0.0)
bump_version_major:
	poetry run cz bump --increment MAJOR

# Bump minor version (0.x.0)
bump_version_minor:
	poetry run cz bump --increment MINOR

# Bump patch version (0.0.x)
bump_version_patch:
	poetry run cz bump --increment PATCH

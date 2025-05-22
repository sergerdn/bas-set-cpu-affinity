# Define all targets as phony (not representing files)
.PHONY: build run install clean lint lint_fix lint_tests lint_tests_fix fix_all check_all prepare_release bump_version bump_version_major bump_version_minor bump_version_patch tests tests_coverage
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

# Check tests for style issues without fixing them
lint_tests:
	docformatter --config pyproject.toml --black --check --recursive tests/ || echo ""
	poetry run black --check tests/
	poetry run isort --check tests/
	poetry run flake8 tests/
	poetry run pylint tests/
	poetry run mypy tests/

# Automatically fix style issues in tests
lint_tests_fix:
	docformatter --config pyproject.toml --black --in-place --recursive tests/ || echo ""
	poetry run black tests/
	poetry run isort tests/

# Fix all code style issues in one command
fix_all:
	make lint_fix
	make lint_tests_fix

# Check all code (main code and tests) for style issues and run all tests
check_all:
	make lint
	make lint_tests
	make test

# Run all tests
tests:
	poetry run pytest -v tests

# Run tests with coverage report
tests_coverage:
	poetry run pytest -v --cov=bas_set_cpu_affinity --cov-report=term --cov-report=html:coverage/html/ tests/
	start "" "./coverage/html/index.html" || powershell -command "Invoke-Item './coverage/html/index.html'"

# Prepare files for GitHub release (builds executable and cleans up unnecessary files)
prepare_release:
	make clean
	make check_all
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

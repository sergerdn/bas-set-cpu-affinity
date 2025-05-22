# Development Guide for BAS CPU Affinity Manager

This document contains information for developers working on the BAS CPU Affinity Manager project, including build
instructions, release procedures, and development workflows.

## Development Setup

```bash
# Clone the repository
git clone git@github.com:sergerdn/bas-set-cpu-affinity.git
cd bas-set-cpu-affinity

# Install dependencies
poetry install
```

## Development Workflow

### Code Style and Linting

The project uses several tools to maintain code quality:

```bash
# Check code for style issues without fixing them
make lint

# Automatically fix code style issues
make lint_fix
```

## Building

### Building the Package

```bash
# Build the Python package (creates wheel and source distribution)
make build
```

### Building the Executable

```bash
# Build a standalone executable
make build_executable
```

The executable will be created in the `dist` directory.

## Release Process

This project uses [Commitizen](https://commitizen-tools.github.io/commitizen/) for versioning and changelog generation.

### Commit Message Format

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification for commit messages:

```
<type>(<scope>): <subject>

<body>

<footer>
```

Types include:

- `feat`: A new feature
- `fix`: A bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code changes that neither fix bugs nor add features
- `perf`: Performance improvements
- `test`: Adding or fixing tests
- `build`: Changes to a build system or dependencies
- `ci`: Changes to CI configuration
- `chore`: Other changes that don't modify src or test files

### Creating a New Release

1. Make sure all your changes are committed

2. Bump the version and update the changelog:
   ```bash
   make bump_version
   ```
   This will:
    - Determine the next version based on commit messages
    - Update version in all configured files
    - Update the CHANGELOG.md file
    - Create a git tag

3. Push the changes and tag:
   ```bash
   git push
   git push --tags
   ```

4. Prepare the release files:
   ```bash
   make prepare_release
   ```
   This will:
    - Clean the build artifacts
    - Run linting checks
    - Build the executable

5. Create a GitHub release:
    - Go to the GitHub repository's Releases page
    - Create a new release from the tag
    - Upload the executable from the `dist` directory
    - Add release notes (you can copy from the CHANGELOG.md file)

## Makefile Commands

- `make build`: Build the package
- `make install`: Install the package
- `make run`: Run the tool with default parameters
- `make build_executable`: Build a standalone executable
- `make clean`: Clean build artifacts
- `make lint`: Check code for style issues without fixing them
- `make lint_fix`: Automatically fix code style issues
- `make prepare_release`: Prepare files for GitHub release (cleans, lints, and builds executable)
- `make bump_version`: Bump version and update changelog
- `make bump_version_major`: Bump major version
- `make bump_version_minor`: Bump minor version
- `make bump_version_patch`: Bump patch version
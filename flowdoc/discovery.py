"""File discovery for cross-module flow analysis."""

from pathlib import Path

DEFAULT_EXCLUDES = frozenset(
    {
        "__pycache__",
        ".git",
        ".hg",
        ".svn",
        ".venv",
        "venv",
        "env",
        ".env",
        ".tox",
        ".nox",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        "node_modules",
        "tests",
        "test",
    }
)


def is_test_file(path: Path) -> bool:
    """Check if a file is a test file by naming convention.

    :param path: Path to check
    :return: True if the file matches test naming patterns
    """
    name = path.stem
    return name.startswith("test_") or name.endswith("_test") or name == "conftest"


def discover_python_files(
    root: Path,
    exclude_patterns: set[str] | None = None,
) -> list[Path]:
    """Recursively discover Python files in a directory.

    Excludes common non-source directories (venvs, caches, test directories)
    and test files by default.

    :param root: Directory to search, or a single .py file.
    :param exclude_patterns: Additional directory names to exclude.
    :return: List of Path objects for discovered .py files.
    :raises FileNotFoundError: If root does not exist.
    :raises ValueError: If root is not a directory or .py file.
    """
    root = root.resolve()

    if not root.exists():
        raise FileNotFoundError(f"Path does not exist: {root}")

    if root.is_file():
        if root.suffix == ".py":
            return [root]
        raise ValueError(f"Not a Python file: {root}")

    if not root.is_dir():
        raise ValueError(f"Not a file or directory: {root}")

    excludes = DEFAULT_EXCLUDES | (exclude_patterns or set())
    python_files: list[Path] = []

    def _should_exclude_dir(dir_path: Path) -> bool:
        if dir_path.name.startswith("."):
            return True
        return dir_path.name in excludes

    def _walk(directory: Path) -> None:
        try:
            entries = sorted(directory.iterdir())
        except PermissionError:
            return

        for entry in entries:
            if entry.is_dir():
                if not _should_exclude_dir(entry):
                    _walk(entry)
            elif entry.is_file() and entry.suffix == ".py":
                if not is_test_file(entry):
                    python_files.append(entry)

    _walk(root)
    return python_files

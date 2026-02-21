"""Tests for the file discovery module."""

from pathlib import Path

import pytest

from flowdoc.discovery import discover_python_files, is_test_file


class TestIsTestFile:
    """Tests for is_test_file()."""

    def test_test_prefix(self, tmp_path: Path) -> None:
        """Files starting with test_ are test files."""
        assert is_test_file(tmp_path / "test_orders.py") is True

    def test_test_suffix(self, tmp_path: Path) -> None:
        """Files ending with _test are test files."""
        assert is_test_file(tmp_path / "orders_test.py") is True

    def test_regular_file(self, tmp_path: Path) -> None:
        """Regular files are not test files."""
        assert is_test_file(tmp_path / "orders.py") is False

    def test_conftest(self, tmp_path: Path) -> None:
        """conftest.py is a test file."""
        assert is_test_file(tmp_path / "conftest.py") is True


class TestDiscoverPythonFiles:
    """Tests for discover_python_files()."""

    def test_discover_single_file(self, tmp_path: Path) -> None:
        """A single .py file returns just that file."""
        py_file = tmp_path / "module.py"
        py_file.write_text("x = 1\n")
        result = discover_python_files(py_file)
        assert result == [py_file.resolve()]

    def test_discover_directory(self, tmp_path: Path) -> None:
        """Discovers .py files in a directory."""
        (tmp_path / "a.py").write_text("a = 1\n")
        (tmp_path / "b.py").write_text("b = 1\n")
        (tmp_path / "readme.txt").write_text("not python\n")
        result = discover_python_files(tmp_path)
        names = [p.name for p in result]
        assert "a.py" in names
        assert "b.py" in names
        assert "readme.txt" not in names

    def test_excludes_pycache(self, tmp_path: Path) -> None:
        """__pycache__ directories are excluded."""
        cache_dir = tmp_path / "__pycache__"
        cache_dir.mkdir()
        (cache_dir / "cached.py").write_text("x = 1\n")
        (tmp_path / "real.py").write_text("x = 1\n")
        result = discover_python_files(tmp_path)
        assert all("__pycache__" not in str(p) for p in result)

    def test_excludes_tests_directory(self, tmp_path: Path) -> None:
        """tests/ and test/ directories are excluded."""
        for dirname in ("tests", "test"):
            test_dir = tmp_path / dirname
            test_dir.mkdir()
            (test_dir / "test_something.py").write_text("x = 1\n")
        (tmp_path / "real.py").write_text("x = 1\n")
        result = discover_python_files(tmp_path)
        names = [p.name for p in result]
        assert "test_something.py" not in names
        assert "real.py" in names

    def test_excludes_test_files(self, tmp_path: Path) -> None:
        """Test files (test_*.py, *_test.py) are excluded."""
        (tmp_path / "test_orders.py").write_text("x = 1\n")
        (tmp_path / "orders_test.py").write_text("x = 1\n")
        (tmp_path / "orders.py").write_text("x = 1\n")
        result = discover_python_files(tmp_path)
        names = [p.name for p in result]
        assert names == ["orders.py"]

    def test_excludes_conftest(self, tmp_path: Path) -> None:
        """conftest.py files are excluded."""
        (tmp_path / "conftest.py").write_text("import pytest\n")
        (tmp_path / "orders.py").write_text("x = 1\n")
        result = discover_python_files(tmp_path)
        names = [p.name for p in result]
        assert "conftest.py" not in names
        assert "orders.py" in names

    def test_excludes_hidden_dirs(self, tmp_path: Path) -> None:
        """Hidden directories (starting with .) are excluded."""
        hidden = tmp_path / ".hidden"
        hidden.mkdir()
        (hidden / "secret.py").write_text("x = 1\n")
        (tmp_path / "visible.py").write_text("x = 1\n")
        result = discover_python_files(tmp_path)
        assert all(".hidden" not in str(p) for p in result)

    def test_excludes_venv_variants(self, tmp_path: Path) -> None:
        """Virtual environment directories are excluded."""
        for dirname in ("venv", "env", ".venv", ".env", ".tox", ".nox"):
            venv_dir = tmp_path / dirname
            venv_dir.mkdir()
            (venv_dir / "module.py").write_text("x = 1\n")
        (tmp_path / "real.py").write_text("x = 1\n")
        result = discover_python_files(tmp_path)
        assert len(result) == 1
        assert result[0].name == "real.py"

    def test_custom_excludes(self, tmp_path: Path) -> None:
        """Additional exclude patterns work."""
        migrations = tmp_path / "migrations"
        migrations.mkdir()
        (migrations / "001.py").write_text("x = 1\n")
        (tmp_path / "real.py").write_text("x = 1\n")
        result = discover_python_files(tmp_path, exclude_patterns={"migrations"})
        names = [p.name for p in result]
        assert "001.py" not in names
        assert "real.py" in names

    def test_nonexistent_path_raises(self) -> None:
        """FileNotFoundError for nonexistent paths."""
        with pytest.raises(FileNotFoundError, match="does not exist"):
            discover_python_files(Path("/nonexistent/path"))

    def test_non_python_file_raises(self, tmp_path: Path) -> None:
        """ValueError for non-Python files."""
        txt_file = tmp_path / "readme.txt"
        txt_file.write_text("not python\n")
        with pytest.raises(ValueError, match="Not a Python file"):
            discover_python_files(txt_file)

    def test_recursive_discovery(self, tmp_path: Path) -> None:
        """Discovers files in nested subdirectories."""
        sub = tmp_path / "pkg" / "sub"
        sub.mkdir(parents=True)
        (tmp_path / "pkg" / "__init__.py").write_text("")
        (tmp_path / "pkg" / "sub" / "__init__.py").write_text("")
        (tmp_path / "pkg" / "module.py").write_text("x = 1\n")
        (tmp_path / "pkg" / "sub" / "deep.py").write_text("x = 1\n")
        result = discover_python_files(tmp_path)
        names = [p.name for p in result]
        assert "__init__.py" in names
        assert "module.py" in names
        assert "deep.py" in names

    def test_results_are_sorted(self, tmp_path: Path) -> None:
        """Results are deterministically ordered."""
        (tmp_path / "z_module.py").write_text("x = 1\n")
        (tmp_path / "a_module.py").write_text("x = 1\n")
        result = discover_python_files(tmp_path)
        names = [p.name for p in result]
        assert names == sorted(names)

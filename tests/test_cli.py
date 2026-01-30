"""Tests for the FlowDoc CLI."""

from pathlib import Path
from textwrap import dedent

import pytest
from click.testing import CliRunner

from flowdoc.cli import cli


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture
def sample_source(tmp_path: Path) -> Path:
    """Create a sample Python file with a flow."""
    source = dedent("""
        from flowdoc import flow, step

        @flow(name="Order Flow", description="Process orders")
        class OrderFlow:
            @step(name="Receive Order")
            def receive(self):
                return self.validate()

            @step(name="Validate")
            def validate(self):
                if True:
                    return self.process()
                else:
                    return self.reject()

            @step(name="Process")
            def process(self):
                pass

            @step(name="Reject")
            def reject(self):
                pass
    """)
    file_path = tmp_path / "order_flow.py"
    file_path.write_text(source)
    return file_path


@pytest.fixture
def empty_source(tmp_path: Path) -> Path:
    """Create a Python file with no flows."""
    file_path = tmp_path / "empty.py"
    file_path.write_text("def hello(): pass\n")
    return file_path


class TestGenerateCommand:
    """Tests for the generate command."""

    def test_generate_dot_format(
        self, runner: CliRunner, sample_source: Path, tmp_path: Path
    ) -> None:
        """Test generating DOT output."""
        output_path = tmp_path / "output"
        result = runner.invoke(
            cli, ["generate", str(sample_source), "-f", "dot", "-o", str(output_path)]
        )
        assert result.exit_code == 0
        assert "Generated:" in result.output

    def test_generate_mermaid_format(
        self, runner: CliRunner, sample_source: Path, tmp_path: Path
    ) -> None:
        """Test generating Mermaid output."""
        output_path = tmp_path / "output"
        result = runner.invoke(
            cli, ["generate", str(sample_source), "-f", "mermaid", "-o", str(output_path)]
        )
        assert result.exit_code == 0
        assert "Generated:" in result.output

        # Verify the file was created
        mmd_path = tmp_path / "output.mmd"
        assert mmd_path.exists()
        content = mmd_path.read_text()
        assert "flowchart" in content

    def test_generate_default_output_name(
        self, runner: CliRunner, sample_source: Path, tmp_path: Path
    ) -> None:
        """Test that default output uses slugified flow name."""
        # Run from tmp_path to control where output goes
        result = runner.invoke(
            cli,
            ["generate", str(sample_source), "-f", "dot"],
        )
        assert result.exit_code == 0
        assert "order_flow" in result.output

    def test_generate_direction_lr(
        self, runner: CliRunner, sample_source: Path, tmp_path: Path
    ) -> None:
        """Test LR direction flag."""
        output_path = tmp_path / "output"
        result = runner.invoke(
            cli, ["generate", str(sample_source), "-f", "dot", "-o", str(output_path), "-d", "LR"]
        )
        assert result.exit_code == 0

        dot_path = tmp_path / "output.dot"
        content = dot_path.read_text()
        assert "rankdir=LR" in content

    def test_generate_nonexistent_file(self, runner: CliRunner) -> None:
        """Test error for nonexistent source file."""
        result = runner.invoke(cli, ["generate", "/nonexistent/file.py"])
        assert result.exit_code != 0

    def test_generate_no_flows_in_file(self, runner: CliRunner, empty_source: Path) -> None:
        """Test error when no flows found."""
        result = runner.invoke(cli, ["generate", str(empty_source), "-f", "dot"])
        assert result.exit_code != 0
        assert "No flows found" in result.output

    def test_generate_from_directory(
        self, runner: CliRunner, sample_source: Path, tmp_path: Path
    ) -> None:
        """Test generating from a directory."""
        result = runner.invoke(cli, ["generate", str(tmp_path), "-f", "dot"])
        assert result.exit_code == 0
        assert "Generated:" in result.output

    def test_generate_syntax_error(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test that syntax errors in source are reported gracefully."""
        bad_file = tmp_path / "bad.py"
        bad_file.write_text("def broken(:\n    pass\n")
        result = runner.invoke(cli, ["generate", str(bad_file), "-f", "dot"])
        assert result.exit_code != 0

    def test_generate_empty_directory(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test generate on a directory with no Python files."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        result = runner.invoke(cli, ["generate", str(empty_dir), "-f", "dot"])
        assert result.exit_code != 0


class TestValidateCommand:
    """Tests for the validate command."""

    def test_validate_clean_flow(self, runner: CliRunner, sample_source: Path) -> None:
        """Test validation of a clean flow."""
        result = runner.invoke(cli, ["validate", str(sample_source)])
        assert result.exit_code == 0
        assert "successfully" in result.output

    def test_validate_with_issues(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test validation with dead steps."""
        source = dedent("""
            from flowdoc import flow, step

            @flow(name="Problem Flow")
            class ProblemFlow:
                @step(name="Start")
                def start(self):
                    return self.end()

                @step(name="End")
                def end(self):
                    pass

                @step(name="Orphan")
                def orphan(self):
                    pass
        """)
        file_path = tmp_path / "problem.py"
        file_path.write_text(source)

        result = runner.invoke(cli, ["validate", str(file_path)])
        assert "WARNING" in result.output or "warning" in result.output.lower()

    def test_validate_strict_mode(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test that --strict exits with error on warnings."""
        source = dedent("""
            from flowdoc import flow, step

            @flow(name="Problem Flow")
            class ProblemFlow:
                @step(name="Start")
                def start(self):
                    return self.end()

                @step(name="End")
                def end(self):
                    pass

                @step(name="Orphan")
                def orphan(self):
                    pass
        """)
        file_path = tmp_path / "problem.py"
        file_path.write_text(source)

        result = runner.invoke(cli, ["validate", str(file_path), "--strict"])
        assert result.exit_code != 0

    def test_validate_nonexistent_file(self, runner: CliRunner) -> None:
        """Test error for nonexistent source file."""
        result = runner.invoke(cli, ["validate", "/nonexistent/file.py"])
        assert result.exit_code != 0

    def test_validate_no_flows(self, runner: CliRunner, empty_source: Path) -> None:
        """Test error when no flows found."""
        result = runner.invoke(cli, ["validate", str(empty_source)])
        assert result.exit_code != 0
        assert "No flows found" in result.output

    def test_validate_syntax_error(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test that validate handles syntax errors gracefully."""
        bad_file = tmp_path / "bad.py"
        bad_file.write_text("def broken(:\n    pass\n")
        result = runner.invoke(cli, ["validate", str(bad_file)])
        assert result.exit_code != 0


class TestCLIGeneral:
    """General CLI tests."""

    def test_version_option(self, runner: CliRunner) -> None:
        """Test --version flag."""
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        # Check that output contains a version number (any format)
        assert any(char.isdigit() for char in result.output)
        assert "flowdoc" in result.output.lower() or "version" in result.output.lower()

    def test_help_output(self, runner: CliRunner) -> None:
        """Test --help flag."""
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "generate" in result.output
        assert "validate" in result.output

    def test_generate_help(self, runner: CliRunner) -> None:
        """Test generate --help."""
        result = runner.invoke(cli, ["generate", "--help"])
        assert result.exit_code == 0
        assert "--format" in result.output
        assert "--output" in result.output
        assert "--direction" in result.output

    def test_validate_help(self, runner: CliRunner) -> None:
        """Test validate --help."""
        result = runner.invoke(cli, ["validate", "--help"])
        assert result.exit_code == 0
        assert "--strict" in result.output

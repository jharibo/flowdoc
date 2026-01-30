# Contributing to FlowDoc

Thank you for considering contributing to FlowDoc! This document provides guidelines and instructions for contributing.

## Development Setup

### Prerequisites

- Python 3.10 or higher
- [uv](https://docs.astral.sh/uv/) package manager
- [Graphviz](https://graphviz.org/download/) (for diagram generation)

### Installation

```bash
# Clone the repository
git clone https://github.com/jharibo/flowdoc.git
cd flowdoc

# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Install in development mode
uv pip install -e .
```

## Development Workflow

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=flowdoc --cov-report=term-missing

# Run a specific test file
uv run pytest tests/test_parser.py

# Run a single test
uv run pytest tests/test_parser.py::test_class_flow_parsing
```

### Code Quality

```bash
# Format code (automatic fixes)
uv run ruff format .

# Lint and check (with automatic fixes)
uv run ruff check . --fix

# Lint without fixes
uv run ruff check .

# Type checking
uv run ty check flowdoc/
```

### Testing Your Changes

```bash
# Generate a diagram from an example
uv run flowdoc generate examples/ecommerce_order.py

# Validate a flow
uv run flowdoc validate examples/ecommerce_order.py
```

## Contribution Process

### 1. Fork and Branch

- Fork the repository on GitHub
- Create a feature branch from `main`:
  ```bash
  git checkout -b feat/your-feature-name
  ```

### 2. Make Changes

- Write your code following the project conventions
- Add tests for new functionality
- Ensure all tests pass: `uv run pytest`
- Ensure code quality checks pass:
  ```bash
  uv run ruff format . && uv run ruff check . && uv run ty check flowdoc/
  ```

### 3. Commit Using Conventional Commits

This project uses [Conventional Commits](https://www.conventionalcommits.org/) for semantic versioning.

**Format**: `<type>(<scope>): <description>`

**Types**:
- `feat`: A new feature (triggers minor version bump)
- `fix`: A bug fix (triggers patch version bump)
- `docs`: Documentation only changes
- `style`: Code style changes (formatting, missing semicolons, etc.)
- `refactor`: Code changes that neither fix a bug nor add a feature
- `test`: Adding or updating tests
- `chore`: Maintenance tasks, dependency updates

**Examples**:
```bash
git commit -m "feat: add support for async decorators"
git commit -m "fix: resolve parser crash on nested functions"
git commit -m "docs: update installation instructions"
git commit -m "test: add edge case tests for validator"
```

**Breaking changes**:
```bash
git commit -m "feat!: change decorator API signature"
```
The `!` indicates a breaking change and triggers a major version bump.

### 4. Push and Create Pull Request

```bash
git push origin feat/your-feature-name
```

- Go to GitHub and create a Pull Request
- Provide a clear description of your changes
- Reference any related issues

### 5. Review Process

- Maintainers will review your PR
- Address any feedback or requested changes
- Once approved, your PR will be merged

## Design Principles

Please follow these core principles when contributing:

1. **Inference over declaration**: Flow structure should be discovered from actual code, not manually specified
2. **No code execution**: Use AST analysis only - never execute user code
3. **Validation is advisory**: Warnings help catch issues but don't enforce correctness
4. **Keep decorators minimal**: Resist adding more decorator parameters - simplicity is key
5. **Business language**: Step names should describe business actions, not technical details
6. **Code is truth**: The actual Python execution determines flow; decorators are just labels

For detailed architecture information, see [CLAUDE.md](CLAUDE.md).

## Adding Examples

Examples live in the `examples/` directory. When adding a new example:

1. Create a `.py` file with a clear, realistic use case
2. Add comprehensive docstrings explaining the pattern
3. Generate diagrams: `uv run flowdoc generate examples/yourfile.py --format png`
4. Update `examples/README.md` to include your example

## Reporting Issues

- Use GitHub Issues to report bugs or request features
- Provide a clear description and reproduction steps
- Include Python version, operating system, and FlowDoc version

## Questions?

- Open a GitHub Discussion for general questions
- Check existing issues for similar questions
- Review the main [README.md](README.md) and [CLAUDE.md](CLAUDE.md)

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

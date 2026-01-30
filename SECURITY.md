# Security Policy

## FlowDoc Security Principles

FlowDoc is designed with **security-first principles** for static code analysis.

### Pure AST Analysis - No Code Execution

**FlowDoc never executes your code.** The parser uses Python's Abstract Syntax Tree (AST) module to analyze code structure without running it.

This means:
- ✅ **Safe on untrusted code** - No risk of malicious code execution
- ✅ **Works in CI/CD** - Safe to run in automated pipelines
- ✅ **No side effects** - Won't modify files, make network calls, or access resources
- ✅ **Fast** - No import overhead or runtime dependencies

### What FlowDoc Does

1. **Reads** your Python source files as text
2. **Parses** them into an AST using Python's built-in `ast` module
3. **Analyzes** decorator patterns and function calls in the AST
4. **Generates** flow diagrams from the analysis

### What FlowDoc Does NOT Do

- ❌ Import or execute your code
- ❌ Evaluate expressions or variables
- ❌ Run decorators or function definitions
- ❌ Access network, filesystem (beyond reading the specified file), or environment

### Design Trade-offs

By using pure AST analysis, FlowDoc cannot support:
- Dynamic decorator arguments (e.g., `@step(name=compute_name())`)
- F-strings with variables (e.g., `@step(name=f"Process {var}")`)
- Computed values

**This is intentional.** Security and simplicity are more important than supporting these edge cases.

### Reporting Security Issues

If you discover a security vulnerability in FlowDoc, please report it to:
- GitHub Security Advisories (preferred)
- Or open an issue with the `security` label

**Do NOT** post sensitive security details in public issues.

## Best Practices for Users

### Safe Usage

```bash
# Safe - reads file as text, no execution
flowdoc generate untrusted_code.py

# Safe - even on code with syntax errors
flowdoc generate broken_code.py  # Will show parse error, won't execute

# Safe - in CI/CD pipelines
flowdoc generate src/**/*.py --output docs/flows/
```

### Recommended Patterns

Use literal strings in decorators:

```python
# ✅ Good - literal strings
@step(name="Process Order", description="Handle customer order")
def process_order(order):
    pass

# ❌ Avoid - dynamic values (won't work)
STEP_NAME = "Process Order"
@step(name=STEP_NAME)  # Won't detect the name
def process_order(order):
    pass
```

## Version Support

- **Minimum Python**: 3.10
- **Tested Versions**: 3.10, 3.11, 3.12, 3.13
- **Dependencies**: Only `graphviz` and `click` for runtime

## License

FlowDoc is released under the MIT License. See LICENSE file for details.

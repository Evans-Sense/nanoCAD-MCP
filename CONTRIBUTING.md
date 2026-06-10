# Contributing to nanoCAD MCP Server

## Getting Started

1. Clone the repository
2. Install Python 3.13+
3. Install the server with dev dependencies:

```powershell
cd server
pip install -e ".[sse,dev]"
```

4. Build the .NET engine plugin (requires .NET SDK):

```powershell
dotnet build engine/CadEngine.Plugin/CadEngine.Plugin.csproj
```

## Running Tests

```powershell
# Unit tests (no CAD needed)
pytest tests/unit/ -v

# Integration tests (requires nanoCAD running with the plugin)
$env:NANOCAD_MCP_TEST_LIVE = "1"
pytest tests/integration/ -v

# Full suite with coverage
pytest --cov=src
```

## Code Style

- **Lint**: `ruff check src/`
- **Format**: `ruff format src/`
- **Type check**: `mypy src/`

All three must pass before submitting a pull request.

## Pull Request Process

1. Create a feature branch from `main`
2. Write tests first (TDD approach)
3. Implement your changes
4. Ensure all tests pass (`pytest tests/unit/`)
5. Run `ruff check src/` and `mypy src/` — zero errors required
6. Submit a pull request against `main`
7. Link any related issues in the PR description

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
